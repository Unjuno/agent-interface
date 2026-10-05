"""Read-only binding audit for the retained local V39 regression outputs."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    frozen = json.loads((ROOT / "FROZEN.json").read_text())
    checks = {
        "candidate_controller_hash": sha256(ROOT / frozen["candidate_controller"])
        == frozen["candidate_controller_sha256"],
        "candidate_test_hash": sha256(ROOT / frozen["candidate_test"])
        == frozen["candidate_test_sha256"],
        "baseline_controller_hash": sha256(ROOT / frozen["baseline_controller"])
        == frozen["baseline_controller_sha256"],
        "htdcu_present": all(
            f"## {heading}" in (ROOT / "H-T-D-C-U.md").read_text()
            for heading in ("H — Hypothesis", "T — Test", "D — Decision",
                            "C — Counterexamples and alternatives", "U — Limits")),
    }
    for filename, case_count in (
            ("renewal-normal.txt", 4), ("renewal-optimized.txt", 4),
            ("wait-normal.txt", 15), ("wait-optimized.txt", 15)):
        output = (ROOT / "results" / filename).read_text()
        checks[filename] = f"Ran {case_count} tests" in output and "OK" in output
    baseline = (ROOT / "results" / "base-red.txt").read_text()
    checks["baseline_expected_failure"] = (
        "unexpected keyword argument 'allow_rejection'" in baseline and "FAILED" in baseline)
    full = (ROOT / "results" / "full-controller-import.txt").read_text()
    checks["full_suite_dependency_hold"] = "No module named 'PIL'" in full
    checks["pycompile_empty_success"] = not (ROOT / "results" / "pycompile.txt").read_text()
    checks["diff_check_empty_success"] = not (ROOT / "results" / "diff-check.txt").read_text()
    print(json.dumps({"scope": "artifact_binding_and_result_shape_only",
                      "checks": checks,
                      "passed": all(checks.values())}, indent=2, sort_keys=True))
    raise SystemExit(0 if all(checks.values()) else 1)


if __name__ == "__main__":
    main()
