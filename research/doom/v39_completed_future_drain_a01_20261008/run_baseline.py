#!/usr/bin/env python3
"""Replay the regression against the immutable controller blob at base main."""

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = "6ea1269defb6d48a607f13b08f1aa2d223ba06e9"
CONTROLLER = "research/doom/map01_overlap_controller_v39.py"
TEST = "research/doom/test_map01_completed_future_drain_v1.py"


def main():
    output = HERE / "results/baseline-01"
    output.mkdir(parents=True, exist_ok=False)
    repo = Path(subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"], cwd=HERE, text=True).strip())
    source_dir = output / "source"
    source_dir.mkdir()
    source = subprocess.check_output(["git", "show", f"{BASE}:{CONTROLLER}"], cwd=repo)
    test = (repo / TEST).read_bytes()
    (source_dir / "map01_overlap_controller_v39.py").write_bytes(source)
    (source_dir / "test_map01_completed_future_drain_v1.py").write_bytes(test)
    env = os.environ.copy()
    paths = [str(repo / "research/doom"), str(repo / "research/live_control")]
    env["PYTHONPATH"] = os.pathsep.join(paths + ([env["PYTHONPATH"]] if env.get("PYTHONPATH") else []))
    command = [sys.executable, "-B", "-m", "unittest", "discover", "-s", str(source_dir),
               "-p", "test_map01_completed_future_drain_v1.py", "-v"]
    result = subprocess.run(command, cwd=repo, env=env, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (output / "baseline_failure.txt").write_text(result.stdout, encoding="utf-8", newline="\n")
    expected = result.returncode == 1 and "FAILED (failures=1, errors=1)" in result.stdout
    report = {
        "schema": "v39_completed_future_drain_baseline_v1",
        "base_commit": BASE,
        "controller_blob": subprocess.check_output(
            ["git", "rev-parse", f"{BASE}:{CONTROLLER}"], cwd=repo, text=True).strip(),
        "controller_sha256": hashlib.sha256(source).hexdigest(),
        "regression_test_sha256": hashlib.sha256(test).hexdigest(),
        "command": command,
        "exit_code": result.returncode,
        "expected_failure_reproduced": expected,
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n",
                                        encoding="utf-8", newline="\n")
    print(json.dumps(report, indent=2))
    return 0 if expected else 1


if __name__ == "__main__":
    raise SystemExit(main())
