#!/usr/bin/env python3
"""Independent, timing-tolerant audit for the frozen socket-backed result."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
FREEZE = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
INPUT_BYTES = len(b'{"op":"finish"}\n')


def audit(result: dict[str, Any]) -> dict[str, Any]:
    hashes: dict[str, bool] = {}
    for name, entry in FREEZE["source_files"].items():
        data = (ROOT / name).read_bytes()
        hashes[name] = len(data) == entry["bytes"] and hashlib.sha256(data).hexdigest() == entry["sha256"]
    cases = {row.get("name"): row for row in result.get("scenarios", []) if type(row) is dict}
    fast = cases.get("ready_fast_control", {})
    entry = cases.get("ready_at_entry_overrun", {})
    during = cases.get("command_arrives_during_overrun", {})

    def starved(case: dict[str, Any]) -> bool:
        tail = case.get("tail", {})
        return (
            case.get("sample_period_ns") == FREEZE["scenario"]["sample_period_ns"]
            and case.get("sample_duration_ns") == FREEZE["scenario"]["overrun_call_ns"]
            and case.get("readiness_check_count") == 0
            and case.get("sample_return_count", 0) >= 3
            and tail.get("tail_samples", 0) >= 3
            and tail.get("termination") in {"deadline", "deadline_overrun"}
            and case.get("socket_readable_after_tail") is True
            and case.get("command_bytes_still_unread") == INPUT_BYTES
        )

    checks = {
        "candidate_and_source_hashes_match_freeze": all(hashes.values()),
        "result_schema_and_source_pin_match": (
            result.get("schema") == "issue59-scorer-tail-command-priority-a02-v1"
            and result.get("candidate_source_head") == FREEZE["candidate_source_head"]
            and result.get("construction_only") is True
        ),
        "fast_control_observes_ready_command": (
            fast.get("tail", {}).get("termination") == "command_ready"
            and fast.get("readiness_check_count") >= 1
            and fast.get("sample_return_count") == 1
            and fast.get("command_bytes_still_unread") == INPUT_BYTES
        ),
        "ready_at_entry_overrun_starves": starved(entry),
        "during_callback_overrun_starves": (
            during.get("scheduled_during_first_sample") is True and starved(during)
        ),
        "release_receipt_and_tail_share_monotonic_epoch": all(
            c.get("tail", {}).get("started_ns", 0) >= c.get("tail", {}).get("release_returned_ns", 1)
            and c.get("tail", {}).get("deadline_ns", 0) - c.get("tail", {}).get("release_returned_ns", 0)
            == FREEZE["scenario"]["deadline_ns"]
            for c in (fast, entry, during)
        ),
        "frozen_gate_matches_observed_outcome": (
            result.get("disposition") == "FAIL_OS_READY_COMMAND_STARVATION_ON_SAMPLE_OVERRUN"
        ),
    }
    behavioral_fail = checks["fast_control_observes_ready_command"] and checks[
        "ready_at_entry_overrun_starves"
    ] and checks["during_callback_overrun_starves"]
    candidate_label_mismatch = not checks["frozen_gate_matches_observed_outcome"]
    passed = all(checks[k] for k in checks if k != "frozen_gate_matches_observed_outcome")
    return {
        "schema": "issue59-scorer-tail-command-priority-a02-audit-v1",
        "source_hash_checks": hashes,
        "checks": checks,
        "behavioral_gate": "FAIL_OS_READY_COMMAND_STARVATION_ON_SAMPLE_OVERRUN" if behavioral_fail else "NOT_ESTABLISHED",
        "candidate_label_mismatch": candidate_label_mismatch,
        "passed": sum(v for k, v in checks.items() if k != "frozen_gate_matches_observed_outcome"),
        "total": len(checks) - 1,
        "disposition": "PASS_AUDIT_FAIL_REPRODUCED_CANDIDATE_LABEL_MISMATCH" if passed and behavioral_fail and candidate_label_mismatch
                       else "PASS_AUDIT_FAIL_REPRODUCED" if passed and behavioral_fail
                       else "AUDIT_FAILED",
    }


def main() -> None:
    raw = json.loads((ROOT / "RESULT_V3.json").read_text(encoding="utf-8"))
    output = audit(raw)
    (ROOT / "AUDIT.json").write_text(json.dumps(output, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
