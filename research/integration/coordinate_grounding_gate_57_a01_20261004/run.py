"""Reproduce A01 probe and construction tests from the repository root."""
from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
from pathlib import Path

from .probe import run_probe


PACKAGE = Path(__file__).resolve().parent
REPO = PACKAGE.parents[2]
OUT = PACKAGE / "out"
MODULE = "research.integration.coordinate_grounding_gate_57_a01_20261004"


def execute(label, argv):
    result = subprocess.run(argv, cwd=REPO, capture_output=True, text=True)
    (OUT / f"{label}.stdout.txt").write_text(result.stdout, encoding="utf-8", newline="\n")
    (OUT / f"{label}.stderr.txt").write_text(result.stderr, encoding="utf-8", newline="\n")
    return {"argv": argv, "exit_code": result.returncode,
            "stdout": result.stdout, "stderr": result.stderr}


def main():
    OUT.mkdir(exist_ok=True)
    result = run_probe()
    (PACKAGE / "PROBE.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    tests = execute("tests", [sys.executable, "-m", "unittest", f"{MODULE}.test_coordinate_grounding", "-v"])
    adjacent = execute("adjacent_compiled_suite", [sys.executable, "-m", "unittest",
                                                  "runtime.guarded_x11_v1.test_compiled", "-v"])
    pycompile = execute("pycompile", [sys.executable, "-m", "py_compile",
                                      str(PACKAGE / "probe.py"),
                                      str(PACKAGE / "test_coordinate_grounding.py"),
                                      str(PACKAGE / "audit.py"), str(PACKAGE / "run.py"),
                                      str(PACKAGE / "freeze.py"), str(PACKAGE / "inventory.py")])
    runs = {
        "schema": "coordinate-grounding-a01-runs-v1",
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO,
                                                  text=True).strip(),
        "environment": {"python": sys.version, "platform": platform.platform(),
                        "pillow": __import__("PIL").__version__, "network": "not used",
                        "model_gui_os_input": False},
        "probe": {"argv": [sys.executable, "-m", f"{MODULE}.run"],
                  "exit_code": 0, "result_path": "PROBE.json"},
        "tests": {"argv": tests["argv"], "exit_code": tests["exit_code"],
                  "stdout_path": "out/tests.stdout.txt", "stderr_path": "out/tests.stderr.txt"},
        "adjacent_compiled_suite": {
            "argv": adjacent["argv"], "exit_code": adjacent["exit_code"],
            "classification": ("PASS" if adjacent["exit_code"] == 0 else
                               "STOP_MISSING_PYTHON_XLIB"),
            "stdout_path": "out/adjacent_compiled_suite.stdout.txt",
            "stderr_path": "out/adjacent_compiled_suite.stderr.txt"},
        "pycompile": {"argv": pycompile["argv"], "exit_code": pycompile["exit_code"],
                      "stdout_path": "out/pycompile.stdout.txt",
                      "stderr_path": "out/pycompile.stderr.txt"},
    }
    (PACKAGE / "RUNS.json").write_text(
        json.dumps(runs, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"tests_exit": tests["exit_code"],
                      "adjacent_suite_exit": adjacent["exit_code"],
                      "pycompile_exit": pycompile["exit_code"],
                      "probe_cases": len(result["case_results"]),
                      "input_dispatch_count": result["input_dispatch_count"]}, sort_keys=True))
    return tests["exit_code"] or pycompile["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
