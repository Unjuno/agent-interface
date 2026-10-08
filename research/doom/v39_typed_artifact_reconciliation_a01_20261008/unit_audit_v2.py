import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE_ROOT = Path(os.environ.get("SOURCE_ROOT", ROOT))
OUT = ROOT / "results" / "a01" / "UNIT_AUDIT_V2.json"
if OUT.exists():
    raise SystemExit("STOP_UNIT_AUDIT_V2_EXISTS")

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    freeze = json.loads((ROOT / "UNIT_TEST_FREEZE.json").read_text(encoding="utf-8"))
    baseline_path = ROOT / "results" / "a01" / "UNIT_BASELINE.txt"
    candidate_path = ROOT / "results" / "a01" / "UNIT_CANDIDATE.txt"
    baseline = baseline_path.read_text(encoding="utf-8")
    candidate = candidate_path.read_text(encoding="utf-8")
    initial_audit = json.loads(
        (ROOT / "results" / "a01" / "UNIT_AUDIT.json").read_text(encoding="utf-8")
    )
    initial_failure = ROOT / "results" / "a01" / "UNIT_AUDIT_INITIAL_FAILURE.json"
    checks = {
        "baseline_test_sha": sha(SOURCE_ROOT / freeze["test"]) == freeze["test_sha256"],
        "candidate_test_sha": sha(ROOT / "candidate" / freeze["test"])
            == freeze["candidate_test_sha256"],
        "candidate_source_sha": sha(ROOT / "candidate/research/doom/doom_typed_observation_v1.py")
            == freeze["candidate_source_sha256"],
        "runner_sha": sha(ROOT / "run_unit_suite.py") == freeze["runner_sha256"],
        "baseline_log_sha": sha(baseline_path)
            == "931a48e8bb4a9bfebb220e208eb6f400f93532c50754d2d0cfc2711856861c16",
        "candidate_log_sha": sha(candidate_path)
            == "c20bdd4a21ffa660aa226b0a0136738f69268fdc8c5333bd7bff59b7ea8fd0cc",
        "prior_audit_failure_preserved": sha(ROOT / "results/a01/UNIT_AUDIT.json")
            == "0995fc6cd073362e6318673c788ed8f56af435e2d1b4611717f3cc5ea84260a5",
        "prior_audit_only_hash_typo": (
            initial_audit.get("passed") is False and
            initial_audit.get("checks", {}).get("baseline_log_sha") is False and
            sum(value is False for value in initial_audit["checks"].values()) == 1
        ),
        "initial_failure_record_sha": sha(initial_failure)
            == "50f53d508a859ffb4919d0539a7b8535f0601ce8fe8256d23c24b14014cb1f22",
        "baseline_expected_exit": "exit=1\n" in baseline,
        "baseline_all_five_aliases_reproduced":
            baseline.count("AssertionError: True is not false") == 5,
        "baseline_suite_inventory":
            "Ran 3 tests" in baseline and "FAILED (failures=5)" in baseline,
        "candidate_expected_exit": "exit=0\n" in candidate,
        "candidate_suite_passed":
            "Ran 3 tests" in candidate and "OK" in candidate and "FAILED" not in candidate,
    }
    audit = {
        "schema": "issue8566-reconcile-alias-a01-unit-audit-v2",
        "checks": checks,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "passed": all(checks.values()),
        "baseline": {"exit": 1, "failures": 5, "tests": 3},
        "candidate": {"exit": 0, "failures": 0, "tests": 3},
        "supersedes": "UNIT_AUDIT.json only; test outcomes and the failed first audit are retained unchanged",
        "audit_scope": "read-only source/test/log integrity and output reconstruction; not an additional test run",
    }
    OUT.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n",
                   encoding="utf-8")
    print(json.dumps({"passed": audit["passed"],
                      "checks_passed": audit["checks_passed"],
                      "checks_total": audit["checks_total"],
                      "baseline_failures": audit["baseline"]["failures"],
                      "candidate_exit": audit["candidate"]["exit"]},
                     sort_keys=True))
    if not audit["passed"]:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
