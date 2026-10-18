"""Independent consistency checks over retained cleanup-follow-up test logs."""
from pathlib import Path
import re
import subprocess


HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"


def exit_code(path):
    match = re.fullmatch(r"exit=(\d+)\s*", path.read_text(encoding="utf-8"))
    return None if match is None else int(match.group(1))


def passing_suite(log, expected, exit_value):
    lines = [line.strip() for line in log.splitlines() if line.strip()]
    summaries = re.findall(r"^Ran (\d+) tests? in [0-9.]+s$", log, re.MULTILINE)
    return (
        exit_value == 0 and len(summaries) == 1
        and int(summaries[0]) == expected and lines[-1:] == ["OK"]
        and not any(line.startswith(("FAILED", "ERROR:")) for line in lines)
    )


def audit():
    parent = (RESULTS / "RAW_PARENT_RED.txt").read_text(encoding="utf-8")
    backend = (RESULTS / "RAW_BACKEND_TESTS.txt").read_text(encoding="utf-8")
    owner = (RESULTS / "RAW_OWNER_TESTS.txt").read_text(encoding="utf-8")
    latest_parent = (RESULTS / "RAW_LATEST_PARENT_RED.txt").read_text(encoding="utf-8")
    rebased_backend = (RESULTS / "RAW_REBASED_BACKEND_TESTS.txt").read_text(encoding="utf-8")
    rebased_owner = (RESULTS / "RAW_REBASED_OWNER_TESTS.txt").read_text(encoding="utf-8")
    current_parent = (RESULTS / "RAW_7399_PARENT_RED.txt").read_text(encoding="utf-8")
    current_backend = (RESULTS / "RAW_7399_BACKEND_TESTS.txt").read_text(encoding="utf-8")
    current_owner = (RESULTS / "RAW_7399_OWNER_TESTS.txt").read_text(encoding="utf-8")
    current_parent = (RESULTS / "RAW_7399_PARENT_RED.txt").read_text(encoding="utf-8")
    current_backend = (RESULTS / "RAW_7399_BACKEND_TESTS.txt").read_text(encoding="utf-8")
    current_owner = (RESULTS / "RAW_7399_OWNER_TESTS.txt").read_text(encoding="utf-8")
    static = (RESULTS / "STATIC_EXIT.txt").read_text(encoding="utf-8")
    current_static = (RESULTS / "CURRENT_STATIC_EXIT.txt").read_text(encoding="utf-8")
    parent_digests = (HERE / "PARENT_SOURCE_SHA256.txt").read_text(encoding="utf-8")
    test_source = (
        HERE.parents[2] / "research/doom/test_doom_typed_release_backend_v3.py"
    ).read_text(encoding="utf-8")
    parent_commit = parent_digests.splitlines()[0].split("=", 1)[1]
    predecessor_manifest = subprocess.run(
        ["git", "show", f"{parent_commit}:research/doom/"
         "map01-v39-release-cleanup-overlap-v1/SHA256SUMS"],
        cwd=HERE.parents[2], check=True, capture_output=True, text=True,
    ).stdout
    red_ok = (
        exit_code(RESULTS / "PARENT_RED_EXIT.txt") == 1
        and len(re.findall(r"^FAIL: test_malformed_", parent, re.MULTILINE)) == 3
        and "Ran 3 tests" in parent and "FAILED (failures=3)" in parent
    )
    backend_ok = passing_suite(
        backend, 24, exit_code(RESULTS / "BACKEND_EXIT.txt"))
    owner_ok = passing_suite(
        owner, 8, exit_code(RESULTS / "OWNER_EXIT.txt"))
    latest_red_ok = (
        exit_code(RESULTS / "LATEST_PARENT_RED_EXIT.txt") == 1
        and len(re.findall(r"^FAIL: test_malformed_", latest_parent, re.MULTILINE)) == 3
        and "Ran 3 tests" in latest_parent and "FAILED (failures=3)" in latest_parent
    )
    rebased_backend_ok = passing_suite(
        rebased_backend, 24, exit_code(RESULTS / "REBASED_BACKEND_EXIT.txt"))
    rebased_owner_ok = passing_suite(
        rebased_owner, 8, exit_code(RESULTS / "REBASED_OWNER_EXIT.txt"))
    current_parent_red_ok = (
        exit_code(RESULTS / "7399_PARENT_RED_EXIT.txt") == 1
        and "Ran 1 test" in current_parent
        and "FAILED (failures=1)" in current_parent
        and "ordinary_release_candidate']" in current_parent
    )
    current_backend_ok = passing_suite(
        current_backend, 26, exit_code(RESULTS / "7399_BACKEND_EXIT.txt"))
    current_owner_ok = passing_suite(
        current_owner, 8, exit_code(RESULTS / "7399_OWNER_EXIT.txt"))
    current_parent_red_ok = (
        exit_code(RESULTS / "7399_PARENT_RED_EXIT.txt") == 1
        and "Ran 1 test" in current_parent
        and "FAILED (failures=1)" in current_parent
        and "ordinary_release_candidate']" in current_parent
    )
    current_backend_ok = passing_suite(
        current_backend, 26, exit_code(RESULTS / "7399_BACKEND_EXIT.txt"))
    current_owner_ok = passing_suite(
        current_owner, 8, exit_code(RESULTS / "7399_OWNER_EXIT.txt"))
    names_ok = all(name in test_source for name in (
        "test_malformed_cleanup_timestamp_fails_closed",
        "test_malformed_owner_record_fails_closed",
        "test_malformed_release_bracket_fails_closed",
    ))
    mutations_rejected = (
        not passing_suite(backend + "\nFAILED (failures=1)\n", 24, 0)
        and not passing_suite(backend, 24, 1)
    )
    static_ok = static == "py_compile_exit=0\ndiff_check_exit=0\n"
    current_static_ok = current_static == "py_compile_exit=0\ndiff_check_exit=0\n"
    predecessor_preserved = all(
        line in predecessor_manifest for line in parent_digests.splitlines()[1:]
    )
    checks = {
        "parent_fails_all_three_adversarial_regressions": red_ok,
        "refreshed_parent_fails_all_three_adversarial_regressions": latest_red_ok,
        "candidate_backend_24_exit_zero": backend_ok,
        "adjacent_owner_suite_8_exit_zero": owner_ok,
        "rebased_backend_24_exit_zero": rebased_backend_ok,
        "rebased_owner_suite_8_exit_zero": rebased_owner_ok,
        "pr7399_parent_fails_malformed_bracket": current_parent_red_ok,
        "pr7399_backend_26_exit_zero": current_backend_ok,
        "pr7399_adjacent_owner_8_exit_zero": current_owner_ok,
        "pr7399_parent_fails_malformed_bracket": current_parent_red_ok,
        "pr7399_backend_26_exit_zero": current_backend_ok,
        "pr7399_adjacent_owner_8_exit_zero": current_owner_ok,
        "all_adversarial_tests_present": names_ok,
        "contradictory_summary_and_exit_rejected": mutations_rejected,
        "static_checks_exit_zero": static_ok,
        "pr7399_rebase_static_checks_exit_zero": current_static_ok,
        "parent_source_hashes_match_untouched_predecessor_manifest": predecessor_preserved,
    }
    for name, passed in checks.items():
        print(f"{'PASS' if passed else 'FAIL'} {name}")
    if not all(checks.values()):
        raise SystemExit(1)
    print(f"PASS {len(checks)} independent retained-log checks")


if __name__ == "__main__":
    audit()
