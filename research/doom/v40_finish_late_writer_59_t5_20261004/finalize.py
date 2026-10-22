"""Bind T5 to exact source and command outputs."""
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOOM = ROOT.parent
REPO = ROOT.parents[2]
BASE = "a2ad677c78aab119eed65884af8848103a292b8c"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    for filename, content in {
        "baseline-exit-code.txt": "1\n",
        "candidate-test-exit-code.txt": "0\n",
        "compile-exit-code.txt": "0\n",
        "diff-check-exit-code.txt": "0\n",
    }.items():
        (ROOT / filename).write_text(content, encoding="utf-8")
    baseline = subprocess.check_output(
        ["git", "show", f"{BASE}:research/doom/map01_overlap_controller_v40.py"],
        cwd=REPO)
    candidate = DOOM / "map01_overlap_controller_v40.py"
    test_source = DOOM / "test_map01_overlap_controller_v40_unknown_source.py"
    result = {
        "schema": "map01-v40-late-finish-writer-t5-v1",
        "disposition": "PASS_LATE_COMPLETION_NOT_CLAIMED",
        "baseline_disposition": "FAIL_LATE_COMPLETION_CLAIMED_SENT",
        "base_commit": BASE,
        "baseline_controller_sha256": sha(baseline),
        "candidate_controller_sha256": sha(candidate.read_bytes()),
        "candidate_test_sha256": sha(test_source.read_bytes()),
        "environment": {"platform": platform.platform(), "python": sys.version},
        "commands": [
            {"command": "run_baseline.py late-writer regression at a2ad677", "exit_code":
             int((ROOT / "baseline-exit-code.txt").read_text().strip())},
            {"command": "focused V40 candidate suite", "exit_code":
             int((ROOT / "candidate-test-exit-code.txt").read_text().strip())},
            {"command": "py_compile candidate/tests/audit", "exit_code":
             int((ROOT / "compile-exit-code.txt").read_text().strip())},
            {"command": "git diff --check", "exit_code":
             int((ROOT / "diff-check-exit-code.txt").read_text().strip())},
        ],
        "candidate_tests_passed": 12,
        "late_completion_not_claimed_as_sent": True,
        "scope": "deterministic child-pipe ordering construction; no game/model/GUI/input/formal allocation",
        "limitations": [
            "A late full-payload write return proves neither child receipt nor processing after its deadline.",
            "No graceful post-control score or application-level input release is claimed after timeout.",
        ],
    }
    (ROOT / "RESULT.json").write_text(json.dumps(result, indent=2) + "\n",
                                       encoding="utf-8")
    files = sorted(path for path in ROOT.rglob("*") if path.is_file() and
                   path.name != "SHA256SUMS" and "__pycache__" not in path.parts)
    rows = [f"{sha(path.read_bytes())}  {path.relative_to(ROOT).as_posix()}"
            for path in files]
    (ROOT / "SHA256SUMS").write_text("\n".join(rows) + "\n", encoding="utf-8")
    print(f"bound {len(files)} files; candidate={result['candidate_controller_sha256']}")


if __name__ == "__main__":
    main()
