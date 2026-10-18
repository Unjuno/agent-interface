#!/usr/bin/env python3
"""Run baseline/candidate stuck-planner cleanup injection and focused tests."""
import hashlib
import json
import platform
import subprocess
import sys
import tempfile
import time
from pathlib import Path


HERE = Path(__file__).resolve().parent
DOOM = HERE.parents[1]
REPO = DOOM.parents[1]
BASE = "2559e5e6682fc6833aa4178a206ba0603e538dc0"
RELATIVE_HELPER = "research/doom/doom_controller_failure_cleanup_v1.py"
FAULT = r'''
import json, sys
from pathlib import Path
from doom_controller_failure_cleanup_v1 import ControllerFailureCleanup
class StuckPlanner:
    def close(self, timeout=1):
        import threading
        threading.Event().wait()
out = Path(sys.argv[2])
error = ValueError("injected primary")
try:
    with ControllerFailureCleanup(StuckPlanner(), out):
        raise error
except ValueError as caught:
    receipt_path = out / "controller-failure.json"
    receipt = json.loads(receipt_path.read_text())
    stage = next(row for row in receipt["stages"]
                 if row["stage"] == "planner_close")
    print(json.dumps({
        "primary_type": type(caught).__name__,
        "primary_message": str(caught),
        "primary_identity_preserved": caught is error,
        "receipt_written": receipt_path.is_file(),
        "planner_close_status": stage["status"],
        "cleanup_complete": receipt["cleanup_complete"],
    }, sort_keys=True))
'''


def run_case(module_dir, timeout):
    with tempfile.TemporaryDirectory() as out:
        start = time.monotonic()
        try:
            completed = subprocess.run(
                [sys.executable, "-c", FAULT, str(module_dir), out],
                cwd=module_dir, capture_output=True, text=True, timeout=timeout,
                check=False)
            elapsed = time.monotonic() - start
            try:
                observed = json.loads(completed.stdout.strip().splitlines()[-1])
            except (ValueError, IndexError):
                observed = None
            return {
                "outcome": "completed" if completed.returncode == 0 else "nonzero_exit",
                "returncode": completed.returncode,
                "elapsed_seconds": round(elapsed, 3),
                "stdout": completed.stdout,
                "stderr": completed.stderr,
                "receipt_exists_after_process": (Path(out) / "controller-failure.json").is_file(),
                "observed": observed,
            }
        except subprocess.TimeoutExpired as exc:
            return {
                "outcome": "watchdog_timeout",
                "elapsed_seconds": round(time.monotonic() - start, 3),
                "stdout": (exc.stdout or b"").decode(errors="replace"),
                "stderr": (exc.stderr or b"").decode(errors="replace"),
                "receipt_exists_after_process": (Path(out) / "controller-failure.json").is_file(),
                "observed": None,
            }


def main():
    original = subprocess.run(
        ["git", "show", f"{BASE}:{RELATIVE_HELPER}"], cwd=REPO,
        capture_output=True, text=True, check=True).stdout
    with tempfile.TemporaryDirectory() as baseline_dir:
        baseline_path = Path(baseline_dir) / "doom_controller_failure_cleanup_v1.py"
        baseline_path.write_text(original, encoding="utf-8")
        baseline = run_case(Path(baseline_dir), 0.75)
    candidate = run_case(DOOM, 2.5)
    helper = DOOM / "doom_controller_failure_cleanup_v1.py"
    tests = subprocess.run(
        [sys.executable, "-m", "unittest", "-v",
         "test_controller_failure_cleanup_v1",
         "test_controller_failure_cleanup_portability_v1",
         "test_controller_failure_cleanup_stage_v1",
         "test_overlap_controller_v39_wait", "test_source_refresh_v1"],
        cwd=DOOM, capture_output=True, text=True, check=False)
    (HERE / "TEST_OUTPUT.txt").write_text(
        tests.stdout + tests.stderr, encoding="utf-8")
    raw = {
        "experiment": "issue59-planner-close-deadline-followup-20261004",
        "source_parent_commit": BASE,
        "host": platform.platform(),
        "python": sys.version,
        "helper_sha256": hashlib.sha256(helper.read_bytes()).hexdigest(),
        "command": "python3 -m unittest -v test_controller_failure_cleanup_v1 test_controller_failure_cleanup_portability_v1 test_controller_failure_cleanup_stage_v1 test_overlap_controller_v39_wait test_source_refresh_v1",
        "baseline_watchdog_seconds": 0.75,
        "candidate_watchdog_seconds": 2.5,
        "planner_timeout_seconds": 1,
        "baseline": baseline,
        "candidate": candidate,
        "focused_tests": {
            "returncode": tests.returncode,
            "passed": "OK" in tests.stderr.splitlines()[-1:] if tests.stderr else False,
            "output_file": "TEST_OUTPUT.txt",
        },
    }
    (HERE / "RAW.json").write_text(json.dumps(raw, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "baseline": baseline["outcome"],
        "candidate": candidate["observed"],
        "candidate_elapsed_seconds": candidate["elapsed_seconds"],
        "focused_tests_returncode": tests.returncode,
    }, sort_keys=True))
    return tests.returncode


if __name__ == "__main__":
    raise SystemExit(main())
