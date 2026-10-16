"""Independently verify the retained V40 finish-pipe fault injection."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOOM = ROOT.parent
REPO = ROOT.parents[2]
BASE = "6bd23799ea899e0c90a3a82299a19c55a5e073c9"
OLD_SOURCE = "0e1183a26cb0f816dcde97bb80f63f436ae306fd356a2ccef160e9ba5fe2add4"
OLD_TEST = "0b075e89e0a4341165dee1d1a9834b7f8a6661ce386276031ae0a654f2298e6a"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    candidate = DOOM / "map01_overlap_controller_v40.py"
    test_source = DOOM / "test_map01_overlap_controller_v40_unknown_source.py"
    old_source = subprocess.check_output(
        ["git", "show", f"{BASE}:research/doom/map01_overlap_controller_v40.py"],
        cwd=REPO)
    baseline_output = (ROOT / "baseline-test-output.txt").read_text(encoding="utf-8")
    candidate_output = (ROOT / "candidate-suite-output.txt").read_text(encoding="utf-8")
    source = candidate.read_text(encoding="utf-8")
    result = json.loads((ROOT / "RESULT.json").read_text(encoding="utf-8"))

    assert sha(old_source) == OLD_SOURCE == result["baseline_controller_sha256"]
    assert sha((ROOT / "baseline-test-source.py.txt").read_bytes()) == OLD_TEST
    assert OLD_TEST == result["baseline_test_sha256"]
    assert sha(candidate.read_bytes()) == result["candidate_controller_sha256"]
    assert sha(test_source.read_bytes()) == result["candidate_test_sha256"]
    assert (ROOT / "baseline-test-exit-code.txt").read_text().strip() == "1"
    assert "FAIL: test_finish_write_backpressure" in baseline_output
    assert "finish_timeout must bound delivery to a non-reading child" in baseline_output
    assert (ROOT / "candidate-test-exit-code.txt").read_text().strip() == "0"
    assert "Ran 11 tests" in candidate_output and "OK" in candidate_output
    assert (ROOT / "compile-exit-code.txt").read_text().strip() == "0"
    assert (ROOT / "diff-check-exit-code.txt").read_text().strip() == "0"
    for required in ("_send_finish_bounded", "_retire_owned_child",
                     "finish_send_timeout", "child_termination_requested",
                     "child_kill_requested"):
        assert required in source
    assert result["disposition"] == "PASS_BOUNDED_FINISH_DELIVERY_CONSTRUCTION"
    assert result["baseline_disposition"] == "FAIL_FINISH_DELIVERY_UNBOUNDED"
    assert result["candidate_tests_passed"] == 11
    print("PASS: frozen baseline failure, candidate source hashes, 11-test pass, and fail-closed receipt fields verified")


if __name__ == "__main__":
    main()
