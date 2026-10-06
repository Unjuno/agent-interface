#!/usr/bin/env python3
"""Run the frozen four-suite source-overlay verification and retain transcripts."""
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parent
SNAPSHOT = ROOT / "source_snapshot"
RESULTS = ROOT / "results"
TESTS = [
    "test_map01_overlap_controller_v39.py",
    "test_overlap_controller_v39_wait.py",
    "test_source_refresh_v1.py",
    "test_v39_soft_stale_renewal_v1.py",
]


def main():
    freeze = json.loads((ROOT / "FREEZE.json").read_text())
    RESULTS.mkdir(exist_ok=True)
    python = sys.executable
    invocation = {
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "candidate_commit": freeze["candidate_commit"],
        "python": python,
        "python_version": subprocess.check_output([python, "--version"], text=True).strip(),
        "tests": TESTS,
        "expected_tests_per_mode": freeze["expected_tests_per_mode"],
        "results": {},
    }
    with tempfile.TemporaryDirectory(prefix="v39-renewal-overlay-") as temp:
        workspace = Path(temp)
        shutil.copytree(SNAPSHOT, workspace, dirs_exist_ok=True)
        doom = workspace / "research" / "doom"
        for label, flags in [("normal", []), ("optimized", ["-O"])]:
            command = [python, "-B", *flags, "-m", "unittest", *TESTS]
            start = time.monotonic_ns()
            result = subprocess.run(
                command, cwd=doom, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, text=True, check=False,
            )
            (RESULTS / f"{label}.txt").write_text(result.stdout)
            invocation["results"][label] = {
                "argv": command,
                "exit_code": result.returncode,
                "elapsed_ns": time.monotonic_ns() - start,
            }
        command = [python, "-B", "-m", "py_compile", *TESTS,
                   "map01_overlap_controller_v39.py"]
        result = subprocess.run(
            command, cwd=doom, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, check=False,
        )
        (RESULTS / "compile.txt").write_text(result.stdout)
        invocation["results"]["compile"] = {
            "argv": command, "exit_code": result.returncode,
        }
    invocation["ended_at_utc"] = datetime.now(timezone.utc).isoformat()
    (RESULTS / "invocation.json").write_text(json.dumps(invocation, indent=2) + "\n")
    print(json.dumps(invocation["results"], indent=2))
    return 0 if all(
        row["exit_code"] == 0 for row in invocation["results"].values()
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
