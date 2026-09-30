#!/usr/bin/env python3
"""One-shot construction launcher with logs outside the runner's output mount.

No model fitting happens here. This launcher verifies directory ownership and
emptiness before invoking the excluded-seed construction entrypoint.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run(source, output, logs, python=sys.executable):
    source = Path(source).resolve()
    output = Path(output).resolve()
    logs = Path(logs).resolve()
    if source == output or source == logs or output == logs:
        return {"status": "STOP_LAUNCH_PATH_ALIAS", "returncode": None}
    if not source.is_dir() or not (source / "construction.py").is_file():
        return {"status": "STOP_SOURCE_MISSING", "returncode": None}
    if not output.is_dir() or any(output.iterdir()):
        return {"status": "STOP_OUTPUT_NOT_EMPTY", "returncode": None}
    logs.mkdir(parents=True, exist_ok=True)
    if any(logs.iterdir()):
        return {"status": "STOP_LOG_DIR_NOT_EMPTY", "returncode": None}

    env = os.environ.copy()
    env["NEEDLE_CONSTRUCTION_OUTPUT"] = str(output)
    env.pop("NEEDLE_OUTPUT", None)
    env.pop("NEEDLE_SEEDS", None)
    command = [python, "-B", str(source / "construction.py"), "--seed", "9944014"]
    completed = subprocess.run(command, cwd=source, env=env, text=True,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               check=False)
    stdout_path, stderr_path = logs / "stdout.txt", logs / "stderr.txt"
    stdout_path.write_text(completed.stdout, encoding="utf-8")
    stderr_path.write_text(completed.stderr, encoding="utf-8")
    receipt = {"status": "CONSTRUCTION_EXIT_0" if completed.returncode == 0
               else "STOP_CONSTRUCTION_NONZERO",
               "returncode": completed.returncode, "command": command,
               "output_dir": str(output), "logs_dir": str(logs),
               "raw_files": sorted(p.name for p in output.iterdir()),
               "stdout_sha256": sha256(stdout_path), "stderr_sha256": sha256(stderr_path)}
    (logs / "launcher_receipt.json").write_text(
        json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return receipt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--logs", required=True)
    args = parser.parse_args()
    receipt = run(args.source, args.output, args.logs)
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["status"] == "CONSTRUCTION_EXIT_0" else 2


if __name__ == "__main__":
    raise SystemExit(main())
