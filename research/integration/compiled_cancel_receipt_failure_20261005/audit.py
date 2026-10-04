#!/usr/bin/env python3
"""Independent raw-result and source-identity audit."""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    freeze = json.loads((HERE / "FREEZE.json").read_text())
    result = json.loads((HERE / "out/RESULT.json").read_text())
    source_checks = {
        relative: (HERE / relative).is_file() and sha(HERE / relative) == digest
        for relative, digest in freeze["source_sha256"].items()
    }
    fixture_checks = {
        relative: (HERE / relative).is_file() and sha(HERE / relative) == digest
        for relative, digest in freeze["fixture_sha256"].items()
    }
    terminals = result["action_terminal_events"]
    programs = result["completed_adapter_programs"]
    checks = {
        "source_commit_matches_freeze": result["source_commit"] == freeze["source_commit"],
        "source_hashes_match": all(source_checks.values()),
        "fixture_hashes_match": all(fixture_checks.values()),
        "callback_failed_on_frozen_check": result["callback_checks"] == 4,
        "only_one_checked_client_command": result["client_command_count"] == 1,
        "one_completed_core_action": len(terminals) == 1 and terminals[0].get("status") == "completed",
        "verified_empty_release": len(programs) == 1 and programs[0].get("status") == "completed" and programs[0].get("release") == {"verified": True, "keys_down": [], "buttons_down": []},
        "no_runtime_finish_receipt_event": result["runtime_finished_events"] == [],
        "adapter_did_not_return_receipt": result["adapter_returned_receipt"] is False and result["returned_receipt"] is None,
        "callback_exception_escaped": result["escaped_exception"] == {"type": "RuntimeError", "message": "synthetic cancellation source unavailable"},
        "no_second_action": result["client_command_count"] == 1,
    }
    disposition = "PASS_REPRODUCED_COMPLETED_PREFIX_RECEIPT_GAP" if all(checks.values()) else "AUDIT_FAIL"
    audit = {
        "schema": "compiled_cancel_receipt_failure_audit_v1",
        "study": freeze["study"],
        "disposition": disposition,
        "passed": all(checks.values()),
        "checks": checks,
        "source_hash_checks": source_checks,
        "fixture_hash_checks": fixture_checks,
        "scientific_interpretation": "The synthetic callback exception escapes after one completed, released action without a typed adapter receipt.",
        "scope": result["scope"],
    }
    (HERE / "out/AUDIT.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    print(json.dumps(audit, indent=2, sort_keys=True))
    return 0 if audit["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
