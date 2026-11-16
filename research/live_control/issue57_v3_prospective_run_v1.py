"""Fail-closed evidence-root and lifecycle journal for a prospective Issue #57 v3 run.

This module deliberately does not dispatch GUI input or model calls. It gives a
future live adapter a non-reusable allocation boundary and durable append-only
custody for assigned preflight/task envelopes before such adapters are enabled.
"""
from __future__ import annotations

import hashlib
import copy
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from research.live_control.integrated_efficiency_protocol_v1 import ARMS, TASKS
from research.live_control.issue57_v3_trace_adapter_v1 import (
    assemble_complete_trace, project_task,
)


SCHEMA = "issue57-v3-prospective-run-v1"
REQUIRED_ALLOCATION = {
    "allocation_id", "host_id", "owner", "exclusive", "expires_at_utc",
    "task_ids", "arms", "model", "settings", "order_seed",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical(value) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                        ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


class ProspectiveRun:
    """Create a new evidence root and append each assigned outcome once.

    Construction requires a trusted caller-supplied allocation attestor, an
    explicit exclusive allocation, and a root that did not exist. The attestor
    must verify the allocation against an authoritative external source; this
    module does not implement that trust source. Every lifecycle record is
    fsynced before the caller may advance. The class has no provider or input
    adapter by design.
    """

    def __init__(self, allocation_path, evidence_root, *, source_root,
                 allocation_verifier):
        self.allocation_path = Path(allocation_path).resolve(strict=True)
        self.evidence_root = Path(evidence_root).resolve()
        self.source_root = Path(source_root).resolve(strict=True)
        allocation_bytes = self.allocation_path.read_bytes()
        allocation = json.loads(allocation_bytes)
        if not callable(allocation_verifier):
            raise ValueError("trusted allocation verifier required")
        if type(allocation) is not dict or set(allocation) != REQUIRED_ALLOCATION:
            raise ValueError("allocation manifest has unexpected or missing fields")
        if any(type(allocation[key]) is not str or not allocation[key]
               for key in ("allocation_id", "host_id", "owner", "expires_at_utc",
                           "model")):
            raise ValueError("allocation identity, owner, host, expiry and model are required")
        try:
            expiry = datetime.fromisoformat(allocation["expires_at_utc"].replace("Z", "+00:00"))
        except ValueError as error:
            raise ValueError("allocation expiry must be an ISO-8601 timestamp") from error
        if expiry.tzinfo is None or expiry <= datetime.now(timezone.utc):
            raise ValueError("allocation must have a future timezone-aware expiry")
        if allocation["exclusive"] is not True:
            raise ValueError("exclusive host allocation is required")
        if allocation["task_ids"] != list(TASKS) or allocation["arms"] != list(ARMS):
            raise ValueError("allocation must contain the frozen six tasks and three arms")
        if type(allocation["settings"]) is not dict or not allocation["settings"]:
            raise ValueError("frozen model/runtime settings required")
        if type(allocation["order_seed"]) is not int:
            raise ValueError("integer frozen order seed required")
        if allocation_verifier(self.allocation_path, copy.deepcopy(allocation)) is not True:
            raise ValueError("allocation verifier did not attest this exclusive allocation")
        if self.evidence_root.exists():
            raise FileExistsError("evidence root must be new and unused")
        self.evidence_root.parent.mkdir(parents=True, exist_ok=True)
        self.evidence_root.mkdir()
        self.allocation = allocation
        self._seen = set()
        self._rows = {arm: [None] * len(TASKS) for arm in ARMS}
        self._preflights = {}
        self._finished = False
        self._journal_path = self.evidence_root / "lifecycle.jsonl"
        manifest = {
            "schema": SCHEMA,
            "created_ns": time.time_ns(),
            "allocation": allocation,
            "allocation_sha256": hashlib.sha256(allocation_bytes).hexdigest(),
            "source_commit": self._git_head(self.source_root),
            "source_files": self._source_hashes(),
            "python": os.sys.version,
            "dispatch_enabled": False,
        }
        self.manifest_path = self.evidence_root / "run-manifest.json"
        self.manifest_path.write_bytes(_canonical(manifest))
        with self.manifest_path.open("r+b") as stream:
            os.fsync(stream.fileno())
        self.append("run_created", {"dispatch_enabled": False})

    def _source_hashes(self):
        names = (
            "research/live_control/run_integrated_efficiency_live_v1.py",
            "research/live_control/adaptive_acquisition_caller_v3.py",
            "research/live_control/integrated_efficiency_compiled_execution_v2.py",
            "research/live_control/integrated_efficiency_compiled_adapter_v2.py",
            "research/live_control/v3_persistent_grounding_adapter_v1.py",
            "research/live_control/issue57_v3_trace_adapter_v1.py",
            "research/live_control/issue57_v3_prospective_run_v1.py",
            "research/live_control/integrated_efficiency_protocol_v1.py",
        )
        return {name: _sha256(self.source_root / name) for name in names}

    @staticmethod
    def _git_head(root):
        try:
            return subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                check=True, capture_output=True, text=True, timeout=5).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            return "unavailable"

    def append(self, event, payload):
        if type(event) is not str or not event or type(payload) is not dict:
            raise ValueError("event name and object payload required")
        row = {"sequence": self._line_count() + 1, "event": event,
               "recorded_ns": time.time_ns(), "payload": payload}
        with self._journal_path.open("ab") as stream:
            stream.write(_canonical(row))
            stream.flush()
            os.fsync(stream.fileno())
        return row

    def _line_count(self):
        if not self._journal_path.exists():
            return 0
        with self._journal_path.open("rb") as stream:
            return sum(1 for _ in stream)

    def record_preflight(self, arm, envelope):
        if self._finished:
            raise ValueError("run is already finalized")
        if arm not in ARMS:
            raise ValueError("unknown frozen arm")
        if arm in self._preflights:
            raise ValueError("preflight already recorded for arm")
        retained = copy.deepcopy(envelope)
        self._preflights[arm] = retained
        self.append("preflight", {"arm": arm, "envelope": retained})

    def record_task(self, arm, index, caller_result, independent_score, telemetry):
        if self._finished:
            raise ValueError("run is already finalized")
        if arm not in ARMS or type(index) is not int or not 0 <= index < len(TASKS):
            raise ValueError("unknown frozen arm/task assignment")
        key = (arm, index)
        if key in self._seen:
            raise ValueError("assigned task outcome already recorded")
        caller_result = copy.deepcopy(caller_result)
        independent_score = copy.deepcopy(independent_score)
        telemetry = copy.deepcopy(telemetry)
        projected = project_task(arm, index, caller_result,
                                 independent_score, telemetry)
        self.append("task", {"arm": arm, "task_index": index,
                              "task_id": TASKS[index],
                              "caller_result": caller_result,
                              "independent_score": independent_score,
                              "telemetry": telemetry,
                              "projection": projected})
        self._rows[arm][index] = projected
        self._seen.add(key)
        return projected

    def finish(self, integration_discoveries):
        if self._finished:
            raise ValueError("run is already finalized")
        integration_discoveries = copy.deepcopy(integration_discoveries)
        expected = {(arm, index) for arm in ARMS for index in range(len(TASKS))}
        missing = sorted(expected - self._seen)
        preflight_calls = {arm: self._preflights.get(arm) for arm in ARMS}
        adjudication = assemble_complete_trace(self._rows, preflight_calls,
                                               integration_discoveries)
        outcome = {"status": "HOLD" if missing else adjudication["status"],
            "reason": ("assigned_task_missing" if missing else adjudication["reason"]),
            "missing_assignments": [[arm, index] for arm, index in missing],
            "adjudication": adjudication}
        outcome_path = self.evidence_root / "adjudication.json"
        outcome_path.write_bytes(_canonical(outcome))
        with outcome_path.open("r+b") as stream:
            os.fsync(stream.fileno())
        self.append("run_finish", {"complete": not missing,
            "missing_assignments": [[arm, index] for arm, index in missing],
            "preflight_calls": preflight_calls,
            "integration_discoveries": integration_discoveries,
            "adjudication_status": outcome["status"],
            "adjudication_sha256": hashlib.sha256(_canonical(outcome)).hexdigest()})
        self._finished = True
        return outcome
