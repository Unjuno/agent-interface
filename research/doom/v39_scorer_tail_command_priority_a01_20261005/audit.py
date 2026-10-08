#!/usr/bin/env python3
"""Independent audit for the source-bound scorer-tail readiness probe."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
FREEZE = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))


def expected() -> dict[str, Any]:
    fast = {
        "name": "ready_fast_control",
        "ready_at_start": True,
        "ready_during_first_sample": False,
        "sample_duration_ns": 1_000_000,
        "sample_period_ns": 10_000_000,
        "sample_starts_ns": [0],
        "scorer_rows": 1,
        "readiness_checks": 1,
        "command_reads": 0,
        "tail": {
            "schema": "map01-scorer-post-release-tail-v1",
            "release_returned_ns": 0,
            "release_id": "program-1",
            "release_step": 2,
            "release_key": "d",
            "intent_token": "token-1",
            "started_ns": 0,
            "ended_ns": 1_000_000,
            "deadline_ns": 100_000_000,
            "tail_samples": 1,
            "total_samples": 1,
            "stop_condition_met": False,
            "deadline_overrun": False,
            "disposition": "CENSORED",
            "termination": "command_ready",
        },
    }
    def slow(name: str, *, ready_at_start: bool, ready_during: bool) -> dict[str, Any]:
        starts = [0, 25_000_000, 50_000_000, 75_000_000]
        return {
            "name": name,
            "ready_at_start": ready_at_start,
            "ready_during_first_sample": ready_during,
            "sample_duration_ns": 25_000_000,
            "sample_period_ns": 10_000_000,
            "sample_starts_ns": starts,
            "scorer_rows": 4,
            "readiness_checks": 0,
            "command_reads": 0,
            "tail": {
                "schema": "map01-scorer-post-release-tail-v1",
                "release_returned_ns": 0,
                "release_id": "program-1",
                "release_step": 2,
                "release_key": "d",
                "intent_token": "token-1",
                "started_ns": 0,
                "ended_ns": 100_000_000,
                "deadline_ns": 100_000_000,
                "tail_samples": 4,
                "total_samples": 4,
                "stop_condition_met": False,
                "deadline_overrun": False,
                "disposition": "CENSORED",
                "termination": "deadline",
            },
        }
    return {
        "schema": "issue59-scorer-tail-command-priority-a01-v1",
        "candidate_head": FREEZE["candidate_head"],
        "classification": "synthetic source-boundary construction; no runtime or live allocation",
        "sample_period_ns": 10_000_000,
        "tail_deadline_ns": 100_000_000,
        "max_samples": 10,
        "scenarios": [
            fast,
            slow("ready_at_entry_overrun", ready_at_start=True, ready_during=False),
            slow("command_arrives_during_overrun", ready_at_start=False, ready_during=True),
        ],
        "disposition": "FAIL_READY_COMMAND_STARVATION_ON_SAMPLE_OVERRUN",
        "scope": "command readiness is represented by a deterministic fake loop; scorer work is a synchronous fake call",
    }


def audit(result: dict[str, Any]) -> dict[str, Any]:
    pin_checks = {}
    for name, metadata in FREEZE["source_files"].items():
        data = (ROOT / "inputs" / name).read_bytes()
        pin_checks[name] = hashlib.sha256(data).hexdigest() == metadata["sha256"]
    expected_result = expected()
    checks = {
        "all_frozen_source_hashes_match": all(pin_checks.values()),
        "exact_result_reconstruction": type(result) is dict and result == expected_result,
        "fast_command_control_detects_readiness": (
            result.get("scenarios", [{}])[0].get("tail", {}).get("termination") == "command_ready"
            and result.get("scenarios", [{}])[0].get("readiness_checks") == 1
        ),
        "entry_overrun_starvation_reproduced": (
            result.get("scenarios", [{}, {}])[1].get("tail", {}).get("termination") == "deadline"
            and result.get("scenarios", [{}, {}])[1].get("readiness_checks") == 0
            and result.get("scenarios", [{}, {}])[1].get("scorer_rows") == 4
        ),
        "during_overrun_starvation_reproduced": (
            result.get("scenarios", [{}, {}, {}])[2].get("tail", {}).get("termination") == "deadline"
            and result.get("scenarios", [{}, {}, {}])[2].get("readiness_checks") == 0
            and result.get("scenarios", [{}, {}, {}])[2].get("scorer_rows") == 4
        ),
        "no_command_bytes_consumed": all(
            case.get("command_reads") == 0 for case in result.get("scenarios", [])
        ),
        "construction_only_disposition": result.get("disposition") == expected_result["disposition"],
    }
    return {
        "schema": "issue59-scorer-tail-command-priority-audit-v1",
        "checks": checks,
        "source_hash_checks": pin_checks,
        "passed": sum(checks.values()),
        "total": len(checks),
        "disposition": "PASS_AUDIT_FAIL_REPRODUCED" if all(checks.values())
                       else "AUDIT_FAILED",
    }


def main() -> None:
    result = json.loads((ROOT / "RESULT.json").read_text(encoding="utf-8"))
    report = audit(result)
    (ROOT / "AUDIT.json").write_text(
        json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
