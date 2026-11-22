#!/usr/bin/env python3
"""Single-use formal driver. An exclusive marker prevents candidate re-invocation."""
import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, data):
    path.write_text(json.dumps(data, sort_keys=True, indent=2) + "\n")


def main():
    started_path = HERE / "formal_started.json"
    fd = os.open(started_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o444)
    with os.fdopen(fd, "w") as stream:
        json.dump({"driver_invocations": 1, "started_utc": datetime.now(timezone.utc).isoformat(),
                   "pid": os.getpid(), "candidate_invocations": 0, "auditor_invocations": 0}, stream, sort_keys=True)
        stream.write("\n"); stream.flush(); os.fsync(stream.fileno())

    freeze = json.loads((HERE / "FROZEN.json").read_text())
    for name, expected in freeze["source_sha256"].items():
        if digest(HERE / name) != expected:
            write(HERE / "terminal.json", {"disposition": "STOP_FROZEN_HASH_MISMATCH", "file": name,
                                           "candidate_invocations": 0, "auditor_invocations": 0})
            return 2
    if digest(HERE / "audit.py") != freeze["auditor_sha256"]:
        write(HERE / "terminal.json", {"disposition": "STOP_AUDITOR_HASH_MISMATCH",
                                       "candidate_invocations": 0, "auditor_invocations": 0})
        return 2

    command = [sys.executable, "-B", "candidate.py", "--input", "public_input.json", "--output", "formal_output.json"]
    candidate = subprocess.run(command, cwd=HERE, text=True, capture_output=True, check=False)
    (HERE / "candidate.stdout.txt").write_text(candidate.stdout)
    (HERE / "candidate.stderr.txt").write_text(candidate.stderr)
    counts = {"candidate_invocations": 1, "auditor_invocations": 0, "driver_invocations": 1}
    if candidate.returncode != 0:
        terminal = {**counts, "disposition": "STOP_CANDIDATE_NONZERO", "candidate_exit": candidate.returncode,
                    "candidate_command": command, "candidate_stdout_sha256": digest(HERE / "candidate.stdout.txt"),
                    "candidate_stderr_sha256": digest(HERE / "candidate.stderr.txt"), "retries": 0}
        write(HERE / "terminal.json", terminal)
        return candidate.returncode

    audit_command = [sys.executable, "-B", "audit.py"]
    audited = subprocess.run(audit_command, cwd=HERE, text=True, capture_output=True, check=False)
    (HERE / "audit.stdout.txt").write_text(audited.stdout)
    (HERE / "audit.stderr.txt").write_text(audited.stderr)
    counts["auditor_invocations"] = 1
    terminal = {**counts, "candidate_exit": candidate.returncode, "auditor_exit": audited.returncode,
                "candidate_command": command, "auditor_command": audit_command, "retries": 0,
                "disposition": "PASS_METHOD_AND_HYPOTHESIS_SCOPED" if audited.returncode == 0 else "FAIL_OR_STOP_AUDIT",
                "candidate_output_sha256": digest(HERE / "formal_output.json"),
                "candidate_stdout_sha256": digest(HERE / "candidate.stdout.txt"),
                "candidate_stderr_sha256": digest(HERE / "candidate.stderr.txt"),
                "audit_output_sha256": digest(HERE / "audit.json") if (HERE / "audit.json").exists() else None,
                "audit_stdout_sha256": digest(HERE / "audit.stdout.txt"),
                "audit_stderr_sha256": digest(HERE / "audit.stderr.txt"),
                "environment": {"python": sys.version.split()[0], "platform": platform.platform(),
                                "machine": platform.machine(), "network": False, "runtime": "native CPU"}}
    write(HERE / "terminal.json", terminal)
    return audited.returncode


if __name__ == "__main__":
    sys.exit(main())
