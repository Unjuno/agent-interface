#!/usr/bin/env python3
"""Run and retain the focused V39 completed-future drain regression set."""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
TESTS = (
    "test_map01_completed_future_drain_v1.py",
    "test_map01_overlap_controller_v39_dual_signal.py",
    "test_map01_overlap_controller_v39.py",
    "test_map01_overlap_controller_v39_pair_duplicate_consistency.py",
    "test_overlap_controller_v39_wait.py",
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=False)
    rows = []
    for mode in ("normal", "optimized"):
        for test in TESTS:
            command = [sys.executable]
            if mode == "optimized":
                command.append("-O")
            command.extend(("-m", "unittest", "discover", "-s", "research/doom",
                            "-p", test, "-v"))
            started = time.perf_counter()
            result = subprocess.run(command, cwd=ROOT, text=True,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            elapsed = time.perf_counter() - started
            name = f"{mode}-{test.removesuffix('.py')}.txt"
            (output / name).write_text(result.stdout, encoding="utf-8", newline="\n")
            rows.append({"mode": mode, "test": test, "command": command,
                         "exit_code": result.returncode,
                         "elapsed_seconds": round(elapsed, 6), "output_file": name})
    report = {"schema": "v39_completed_future_drain_checks_v1",
              "base_commit": "6ea1269defb6d48a607f13b08f1aa2d223ba06e9",
              "python": sys.version, "platform": sys.platform,
              "results": rows,
              "all_passed": all(row["exit_code"] == 0 for row in rows)}
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n",
                                         encoding="utf-8", newline="\n")
    print(json.dumps(report, indent=2))
    return 0 if report["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
