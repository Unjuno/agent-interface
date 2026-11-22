#!/usr/bin/env python3
"""One-shot runner. An O_EXCL marker permanently consumes this formal invocation."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT, OUT = Path("/src"), Path("/out")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    marker = OUT / "formal_started.json"
    payload = {"allocation": "UNJUNO-8049-IPCW-REPEATED-UNCERTAINTY-A01-ORBSTACK-20261005",
               "started_unix_ns": time.time_ns(), "driver_pid": os.getpid()}
    fd = os.open(marker, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as stream:
        json.dump(payload, stream, sort_keys=True)
        stream.write("\n")

    frozen = json.loads((ROOT / "FROZEN.json").read_text())
    mismatches = [name for name, expected in frozen["files"].items()
                  if sha(ROOT / name) != expected]
    if mismatches:
        (OUT / "formal_terminal.json").write_text(json.dumps({"status": "STOP_SOURCE_HASH_MISMATCH",
            "mismatches": mismatches, "formal_candidate_invocations": 0, "formal_auditor_invocations": 0}, indent=2) + "\n")
        return 2

    candidate_out = OUT / "candidate_output.json"
    commands = [
        [sys.executable, "-B", str(ROOT / "candidate.py"), "--input", str(ROOT / "public_input.json"), "--output", str(candidate_out)],
        [sys.executable, "-B", str(ROOT / "auditor.py"), "--public", str(ROOT / "public_input.json"),
         "--oracle", str(ROOT / "oracle_input.json"), "--candidate", str(candidate_out), "--output", str(OUT / "audit.json")],
    ]
    runs = []
    for label, command in zip(("candidate", "auditor"), commands):
        proc = subprocess.run(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        (OUT / f"{label}.stdout.txt").write_bytes(proc.stdout)
        (OUT / f"{label}.stderr.txt").write_bytes(proc.stderr)
        runs.append({"role": label, "argv": command, "exit_code": proc.returncode,
                     "stdout_sha256": sha(OUT / f"{label}.stdout.txt"),
                     "stderr_sha256": sha(OUT / f"{label}.stderr.txt")})
    terminal = {"allocation": payload["allocation"], "status": "COMPLETED",
                "formal_candidate_invocations": 1, "formal_auditor_invocations": 1,
                "retries": 0, "runs": runs,
                "frozen_manifest_sha256": sha(ROOT / "FROZEN.json"),
                "candidate_output_sha256": sha(candidate_out) if candidate_out.exists() else None,
                "audit_sha256": sha(OUT / "audit.json") if (OUT / "audit.json").exists() else None}
    (OUT / "formal_terminal.json").write_text(json.dumps(terminal, sort_keys=True, indent=2) + "\n")
    return 0 if all(run["exit_code"] == 0 for run in runs) else 1


if __name__ == "__main__":
    raise SystemExit(main())
