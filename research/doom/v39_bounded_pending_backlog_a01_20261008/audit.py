from __future__ import annotations

import ast
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
FREEZE = "6ea1269defb6d48a607f13b08f1aa2d223ba06e9"
EXPECTED_BASE_BLOBS = {
    "research/doom/map01_overlap_controller_v39.py":
        "f7b66279d87ebc3704ccef1b6a5ce646611c890b",
    "research/live_control/executor_v12.py":
        "7e9bb6286d5f674108688ba092300a8ad2421ba9",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(ROOT), *args], text=True).strip()


def main() -> int:
    assert git("cat-file", "-t", FREEZE) == "commit"
    actual_base_blobs = {
        path: git("rev-parse", f"{FREEZE}:{path}")
        for path in EXPECTED_BASE_BLOBS
    }
    assert actual_base_blobs == EXPECTED_BASE_BLOBS

    result = json.loads((HERE / "baseline_result.json").read_text(encoding="utf-8"))
    assert result["main_commit"] == FREEZE
    assert result["status"] == (
        "REPRODUCED_STALE_ANSWER_REACHES_EXECUTOR_REJECTION_WITHOUT_REPLAN")
    assert result["drain"]["latest_sequence_used"] == 11
    assert result["drain"]["hard_crossing_sequence_left_queued"] == 12
    assert result["executor"]["outcome"] == "rejected"
    assert result["executor"]["reason"] == (
        "latest observation sequence required before input")

    controller_path = ROOT / "research/doom/map01_overlap_controller_v39.py"
    controller = controller_path.read_text(encoding="utf-8")
    ast.parse(controller)
    assert "MAX_PENDING_OBSERVATION_EVENTS = 256" in controller
    assert "MAX_PENDING_OBSERVATION_RECOVERY_BATCHES = 4" in controller
    assert 'elif drained["pending_events"]:' in controller
    assert "recovery = recover_pending_observation_backlog(" in controller
    assert '"pending_observation_recovery":recovery' in controller

    test_path = ROOT / "research/doom/test_map01_v39_pending_observation_drain.py"
    test_source = test_path.read_text(encoding="utf-8")
    ast.parse(test_source)
    required_cases = (
        "test_boundary_hard_crossing_is_processed_before_answer_reuse",
        "test_drain_stops_at_fixed_budget_and_reports_remaining_backlog",
        "test_continuous_backlog_recovery_exhausts_a_finite_budget",
        "test_stale_executor_rejection_recovers_then_admits_fresh_sequence",
    )
    assert all(case in test_source for case in required_cases)

    manifest = json.loads((HERE / "sha256.json").read_text(encoding="utf-8"))
    missing = []
    mismatched = []
    for relative_path, expected in manifest.items():
        path = ROOT / relative_path
        if not path.is_file():
            missing.append({"path": relative_path, "expected_sha256": expected})
        else:
            actual = sha256(path)
            if actual == expected:
                continue
            mismatched.append({"path": relative_path,
                               "expected_sha256": expected,
                               "actual_sha256": actual})

    log_path = HERE / "unittest.log"
    if not log_path.is_file() and not mismatched and len(missing) == 1:
        print(json.dumps({
            "status": "AUDIT_HOLD_MISSING_RETAINED_TEST_LOG",
            "freeze": FREEZE,
            "base_blobs": actual_base_blobs,
            "baseline_and_source_checks": "PASS",
            "missing_manifest_entries": missing,
            "mismatched_manifest_entries": mismatched,
            "historical_test_result": "UNVERIFIED",
            "scope": "The package claims 48 tests passed, but the retained raw unittest.log is absent; no test result is inferred from the manifest digest alone.",
        }, indent=2))
        return 2

    if not log_path.is_file():
        print(json.dumps({
            "status": "AUDIT_FAIL",
            "freeze": FREEZE,
            "missing_manifest_entries": missing,
            "mismatched_manifest_entries": mismatched,
            "test_log_valid": False,
        }, indent=2))
        return 1

    log = log_path.read_text(encoding="utf-8")
    match = re.search(r"Ran (\d+) tests in ([0-9.]+)s", log)
    if (missing or mismatched or not match or match.group(1) != "48" or
            not log.rstrip().endswith("OK")):
        print(json.dumps({
            "status": "AUDIT_FAIL",
            "freeze": FREEZE,
            "missing_manifest_entries": missing,
            "mismatched_manifest_entries": mismatched,
            "test_log_valid": bool(match and match.group(1) == "48" and
                                   log.rstrip().endswith("OK")),
        }, indent=2))
        return 1

    print(json.dumps({
        "status": "AUDIT_PASS",
        "freeze": FREEZE,
        "base_blobs": actual_base_blobs,
        "tests": int(match.group(1)),
        "elapsed_seconds": float(match.group(2)),
        "checked_hashes": len(manifest),
        "scope": "provenance, pinned baseline outcome, bounded-recovery wiring, and retained unit-test result; not a live runtime audit",
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
