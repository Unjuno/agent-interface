"""Durable, allocation-scoped evidence for the existing Calc v3 caller.

This local research ledger publishes model-attempt events as they happen,
stores the compiled receipt before outer effect verification, and preserves
the independent effect receipt and terminal accounting separately. It is not
a crash-proof external custodian or a live correctness certificate.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import threading
from pathlib import Path


_MAX_EVENT_BYTES = 1024 * 1024
_MAX_EVENTS = 1024
_ALLOCATION_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}\Z")


def _encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def _write_exclusive(path, data):
    payload = _encode(data) + b"\n"
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0), 0o600)
    try:
        view = memoryview(payload)
        while view:
            written = os.write(fd, view)
            if written <= 0:
                raise OSError("short evidence write")
            view = view[written:]
        os.fsync(fd)
    finally:
        os.close(fd)
    return hashlib.sha256(payload).hexdigest()


class DurableCalcAllocation:
    """One exclusive attempt directory with a hash-linked fsynced event log."""

    def __init__(self, parent, allocation_id, *, source_sha256,
                 observation_ids, source_hashes, conditions):
        if type(allocation_id) is not str or not _ALLOCATION_ID.fullmatch(allocation_id):
            raise ValueError("safe allocation id required")
        if type(source_sha256) is not str or not re.fullmatch(r"[0-9a-f]{64}", source_sha256):
            raise ValueError("source SHA-256 required")
        if (type(observation_ids) is not list or not observation_ids or
                any(type(value) is not str or not value for value in observation_ids) or
                len(observation_ids) != len(set(observation_ids))):
            raise ValueError("unique bound observation ids required")
        if (type(source_hashes) is not dict or not source_hashes or
                any(type(path) is not str or not path or type(digest) is not str or
                    not re.fullmatch(r"[0-9a-f]{64}", digest)
                    for path, digest in source_hashes.items())):
            raise ValueError("nonempty pinned source hash mapping required")
        if type(conditions) is not dict:
            raise ValueError("frozen conditions object required")
        self.path = Path(parent) / allocation_id
        if not self.path.parent.is_dir():
            raise ValueError("allocation parent directory must already exist")
        self.path.mkdir(mode=0o700, exist_ok=False)
        self._lock = threading.Lock()
        self._event_count = 0
        self._previous = None
        self._receipt_digest = None
        self._effect_digest = None
        self._graph_binding = None
        self._finalized = False
        self.manifest = {
            "schema": "calc-durable-allocation-v1",
            "allocation_id": allocation_id,
            "source_sha256": source_sha256,
            "observation_ids": list(observation_ids),
            "source_hashes": copy.deepcopy(source_hashes),
            "conditions": copy.deepcopy(conditions),
            "durability_limit": "fsynced local files; no independent post-crash custodian",
        }
        _encode(self.manifest)
        conditions_digest = _write_exclusive(self.path / "conditions.json", self.manifest)
        fd = os.open(self.path / "events.jsonl",
                     os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0), 0o600)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
        self.append_event("allocation_created", {
            "conditions_sha256": conditions_digest,
            "source_sha256": source_sha256,
            "observation_ids": list(observation_ids)})

    @property
    def source_sha256(self):
        return self.manifest["source_sha256"]

    @property
    def observation_ids(self):
        return list(self.manifest["observation_ids"])

    def append_event(self, event_type, data):
        if type(event_type) is not str or not event_type or type(data) is not dict:
            raise ValueError("typed allocation event required")
        with self._lock:
            if self._finalized:
                raise RuntimeError("allocation is already finalized")
            if self._event_count >= _MAX_EVENTS:
                raise ValueError("allocation event limit reached")
            body = {"schema": "calc-durable-event-v1",
                    "index": self._event_count + 1,
                    "previous_sha256": self._previous,
                    "event_type": event_type,
                    "data": copy.deepcopy(data)}
            digest = hashlib.sha256(_encode(body)).hexdigest()
            frame = _encode(dict(body, sha256=digest)) + b"\n"
            if len(frame) > _MAX_EVENT_BYTES:
                raise ValueError("allocation event exceeds size limit")
            fd = os.open(self.path / "events.jsonl",
                         os.O_WRONLY | os.O_APPEND | getattr(os, "O_BINARY", 0))
            try:
                view = memoryview(frame)
                while view:
                    written = os.write(fd, view)
                    if written <= 0:
                        raise OSError("short event append")
                    view = view[written:]
                os.fsync(fd)
            finally:
                os.close(fd)
            self._event_count += 1
            self._previous = digest
            return digest

    def bind_interface(self, interface):
        if type(interface) is not dict or type(interface.get("interface_id")) is not str:
            raise ValueError("compiled interface with identity required")
        graph_digest = hashlib.sha256(_encode(interface)).hexdigest()
        binding = {"interface_id": interface["interface_id"],
                   "graph_sha256": graph_digest,
                   "source_sha256": self.source_sha256,
                   "observation_ids": self.observation_ids}
        if self._graph_binding is not None:
            raise ValueError("one compiled interface per allocation required")
        self._write_once("interface_binding.json", binding)
        self._graph_binding = binding
        self.append_event("interface_bound", binding)
        return copy.deepcopy(binding)

    def persist_execution_receipt(self, receipt):
        if type(receipt) is not dict or self._graph_binding is None:
            raise ValueError("compiled receipt and prior interface binding required")
        envelope = {"schema": "calc-durable-execution-receipt-v1",
                    "allocation_id": self.manifest["allocation_id"],
                    "source_sha256": self.source_sha256,
                    "observation_ids": self.observation_ids,
                    "interface_binding": copy.deepcopy(self._graph_binding),
                    "receipt": copy.deepcopy(receipt)}
        self._receipt_digest = self._write_once("compiled_receipt.json", envelope)
        self.append_event("compiled_receipt_persisted", {
            "sha256": self._receipt_digest,
            "interface_id": self._graph_binding["interface_id"],
            "graph_sha256": self._graph_binding["graph_sha256"]})
        return self._receipt_digest

    def persist_effect_receipt(self, effect_receipt):
        if type(effect_receipt) is not dict or effect_receipt.get("status") not in {
                "succeeded", "failed", "unavailable"}:
            raise ValueError("validated effect receipt required")
        envelope = {"schema": "calc-durable-effect-receipt-v1",
                    "allocation_id": self.manifest["allocation_id"],
                    "source_sha256": self.source_sha256,
                    "observation_ids": self.observation_ids,
                    "execution_receipt_sha256": self._receipt_digest,
                    "effect_receipt": copy.deepcopy(effect_receipt)}
        self._effect_digest = self._write_once("effect_receipt.json", envelope)
        self.append_event("effect_receipt_persisted", {
            "sha256": self._effect_digest,
            "execution_receipt_sha256": self._receipt_digest,
            "status": effect_receipt["status"]})
        return self._effect_digest

    def _write_once(self, name, data):
        return _write_exclusive(self.path / name, data)

    def record_abort(self, error):
        try:
            self.append_event("caller_aborted", {"exception_type": type(error).__name__})
        except BaseException:
            # Preserve the original interruption; missing event durability is
            # an unknown allocation, never a reason to claim completion.
            pass

    def finalize(self, result):
        if type(result) is not dict or type(result.get("outcome")) is not str:
            raise ValueError("caller result required")
        if result["outcome"] == "TASK_SUCCEEDED" and (
                self._receipt_digest is None or self._effect_digest is None or
                result.get("effect_receipt", {}).get("status") != "succeeded"):
            raise ValueError("success requires persisted execution and effect receipts")
        summary = {key: copy.deepcopy(result.get(key)) for key in (
            "outcome", "reason", "task_effect", "delivery", "execution_progress",
            "effect_receipt", "stages", "attempt_ledger", "accounting", "phase_timings")}
        call_fields = ("attempt_id", "stage", "call_id", "thread_id",
                       "requested_model", "requested_effort", "usage", "cost",
                       "visible_images_submitted", "wait_ns")
        summary["model_call_cost_ledger"] = [
            {field: copy.deepcopy(row.get(field)) for field in call_fields}
            for row in result.get("model_call_ledger", [])]
        summary.update({"schema": "calc-durable-result-v1",
                        "allocation_id": self.manifest["allocation_id"],
                        "source_sha256": self.source_sha256,
                        "observation_ids": self.observation_ids,
                        "compiled_receipt_sha256": self._receipt_digest,
                        "effect_receipt_sha256": self._effect_digest,
                        "model_outputs_retained": False})
        result_digest = self._write_once("result.json", summary)
        self.append_event("allocation_finalized", {
            "outcome": summary["outcome"],
            "receipt_sha256": self._receipt_digest,
            "effect_receipt_sha256": self._effect_digest,
            "result_sha256": result_digest})
        self._finalized = True
        return summary


def audit_allocation(path):
    """Verify local record linkage; absent terminal result remains UNKNOWN."""
    root = Path(path)
    manifest_bytes = (root / "conditions.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    if manifest.get("schema") != "calc-durable-allocation-v1":
        raise ValueError("allocation manifest schema mismatch")
    raw = (root / "events.jsonl").read_bytes()
    if raw and not raw.endswith(b"\n"):
        raise ValueError("torn event log; allocation outcome UNKNOWN")
    previous = None
    rows = []
    for index, line in enumerate(raw.splitlines(), 1):
        if len(line) > _MAX_EVENT_BYTES:
            raise ValueError("oversized event record")
        frame = json.loads(line)
        digest = frame.pop("sha256")
        if (frame.get("schema") != "calc-durable-event-v1" or
                frame.get("index") != index or frame.get("previous_sha256") != previous or
                hashlib.sha256(_encode(frame)).hexdigest() != digest):
            raise ValueError("event hash chain mismatch; allocation outcome UNKNOWN")
        previous = digest
        rows.append(frame)
    if not rows or rows[0]["event_type"] != "allocation_created":
        raise ValueError("allocation conditions lack a creation-event anchor")
    expected_creation = {
        "conditions_sha256": hashlib.sha256(
            (root / "conditions.json").read_bytes()).hexdigest(),
        "source_sha256": manifest.get("source_sha256"),
        "observation_ids": manifest.get("observation_ids"),
    }
    if rows[0]["data"] != expected_creation:
        raise ValueError("allocation manifest/event mismatch; conditions may be rewritten")
    result_path = root / "result.json"
    result_bytes = result_path.read_bytes() if result_path.exists() else None
    result = json.loads(result_bytes) if result_bytes is not None else None
    result_digest = hashlib.sha256(result_bytes).hexdigest() if result_bytes is not None else None
    if result is not None and result.get("schema") != "calc-durable-result-v1":
        raise ValueError("terminal result schema mismatch")
    receipt = json.loads((root / "compiled_receipt.json").read_bytes()) if (root / "compiled_receipt.json").exists() else None
    effect = json.loads((root / "effect_receipt.json").read_bytes()) if (root / "effect_receipt.json").exists() else None
    interface_path = root / "interface_binding.json"
    interface_binding = json.loads(interface_path.read_bytes()) if interface_path.exists() else None
    interface_events = [row["data"] for row in rows if row["event_type"] == "interface_bound"]
    if interface_binding is not None and (
            len(interface_events) != 1 or interface_events[0] != interface_binding):
        raise ValueError("interface binding event/file mismatch")
    if interface_binding is None and interface_events:
        raise ValueError("interface binding event lacks its file")
    if interface_binding is not None and (
            interface_binding.get("source_sha256") != manifest.get("source_sha256") or
            interface_binding.get("observation_ids") != manifest.get("observation_ids")):
        raise ValueError("interface binding source mismatch")
    for envelope in (receipt, effect):
        if envelope is not None and (
                envelope.get("allocation_id") != manifest.get("allocation_id") or
                envelope.get("source_sha256") != manifest.get("source_sha256") or
                envelope.get("observation_ids") != manifest.get("observation_ids")):
            raise ValueError("durable receipt source binding mismatch")
    if receipt is not None and (
            interface_binding is None or
            receipt.get("interface_binding") != interface_binding):
        raise ValueError("compiled receipt interface binding mismatch")
    receipt_bytes = (root / "compiled_receipt.json").read_bytes() if receipt is not None else None
    effect_bytes = (root / "effect_receipt.json").read_bytes() if effect is not None else None
    receipt_digest = hashlib.sha256(receipt_bytes).hexdigest() if receipt_bytes is not None else None
    effect_digest = hashlib.sha256(effect_bytes).hexdigest() if effect_bytes is not None else None
    receipt_events = [row["data"] for row in rows if row["event_type"] == "compiled_receipt_persisted"]
    effect_events = [row["data"] for row in rows if row["event_type"] == "effect_receipt_persisted"]
    terminal_events = [row["data"] for row in rows if row["event_type"] == "allocation_finalized"]
    if receipt is not None and (len(receipt_events) != 1 or receipt_events[0].get("sha256") != receipt_digest):
        raise ValueError("compiled receipt event/file mismatch")
    if effect is not None and (len(effect_events) != 1 or effect_events[0].get("sha256") != effect_digest or
            effect_events[0].get("execution_receipt_sha256") != receipt_digest):
        raise ValueError("effect receipt event/file mismatch")
    if result is not None:
        attempts = result.get("attempt_ledger")
        accounting = result.get("accounting")
        if type(attempts) is not list or type(accounting) is not dict or accounting.get("attempted_calls") != len(attempts):
            raise ValueError("all-attempt result accounting mismatch")
        fields = ("input_tokens", "cached_input_tokens", "cache_write_input_tokens",
                  "output_tokens", "reasoning_output_tokens")
        for field in fields:
            coverage = sum(type(row.get("usage")) is dict and type(row["usage"].get(field)) is int
                           for row in attempts)
            total = (sum(row["usage"][field] for row in attempts
                         if type(row.get("usage")) is dict and type(row["usage"].get(field)) is int)
                     if coverage == len(attempts) else None)
            if (accounting.get("usage_coverage", {}).get(field) != coverage or
                    accounting.get("usage_totals", {}).get(field) != total):
                raise ValueError("all-attempt usage total mismatch")
        costs = [row["cost"] for row in attempts if row.get("cost") is not None]
        total_cost = sum(costs) if len(costs) == len(attempts) else None
        if (accounting.get("cost_coverage") != len(costs) or
                accounting.get("cost") != total_cost):
            raise ValueError("all-attempt cost total mismatch")
        if len(terminal_events) != 1 or terminal_events[0] != {
                "outcome": result.get("outcome"),
                "receipt_sha256": receipt_digest,
                "effect_receipt_sha256": effect_digest,
                "result_sha256": result_digest}:
            raise ValueError("terminal event/result mismatch; allocation outcome UNKNOWN")
    if result and result.get("outcome") == "TASK_SUCCEEDED":
        if (receipt is None or effect is None or effect.get("effect_receipt", {}).get("status") != "succeeded" or
                result.get("compiled_receipt_sha256") != receipt_digest or
                result.get("effect_receipt_sha256") != effect_digest):
            raise ValueError("success is missing linked durable evidence")
    finalized = result is not None and len(terminal_events) == 1
    return {"status": "audited" if finalized else "UNKNOWN",
            "allocation_id": manifest["allocation_id"],
            "outcome": result.get("outcome") if finalized else "UNKNOWN",
            "event_count": len(rows),
            "attempt_ledger": copy.deepcopy(result.get("attempt_ledger")) if result else None,
            "accounting": copy.deepcopy(result.get("accounting")) if result else None,
            "receipt_persisted": receipt is not None,
            "effect_receipt_persisted": effect is not None}
