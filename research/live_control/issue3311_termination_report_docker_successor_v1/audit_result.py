"""Independent raw-output auditor for allocation 03; imports no test code."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(sys.argv[1]).resolve()
OUT = Path(sys.argv[2]).resolve()
SELF = ROOT / "research" / "live_control" / "issue3311_termination_report_docker_successor_v1"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    freeze = json.loads((SELF / "FREEZE.json").read_text(encoding="utf-8"))
    result_path = OUT / "RESULT.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    log = OUT / "test.stdout.txt"
    lines = log.read_text(encoding="utf-8").splitlines()
    ended = [line for line in lines if line.startswith(("Ran ", "OK", "FAILED"))]
    cases_root = OUT / "cases"
    actual_cases = sorted(p.name for p in cases_root.iterdir()) if cases_root.exists() else []
    expected_cases = sorted(name.rsplit(".", 1)[-1] for name in freeze["expected_tests"])
    source_errors = []
    for name, row in freeze["sources"].items():
        if sha(ROOT / row["path"]) != row["sha256"]:
            source_errors.append(name)
    checks = {
        "allocation_matches": result.get("allocation_id") == freeze["allocation_id"],
        "result_pass": result.get("status") == "PASS_TERMINATION_HOLD_CONTRACT_DOCKER_SCOPED",
        "all_tests_ran": result.get("test_count") == len(freeze["expected_tests"]),
        "no_test_failures": result.get("failures") == 0 and result.get("errors") == 0,
        "test_names_match": result.get("test_names") == freeze["expected_tests"],
        "case_artifacts_complete": actual_cases == expected_cases,
        "source_hashes_match": not source_errors,
        "log_reports_success": any(line.startswith("OK") for line in ended),
        "stdout_hash_matches": sha(log) == result.get("stdout_sha256"),
    }
    audit = {
        "schema": "issue3311-termination-docker-successor-audit-v1",
        "allocation_id": freeze["allocation_id"],
        "status": "PASS_INDEPENDENT_RAW_AUDIT" if all(checks.values()) else "FAIL_INDEPENDENT_RAW_AUDIT",
        "checks": checks,
        "expected_test_count": len(freeze["expected_tests"]),
        "actual_case_directories": actual_cases,
        "source_hash_mismatches": source_errors,
        "test_log_terminal_lines": ended,
    }
    (OUT / "AUDIT.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n",
                                    encoding="utf-8")
    print(json.dumps(audit, indent=2, sort_keys=True))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
