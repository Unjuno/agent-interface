#!/usr/bin/env python3
"""Independent raw audit for construction attempt 02."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    freeze = json.loads((HERE / "FREEZE_ATTEMPT_02.json").read_text())
    result = json.loads((HERE / "out/attempt-02/RESULT.json").read_text())
    source_checks = {
        relative: (HERE / relative).is_file() and sha(HERE / relative) == digest
        for relative, digest in freeze["source_sha256"].items()
    }
    fixture_checks = {
        relative: (HERE / relative).is_file() and sha(HERE / relative) == digest
        for relative, digest in freeze["fixture_sha256"].items()
    }
    harness_checks = {
        relative: (HERE / relative).is_file() and sha(HERE / relative) == digest
        for relative, digest in freeze["harness_sha256"].items()
    }
    terminals = result["action_terminal_events"]
    programs = result["completed_adapter_programs"]
    checks = {
        "study_and_source_match_freeze": result["study"] == freeze["study"] and result["source_commit"] == freeze["source_commit"],
        "source_hashes_match": all(source_checks.values()),
        "fixture_hashes_match": all(fixture_checks.values()),
        "harness_hashes_match": all(harness_checks.values()),
        "callback_failed_on_check_four": result["callback_checks"] == 4,
        "one_checked_client_command": result["client_command_count"] == 1,
        "one_completed_core_action": len(terminals) == 1 and terminals[0].get("status") == "completed",
        "completed_action_release_verified_empty": len(programs) == 1 and programs[0].get("status") == "completed" and programs[0].get("release") == {"verified": True, "keys_down": [], "buttons_down": []},
        "callback_exception_escaped": result["escaped_exception"] == {"type": "RuntimeError", "message": "synthetic cancellation source unavailable"},
        "no_adapter_receipt_returned": result["adapter_returned_receipt"] is False and result["returned_receipt"] is None,
        "no_runtime_finished_event": result["runtime_finished_events"] == [],
        "no_second_action": result["client_command_count"] == 1,
    }
    out = {
        "schema": "compiled_cancel_receipt_failure_audit_v2",
        "study": freeze["study"],
        "disposition": "PASS_REPRODUCED_COMPLETED_PREFIX_RECEIPT_GAP" if all(checks.values()) else "AUDIT_FAIL",
        "passed": all(checks.values()),
        "checks": checks,
        "source_hash_checks": source_checks,
        "fixture_hash_checks": fixture_checks,
        "harness_hash_checks": harness_checks,
        "scope": result["scope"],
    }
    path = HERE / "out/attempt-02/AUDIT.json"
    path.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0 if out["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
