#!/usr/bin/env python3
"""Replay the frozen V12 release-error regression closure in disposable overlays."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parent
SNAPSHOT = ROOT / "source_snapshot"
BASELINE = ROOT / "baseline_source"
RESULTS = ROOT / "results"
BASELINE_TEST = (
    "test_input_owner_v12_explicit_up_cancel."
    "ExplicitKeyUpCancellationTests.test_keyrelease_send_failure_retains_receipt_and_retries"
)
SUITES = [
    "test_input_owner_v12_explicit_up_cancel",
    "test_input_transition_owner_v3",
    "test_input_transition_owner_v3_owner_queue",
    "test_input_transition_owner_v4",
]
PYCOMPILE = [
    "input_owner_v12.py",
    "input_transition_owner_v3.py",
    "input_transition_owner_v4.py",
    "test_input_owner_v12_explicit_up_cancel.py",
    "test_input_transition_owner_v3.py",
    "test_input_transition_owner_v3_owner_queue.py",
    "test_input_transition_owner_v4.py",
]


def invoke(label, source_root, modules):
    live = source_root / "research" / "live_control"
    command = [sys.executable, "-B", "-m", "unittest", "-v", *modules]
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(live)
    started = datetime.now(timezone.utc).isoformat()
    begin = time.monotonic_ns()
    result = subprocess.run(command, cwd=live, env=environment,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, check=False)
    elapsed = time.monotonic_ns() - begin
    (RESULTS / f"{label}.txt").write_text(result.stdout, encoding="utf-8")
    return {
        "argv": command,
        "cwd": str(live),
        "started_at_utc": started,
        "exit_code": result.returncode,
        "elapsed_ns": elapsed,
    }


def main():
    freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
    RESULTS.mkdir(exist_ok=True)
    invocation = {
        "schema": "v39-terminal-release-errors-a02-invocation-v1",
        "candidate_commit": freeze["candidate_commit"],
        "baseline_main_sha": freeze["baseline_main_sha"],
        "python": sys.executable,
        "python_version": subprocess.check_output(
            [sys.executable, "--version"], text=True).strip(),
        "runs": {},
    }
    with tempfile.TemporaryDirectory(prefix="v39-release-errors-a02-baseline-") as temp:
        baseline_root = Path(temp)
        shutil.copytree(SNAPSHOT, baseline_root, dirs_exist_ok=True)
        baseline_owner = baseline_root / "research" / "live_control" / "input_owner_v12.py"
        baseline_owner.write_bytes((BASELINE / "research" / "live_control" /
                                    "input_owner_v12.py").read_bytes())
        invocation["runs"]["baseline"] = invoke("baseline", baseline_root,
                                                 [BASELINE_TEST])

    with tempfile.TemporaryDirectory(prefix="v39-release-errors-a02-candidate-") as temp:
        candidate_root = Path(temp)
        shutil.copytree(SNAPSHOT, candidate_root, dirs_exist_ok=True)
        invocation["runs"]["candidate"] = invoke("candidate", candidate_root, SUITES)
        live = candidate_root / "research" / "live_control"
        command = [sys.executable, "-B", "-m", "py_compile", *PYCOMPILE]
        result = subprocess.run(command, cwd=live, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True, check=False)
        (RESULTS / "compile.txt").write_text(result.stdout, encoding="utf-8")
        invocation["runs"]["compile"] = {"argv": command, "cwd": str(live),
                                           "exit_code": result.returncode}
    invocation["ended_at_utc"] = datetime.now(timezone.utc).isoformat()
    (RESULTS / "invocation.json").write_text(
        json.dumps(invocation, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(invocation["runs"], indent=2))
    return 0 if invocation["runs"]["baseline"]["exit_code"] == 1 and \
        invocation["runs"]["candidate"]["exit_code"] == 0 and \
        invocation["runs"]["compile"]["exit_code"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
