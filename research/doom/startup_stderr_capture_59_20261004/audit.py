"""Independent audit for the early child-stderr capture construction packet."""
import hashlib
import json
import subprocess
from pathlib import Path


PACKET = Path(__file__).resolve().parent
REPO = PACKET.parents[2]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_at_commit(commit, path):
    content = subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=REPO)
    return hashlib.sha256(content).hexdigest()


def main():
    freeze = json.loads((PACKET / "FREEZE.json").read_text(encoding="utf-8"))
    for role in ("controller", "wait_test"):
        candidate = freeze["candidate"]
        assert sha256_at_commit(candidate["verification_commit"],
                                candidate[f"{role}_path"]) == candidate[f"{role}_sha256"]
        baseline = freeze["baseline"]
        blob = subprocess.check_output(
            ["git", "rev-parse", f"{freeze['base_commit']}:{baseline[f'{role}_path'] if role == 'controller' else baseline['wait_test_path']}"],
            cwd=REPO, text=True).strip()
        assert blob == baseline[f"{role}_git_blob"]

    index = freeze["index_entry"]
    assert sha256(REPO / index["path"]) == index["sha256"]

    for line in (PACKET / "FILES.sha256").read_text(encoding="utf-8").splitlines():
        digest, relative = line.split("  ", 1)
        assert sha256(PACKET / relative) == digest, relative

    out = PACKET / "out"
    red_sink = (out / "red-sink.txt").read_text(encoding="utf-8")
    red_diagnostic = (out / "red-diagnostic.txt").read_text(encoding="utf-8")
    green = (out / "green.txt").read_text(encoding="utf-8")
    assert "v39 must open a file-backed child-stderr sink" in red_sink
    assert "stderr.txt" in red_diagnostic and "not found" in red_diagnostic
    assert (out / "red-sink-exit.txt").read_text().strip() == "1"
    assert (out / "red-diagnostic-exit.txt").read_text().strip() == "1"
    assert "Ran 10 tests" in green and "OK" in green
    assert (out / "green-exit.txt").read_text().strip() == "0"
    assert (out / "pycompile-exit.txt").read_text().strip() == "0"
    assert (out / "diff-check-exit.txt").read_text().strip() == "0"
    followup = freeze["followup_01"]
    assert sha256(REPO / followup["wait_test_path"]) == followup["wait_test_sha256"]
    baseline_wiring = (PACKET / followup["baseline_output"]).read_text(encoding="utf-8")
    assert "must create the file-backed stderr sink" in baseline_wiring
    assert (PACKET / followup["baseline_exit"]).read_text(encoding="utf-8").strip() == str(followup["expected_baseline_exit"])
    followup_tests = (PACKET / followup["test_output"]).read_text(encoding="utf-8")
    assert "Ran 11 tests" in followup_tests and "OK" in followup_tests
    for key in ("test_exit", "compile_exit", "diff_check_exit"):
        assert (PACKET / followup[key]).read_text(encoding="utf-8").strip() == "0"
    print(json.dumps({"status": "PASS", "baseline_red": 2,
                      "candidate_tests": "10_PASS",
                      "followup_tests": "11_PASS",
                      "manifest_files": len((PACKET / "FILES.sha256").read_text().splitlines()),
                      "live_execution": False}, sort_keys=True))


if __name__ == "__main__":
    main()
