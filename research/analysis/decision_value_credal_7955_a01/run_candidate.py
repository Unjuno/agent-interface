#!/usr/bin/env python3
"""Verify the freeze, launch the candidate once, and retain exact stdout."""
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
FREEZE = json.loads((HERE / "FROZEN.json").read_text())
if (HERE / "terminal.json").exists() or (HERE / "result.json").exists():
    raise SystemExit("refusing repeat or overwrite; preserve first outcome")
for name, expected in FREEZE["source_sha256"].items():
    actual = hashlib.sha256((HERE / name).read_bytes()).hexdigest()
    if actual != expected:
        raise SystemExit(f"frozen source mismatch: {name}")
if sys.platform != FREEZE["environment"]["platform"] or platform.machine() != FREEZE["environment"]["machine"]:
    raise SystemExit("frozen execution platform mismatch")
if platform.python_version() != FREEZE["environment"]["python"]:
    raise SystemExit("frozen Python version mismatch")

proc = subprocess.run([sys.executable, "-B", "candidate.py"], cwd=HERE,
                      stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                      check=False, timeout=60)
(HERE / "result.json").write_bytes(proc.stdout)
(HERE / "candidate.stderr.txt").write_bytes(proc.stderr)
terminal = {
    "run_id": FREEZE["run_id"],
    "frozen_source_verified": True,
    "launch_count": 1,
    "retry_count": 0,
    "exit_code": proc.returncode,
    "stdout_bytes": len(proc.stdout),
    "stdout_sha256": hashlib.sha256(proc.stdout).hexdigest(),
    "stderr_bytes": len(proc.stderr),
    "stderr_sha256": hashlib.sha256(proc.stderr).hexdigest(),
    "python": platform.python_version(),
    "platform": sys.platform,
    "machine": platform.machine(),
}
(HERE / "terminal.json").write_text(json.dumps(terminal, sort_keys=True, indent=2) + "\n")
print(json.dumps(terminal, sort_keys=True))
raise SystemExit(proc.returncode)
