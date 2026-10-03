"""Retain actual commands, UTC times, output bytes and subprocess exits."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

P = Path(__file__).parent
ROOT = P.parents[2]


def execute(label, args, output):
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    result = subprocess.run(args, cwd=ROOT, capture_output=True,
                            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    (P / output).write_bytes(result.stdout)
    (P / (label + ".stderr.txt")).write_bytes(result.stderr)
    receipt = {"label": label, "command": ["python3" if arg == sys.executable else arg for arg in args],
               "cwd": "repository root", "utc_start": started,
               "utc_end": datetime.datetime.now(datetime.timezone.utc).isoformat(),
               "exit_code": result.returncode, "stdout": output, "stderr": label + ".stderr.txt",
               "stdout_sha256": hashlib.sha256(result.stdout).hexdigest(),
               "stderr_sha256": hashlib.sha256(result.stderr).hexdigest()}
    (P / (label + ".receipt.json")).write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(label, "exit", result.returncode)
    return result.returncode


def main():
    relative = P.relative_to(ROOT).as_posix()
    freeze = json.loads((P / "FREEZE.json").read_text())
    for name, digest in freeze["files"].items():
        if hashlib.sha256((P / name).read_bytes()).hexdigest() != digest:
            raise ValueError("freeze source changed: " + name)
    for label, source in freeze["sources"].items():
        if hashlib.sha256((P / "sources" / (label + ".py")).read_bytes()).hexdigest() != source["sha256"]:
            raise ValueError("retained source changed: " + label)
    if any((P / name).exists() for name in ("raw.jsonl", "audit.json", "controls.json")):
        raise ValueError("original output exists; do not overwrite or retry")
    if execute("candidate", [sys.executable, relative + "/candidate.py"], "raw.jsonl"):
        return 1
    if execute("audit", [sys.executable, relative + "/audit.py", relative + "/raw.jsonl"], "audit.json"):
        return 1
    if execute("controls", [sys.executable, relative + "/check_controls.py", relative + "/raw.jsonl"], "controls.json"):
        return 1
    return execute("compiled_regression", [sys.executable, "-m", "unittest", "-v", "runtime.core_v1.test_compiled_gui"], "compiled_regression.stdout.txt")


if __name__ == "__main__":
    raise SystemExit(main())
