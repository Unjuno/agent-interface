"""Independent, terminal-summary and exit-bound checks over retained logs."""
from pathlib import Path
import re


HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"


def terminal_run_matches(log, expected_tests, exit_text, *, passed):
    """Require one unittest summary, a consistent terminal status, and exit."""
    exit_match = re.fullmatch(r"exit=(\d+)\s*", exit_text)
    if exit_match is None:
        return False
    exit_code = int(exit_match.group(1))
    summaries = re.findall(r"^Ran (\d+) tests? in [0-9.]+s$", log, re.MULTILINE)
    if len(summaries) != 1 or int(summaries[0]) != expected_tests:
        return False
    terminal = [line.strip() for line in log.splitlines() if line.strip()]
    if not terminal:
        return False
    failed_lines = [line for line in terminal if line.startswith(("FAILED", "ERROR:"))]
    if passed:
        return terminal[-1] == "OK" and not failed_lines and exit_code == 0
    return terminal[-1].startswith("FAILED (") and exit_code != 0


def audit_retained():
    baseline = (RESULTS / "RAW_BASELINE.txt").read_text(encoding="utf-8")
    candidate = (RESULTS / "RAW_CANDIDATE.txt").read_text(encoding="utf-8")
    owner_wrapper = (RESULTS / "RAW_OWNER_WRAPPER_HOST.txt").read_text(encoding="utf-8")
    baseline_direct = (RESULTS / "RAW_BASELINE_DIRECT_BOUNDARY.txt").read_text(encoding="utf-8")
    candidate_wslc = (RESULTS / "RAW_CANDIDATE_WSLC_DIRECT_BOUNDARY.txt").read_text(encoding="utf-8")
    adjacent = (RESULTS / "RAW_ADJACENT.txt").read_text(encoding="utf-8")
    candidate_exit = (RESULTS / "CANDIDATE_EXIT.txt").read_text(encoding="utf-8")
    owner_wrapper_exit = (RESULTS / "OWNER_WRAPPER_EXIT.txt").read_text(encoding="utf-8")
    candidate_wslc_exit = (RESULTS / "CANDIDATE_WSLC_EXIT.txt").read_text(encoding="utf-8")
    baseline_direct_exit = (RESULTS / "BASELINE_DIRECT_EXIT.txt").read_text(encoding="utf-8")
    adjacent_exit = (RESULTS / "ADJACENT_EXIT.txt").read_text(encoding="utf-8")
    baseline_exit = (RESULTS / "BASELINE_EXIT.txt").read_text(encoding="utf-8")
    baseline_exit_match = re.fullmatch(
        r"expected regression failure; observed exit=(\d+)\s*", baseline_exit)
    checks = {
        "baseline_reproduces_false_positive": (
            baseline_exit_match is not None
            and terminal_run_matches(
                baseline, 1, f"exit={baseline_exit_match.group(1)}", passed=False)
            and "FAILED (failures=1)" in baseline
            and "ordinary_release_candidate'] is False" in baseline
        ),
        "execute_path_candidate_passes_21_exit_zero": terminal_run_matches(
            candidate, 21, candidate_exit, passed=True),
        "owner_wrapper_passes_8_exit_zero": terminal_run_matches(
            owner_wrapper, 8, owner_wrapper_exit, passed=True),
        "direct_boundary_parent_reproduces_false_positive": (
            terminal_run_matches(baseline_direct, 1, "exit=1", passed=False)
            and "ordinary_release_candidate'] is False" in baseline_direct
            and baseline_direct_exit.strip() == "expected regression failure; observed exit=1"
        ),
        "original_wslc_direct_boundary_candidate_passes": terminal_run_matches(
            candidate_wslc, 21, candidate_wslc_exit, passed=True),
        "adjacent_suites_pass_29_exit_zero": terminal_run_matches(
            adjacent, 29, adjacent_exit, passed=True),
        "cleanup_case_exercises_execute_path": (
            "test_cleanup_inside_explicit_release_bracket_is_not_ordinary" in candidate
            and "test_cleanup_inside_explicit_release_bracket_is_not_ordinary" in
            (HERE.parents[2] / "research/doom/test_doom_typed_release_backend_v3.py").read_text(encoding="utf-8")
            and "self.assertEqual(owner.explicit_key_release_requests, [])" in
            (HERE.parents[2] / "research/doom/test_doom_typed_release_backend_v3.py").read_text(encoding="utf-8")
        ),
        "outside_bracket_control_passes": "test_cleanup_outside_explicit_release_bracket_keeps_ordinary_release" in candidate,
        "missing_log_case_passes": "test_missing_cleanup_log_fails_closed" in candidate,
        "swap_limit_warning_retained": "does not support swap limit" in candidate_wslc,
        "contradictory_failure_summary_rejected": not terminal_run_matches(
            candidate + "\nFAILED (failures=1)\n", 21, candidate_exit, passed=True),
        "contradictory_nonzero_exit_rejected": not terminal_run_matches(
            candidate, 21, "exit=1", passed=True),
    }
    for name, passed in checks.items():
        print(f"{'PASS' if passed else 'FAIL'} {name}")
    if not all(checks.values()):
        raise SystemExit(1)
    print(f"PASS {len(checks)} independent raw-log checks")


if __name__ == "__main__":
    audit_retained()
