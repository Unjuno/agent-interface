"""Verify T5's frozen-baseline failure and repaired late-writer accounting."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOOM = ROOT.parent
REPO = ROOT.parents[2]
BASE = "a2ad677c78aab119eed65884af8848103a292b8c"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    baseline = subprocess.check_output(
        ["git", "show", f"{BASE}:research/doom/map01_overlap_controller_v40.py"],
        cwd=REPO)
    candidate = (DOOM / "map01_overlap_controller_v40.py").read_bytes()
    test_source = (DOOM / "test_map01_overlap_controller_v40_unknown_source.py").read_bytes()
    baseline_output = (ROOT / "baseline-output.txt").read_text(encoding="utf-8")
    candidate_output = (ROOT / "candidate-suite-output.txt").read_text(encoding="utf-8")
    result = json.loads((ROOT / "RESULT.json").read_text(encoding="utf-8"))

    assert sha(baseline) == result["baseline_controller_sha256"]
    assert sha(candidate) == result["candidate_controller_sha256"]
    assert sha(test_source) == result["candidate_test_sha256"]
    assert (ROOT / "baseline-exit-code.txt").read_text().strip() == "1"
    assert "FAIL: test_late_finish_writer_success_does_not_claim_delivery" in baseline_output
    assert "True is not false" in baseline_output
    assert (ROOT / "candidate-test-exit-code.txt").read_text().strip() == "0"
    assert "Ran 12 tests" in candidate_output and "OK" in candidate_output
    assert "Ran 12 tests" in candidate_output
    assert (ROOT / "compile-exit-code.txt").read_text().strip() == "0"
    assert (ROOT / "diff-check-exit-code.txt").read_text().strip() == "0"
    assert result["disposition"] == "PASS_LATE_COMPLETION_NOT_CLAIMED"
    assert result["late_completion_not_claimed_as_sent"] is True
    assert result["candidate_tests_passed"] == 12
    print("PASS: a2ad baseline late-send false-success reproduced; candidate keeps it unconfirmed; 12 tests pass")


if __name__ == "__main__":
    main()
