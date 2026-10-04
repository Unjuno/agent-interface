"""Independent checks over retained cleanup-overlap run logs."""
from pathlib import Path


HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
baseline = (RESULTS / "RAW_BASELINE.txt").read_text(encoding="utf-8")
candidate = (RESULTS / "RAW_CANDIDATE.txt").read_text(encoding="utf-8")
adjacent = (RESULTS / "RAW_ADJACENT.txt").read_text(encoding="utf-8")
checks = {
    "baseline_reproduces_false_positive": (
        "FAILED (failures=1)" in baseline
        and "ordinary_release_candidate'] is False" in baseline
    ),
    "candidate_suite_passes_21": "Ran 21 tests" in candidate and "OK" in candidate,
    "adjacent_suites_pass_29": "Ran 29 tests" in adjacent and "OK" in adjacent,
    "inside_bracket_case_passes": "test_cleanup_inside_explicit_release_bracket_is_not_ordinary" in candidate,
    "outside_bracket_control_passes": "test_cleanup_outside_explicit_release_bracket_keeps_ordinary_release" in candidate,
    "missing_log_case_passes": "test_missing_cleanup_log_fails_closed" in candidate,
    "swap_limit_warning_retained": "does not support swap limit" in candidate,
}
for name, passed in checks.items():
    print(f"{'PASS' if passed else 'FAIL'} {name}")
if not all(checks.values()):
    raise SystemExit(1)
print(f"PASS {len(checks)} independent raw-log checks")
