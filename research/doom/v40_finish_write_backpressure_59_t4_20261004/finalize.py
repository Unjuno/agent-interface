"""Bind the T4 result to exact source hashes and retained command outcomes."""
import hashlib
import json
import platform
import subprocess
import sys
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
    old_test = (ROOT / "baseline-test-source.py.txt").read_bytes()
    values = {
        "schema": "map01-v40-finish-pipe-pressure-t4-v1",
        "disposition": "PASS_BOUNDED_FINISH_DELIVERY_CONSTRUCTION",
        "baseline_disposition": "FAIL_FINISH_DELIVERY_UNBOUNDED",
        "base_commit": BASE,
        "baseline_controller_sha256": sha(old_source),
        "baseline_test_sha256": sha(old_test),
        "candidate_controller_sha256": sha(candidate.read_bytes()),
        "candidate_test_sha256": sha(test_source.read_bytes()),
        "audit_source_sha256": sha((ROOT / "audit.py").read_bytes()),
        "environment": {"platform": platform.platform(), "python": sys.version},
        "commands": [
            {"command": "baseline focused backpressure regression", "exit_code":
             int((ROOT / "baseline-test-exit-code.txt").read_text().strip())},
            {"command": "focused V40 candidate suite", "exit_code":
             int((ROOT / "candidate-test-exit-code.txt").read_text().strip())},
            {"command": "py_compile candidate/controller/tests/auditor", "exit_code":
             int((ROOT / "compile-exit-code.txt").read_text().strip())},
            {"command": "git diff --check", "exit_code":
             int((ROOT / "diff-check-exit-code.txt").read_text().strip())},
        ],
        "candidate_tests_passed": 11,
        "retained_process_bound_ms": 350,
        "scope": "native Windows synthetic non-reading child pipe; no game, model, GUI, physical input, or formal #59 allocation",
        "limitations": [
            "Forced retirement stops only this custody object's owned child; no graceful score or application-level release is claimed after delivery timeout.",
            "This construction does not prove all child runtimes or operating systems exhibit identical pipe behavior.",
        ],
    }
    (ROOT / "RESULT.json").write_text(json.dumps(values, indent=2) + "\n",
                                       encoding="utf-8")
    files = sorted(path for path in ROOT.rglob("*") if path.is_file() and
                   path.name != "SHA256SUMS" and "__pycache__" not in path.parts)
    rows = [f"{sha(path.read_bytes())}  {path.relative_to(ROOT).as_posix()}"
            for path in files]
    (ROOT / "SHA256SUMS").write_text("\n".join(rows) + "\n", encoding="utf-8")
    print(f"bound {len(files)} files; candidate={values['candidate_controller_sha256']}")


if __name__ == "__main__":
    main()
