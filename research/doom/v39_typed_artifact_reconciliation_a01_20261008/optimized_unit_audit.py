import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results" / "a01" / "UNIT_OPTIMIZED_AUDIT.json"
if OUT.exists():
    raise SystemExit("STOP_OPTIMIZED_AUDIT_EXISTS")

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    freeze = json.loads((ROOT / "UNIT_OPTIMIZED_AUDIT_FREEZE.json").read_text(encoding="utf-8"))
    baseline_path = ROOT / "results" / "a01" / "UNIT_BASELINE_OPTIMIZED.txt"
    candidate_path = ROOT / "results" / "a01" / "UNIT_CANDIDATE_OPTIMIZED.txt"
    baseline = baseline_path.read_text(encoding="utf-8")
    candidate = candidate_path.read_text(encoding="utf-8")
    checks = {
        "runner_sha": sha(ROOT / freeze["runner"]) == freeze["runner_sha256"],
        "candidate_source_sha": sha(ROOT / "candidate/research/doom/doom_typed_observation_v1.py")
            == freeze["candidate_source_sha256"],
        "test_sha": sha(ROOT / "candidate/research/doom/test_doom_typed_artifact_reconciliation_v1.py")
            == freeze["unit_test_sha256"],
        "baseline_log_sha": sha(baseline_path) == freeze["baseline_log_sha256"],
        "candidate_log_sha": sha(candidate_path) == freeze["candidate_log_sha256"],
        "baseline_optimized_red": (
            "optimized=true" in baseline and "exit=1\n" in baseline and
            "Ran 3 tests" in baseline and "FAILED (failures=5)" in baseline
        ),
        "candidate_optimized_green": (
            "optimized=true" in candidate and "exit=0\n" in candidate and
            "Ran 3 tests" in candidate and "OK" in candidate and "FAILED" not in candidate
        ),
    }
    audit = {
        "schema": "issue8566-reconcile-alias-a01-optimized-unit-audit-v1",
        "checks": checks,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "passed": all(checks.values()),
        "baseline": {"exit": 1, "failures": 5, "tests": 3},
        "candidate": {"exit": 0, "failures": 0, "tests": 3},
        "audit_scope": "read-only integrity and output reconstruction; not an additional test run",
    }
    OUT.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n",
                   encoding="utf-8")
    print(json.dumps({"passed": audit["passed"],
                      "checks_passed": audit["checks_passed"],
                      "checks_total": audit["checks_total"]}, sort_keys=True))
    if not audit["passed"]:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
