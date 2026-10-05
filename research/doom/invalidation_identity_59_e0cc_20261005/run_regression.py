"""Retain source-bound regressions; each output label is write-once."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

PACKAGE = Path(__file__).resolve().parent
ROOT = PACKAGE.parents[2]
FOCUSED = ["research.live_control.test_observable_signal_guard_v2",
           "research.doom.test_map01_overlap_controller_v39"]
ADJACENT = ["research.doom.test_overlap_controller_v39_wait",
            "research.doom.test_controller_failure_cleanup_v1",
            "research.doom.test_map01_overlap_controller_v39_dual_signal",
            "research.doom.test_map01_overlap_controller_v39_pair_duplicate_consistency",
            "research.doom.test_map01_v39_pair_wait_dispatch"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True)
    parser.add_argument("--adjacent", action="store_true")
    parser.add_argument("--optimized", action="store_true")
    args = parser.parse_args()
    if not args.label.replace("-", "").isalnum():
        parser.error("simple output label required")
    output = PACKAGE / args.label
    output.mkdir()
    manifest = json.loads((PACKAGE / "baseline-source-manifest.json").read_text())
    sources = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
               for p in manifest["files"]}
    command = [sys.executable, "-B"] + (["-O"] if args.optimized else [])
    command += ["-m", "unittest", "-v", *(ADJACENT if args.adjacent else FOCUSED)]
    environment = dict(os.environ)
    environment["PYTHONPATH"] = os.pathsep.join(
        str(ROOT / path) for path in ("research/doom", "research/live_control"))
    start = time.time_ns()
    result = subprocess.run(command, cwd=ROOT, env=environment, capture_output=True)
    end = time.time_ns()
    (output / "stdout.log").write_bytes(result.stdout)
    (output / "stderr.log").write_bytes(result.stderr)
    unchanged = all(hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == h
                    for p, h in sources.items())
    receipt = {"command": ["python", *command[1:]], "cwd": "repository root",
               "PYTHONPATH": ["research/doom", "research/live_control"],
               "python": platform.python_version(), "platform": platform.platform(),
               "started_unix_ns": start, "finished_unix_ns": end,
               "exit_code": result.returncode, "sources_unchanged": unchanged,
               "source_sha256": sources,
               "stdout_sha256": hashlib.sha256(result.stdout).hexdigest(),
               "stderr_sha256": hashlib.sha256(result.stderr).hexdigest()}
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"label": args.label, "exit_code": result.returncode,
                      "sources_unchanged": unchanged}))
    print(result.stderr.decode())
    return result.returncode if unchanged else 99


if __name__ == "__main__":
    raise SystemExit(main())
