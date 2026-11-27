"""Append-only comparison ledger for current v3 caller result envelopes.

This is an offline/live-candidate recording seam. It does not execute a model,
GUI action, scorer, or recovery operation.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path

OUTCOMES = {"TASK_SUCCEEDED", "TASK_NOT_VERIFIED", "EXECUTION_INCOMPLETE",
            "SAFE_STOP", "CALLER_FAILED", "TASK_DEFERRED"}


def _json_bytes(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                        ensure_ascii=False) + "\n").encode("utf-8")


def _evidence_ref(value, label):
    if type(value) is not dict:
        raise ValueError(label + " evidence receipt required")
    if value.get("status") not in {"succeeded", "failed", "unavailable"}:
        raise ValueError(label + " evidence status must be explicit")
    ref = value.get("evidence_ref")
    digest = value.get("evidence_digest")
    if ref is not None and (type(ref) is not str or not ref):
        raise ValueError(label + " evidence_ref must be nonempty text or null")
    if digest is not None and (type(digest) is not str or not digest):
        raise ValueError(label + " evidence_digest must be nonempty text or null")
    if value["status"] == "succeeded" and (ref is None or digest is None):
        raise ValueError(label + " success requires evidence reference and digest")
    return {"status": value["status"], "evidence_ref": ref,
            "evidence_digest": digest}


def _release_ref(value):
    receipt = _evidence_ref(value, "release")
    if receipt["status"] == "succeeded":
        if (value.get("verified") is not True or value.get("keys_down") != []
                or value.get("buttons_down") != []):
            raise ValueError("successful release requires verified empty key/button state")
    elif value.get("verified") is True and (value.get("keys_down") or value.get("buttons_down")):
        raise ValueError("release cannot be verified while input remains down")
    return {**receipt,
            "verified": value.get("verified"),
            "keys_down": copy.deepcopy(value.get("keys_down")),
            "buttons_down": copy.deepcopy(value.get("buttons_down"))}


def make_row(assignment_id, caller_result, release_receipt, effect_receipt,
             raw_paths=()):
    """Build one all-attempt row from the public v3 composition result.

    Release and task-effect evidence are explicit inputs because the caller's
    execution outcome alone does not prove either property.
    """
    if type(assignment_id) is not str or not assignment_id:
        raise ValueError("nonempty frozen assignment_id required")
    if type(caller_result) is not dict or type(caller_result.get("outcome")) is not str:
        raise ValueError("public v3 caller result required")
    if caller_result["outcome"] not in OUTCOMES:
        raise ValueError("unsupported public v3 outcome")
    attempts = caller_result.get("attempt_ledger")
    if type(attempts) is not list:
        raise ValueError("v3 attempt ledger required")
    ids = [row.get("attempt_id") for row in attempts if type(row) is dict]
    if len(ids) != len(attempts) or any(type(item) is not str or not item for item in ids):
        raise ValueError("every attempted call must retain an attempt id")
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate attempt ids")
    accounting = caller_result.get("accounting")
    if type(accounting) is not dict or accounting.get("attempted_calls") != len(attempts):
        raise ValueError("public accounting must include every attempt")
    receipts = caller_result.get("compiled_execution_receipt")
    if receipts is not None and type(receipts) is not dict:
        raise ValueError("compiled execution receipt must be object or null")
    release = _release_ref(release_receipt)
    effect = _evidence_ref(effect_receipt, "effect")
    caller_effect = caller_result.get("task_effect")
    if (caller_effect != effect["status"] and
            not (caller_effect is None and effect["status"] == "unavailable")):
        raise ValueError("public task_effect and independent effect receipt disagree")

    hashes = []
    for raw_path in raw_paths:
        path = Path(raw_path)
        if not path.is_file():
            raise ValueError("raw evidence path is not a file")
        data = path.read_bytes()
        hashes.append({"name": path.name, "size_bytes": len(data),
                       "sha256": hashlib.sha256(data).hexdigest()})

    return {"schema": "issue57-v3-attempt-row-v1",
            "assignment_id": assignment_id,
            "outcome": caller_result["outcome"],
            "reason": caller_result.get("reason"),
            "task_effect": caller_effect,
            "delivery": caller_result.get("delivery"),
            "attempt_ledger": copy.deepcopy(attempts),
            "accounting": copy.deepcopy(accounting),
            "compiled_execution_receipt": copy.deepcopy(receipts),
            "execution_progress": copy.deepcopy(caller_result.get("execution_progress")),
            "release_receipt": release,
            "effect_receipt": effect,
            "raw_evidence": hashes}


class AppendOnlyAttemptLedger:
    """Minimal fsync-per-row journal; refuses duplicate assignments."""
    def __init__(self, path, assigned_ids):
        self.path = Path(path)
        self.assigned_ids = tuple(assigned_ids)
        if (not self.assigned_ids or any(type(v) is not str or not v
                for v in self.assigned_ids) or len(set(self.assigned_ids)) != len(self.assigned_ids)):
            raise ValueError("unique frozen assignment ids required")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists() and self.path.stat().st_size:
            raise FileExistsError("ledger path must be new; no append/replay")
        self._seen = set()

    def append(self, row):
        if type(row) is not dict or row.get("schema") != "issue57-v3-attempt-row-v1":
            raise ValueError("validated v3 attempt row required")
        assignment = row.get("assignment_id")
        expected_index = len(self._seen)
        if (expected_index >= len(self.assigned_ids)
                or assignment != self.assigned_ids[expected_index]):
            raise ValueError("assignment is unassigned, duplicate, or out of frozen order")
        encoded = _json_bytes(row)
        with self.path.open("ab") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        self._seen.add(assignment)
        return hashlib.sha256(encoded).hexdigest()

    def audit(self):
        if not self.path.is_file():
            rows = []
        else:
            raw = self.path.read_bytes()
            if raw and not raw.endswith(b"\n"):
                raise ValueError("incomplete trailing ledger row")
            rows = [json.loads(line) for line in raw.splitlines()]
        ids = [row.get("assignment_id") for row in rows]
        if len(ids) != len(set(ids)) or any(v not in self.assigned_ids for v in ids):
            raise ValueError("duplicate or unassigned ledger row")
        if ids != list(self.assigned_ids):
            raise ValueError("assigned attempts missing or out of frozen order")
        for row in rows:
            required = {"schema", "assignment_id", "outcome", "reason", "task_effect",
                        "delivery", "attempt_ledger", "accounting",
                        "compiled_execution_receipt", "execution_progress",
                        "release_receipt", "effect_receipt", "raw_evidence"}
            if type(row) is not dict or set(row) != required:
                raise ValueError("ledger row fields are incomplete or unexpected")
            if row.get("schema") != "issue57-v3-attempt-row-v1":
                raise ValueError("unsupported or modified row schema")
            if type(row.get("outcome")) is not str or row["outcome"] not in OUTCOMES:
                raise ValueError("unsupported or modified caller outcome")
            attempts = row["attempt_ledger"]
            if type(attempts) is not list:
                raise ValueError("attempt ledger must remain a list")
            attempt_ids = [item.get("attempt_id") for item in attempts
                           if type(item) is dict]
            if (len(attempt_ids) != len(attempts)
                    or any(type(value) is not str or not value for value in attempt_ids)
                    or len(attempt_ids) != len(set(attempt_ids))):
                raise ValueError("attempt rows missing ids or contain duplicates")
            if (type(row["accounting"]) is not dict or
                    row["accounting"].get("attempted_calls") != len(attempts)):
                raise ValueError("attempt total differs from retained rows")
            receipt = row["compiled_execution_receipt"]
            if receipt is not None and type(receipt) is not dict:
                raise ValueError("compiled receipt must remain object or null")
            effect = row["effect_receipt"]
            if type(effect) is not dict:
                raise ValueError("effect receipt must remain an object")
            task_effect = row["task_effect"]
            if (task_effect is not None and
                    (type(task_effect) is not str or task_effect not in
                     {"succeeded", "failed", "unavailable"})):
                raise ValueError("unsupported caller task-effect state")
            if (effect.get("status") != task_effect and
                    not (task_effect is None and effect.get("status") == "unavailable")):
                raise ValueError("task effect differs from receipt")
            _evidence_ref(effect, "effect")
            _release_ref(row["release_receipt"])
            if type(row["raw_evidence"]) is not list:
                raise ValueError("raw evidence manifest must remain a list")
            for evidence in row["raw_evidence"]:
                if (type(evidence) is not dict
                        or type(evidence.get("name")) is not str
                        or type(evidence.get("size_bytes")) is not int
                        or evidence["size_bytes"] < 0
                        or type(evidence.get("sha256")) is not str
                        or len(evidence["sha256"]) != 64
                        or any(char not in "0123456789abcdef" for char in evidence["sha256"])):
                    raise ValueError("malformed raw evidence manifest row")
        return {"rows": len(rows), "attempts": sum(len(row["attempt_ledger"]) for row in rows),
                "assignment_ids": ids,
                "sha256": hashlib.sha256(self.path.read_bytes()).hexdigest()}
