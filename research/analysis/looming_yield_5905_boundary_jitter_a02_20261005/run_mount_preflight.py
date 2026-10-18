#!/usr/bin/env python3
"""Non-candidate image and RO bind-mount smoke test."""
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
IMAGE = "python@sha256:c3e521df8b2b498a7a682e7e18676771cb80c6b75b8699af886b2d554ce40151"
SOURCE = ROOT.parents[0] / "looming_yield_5905_image_only_t0_9_a09_20261005/candidate.py"


def main():
    cmd = ["docker", "run", "--pull=never", "--rm", "--network=none", "--read-only",
           "--tmpfs", "/tmp:rw,noexec,nosuid,size=16m", "--cap-drop=ALL",
           "--security-opt=no-new-privileges", "--cpus=1", "--memory=1g",
           "--mount", f"type=bind,src={SOURCE},dst=/src/candidate.py,readonly",
           IMAGE, "python", "-B", "-c",
           "from pathlib import Path; print('source_bytes='+str(Path('/src/candidate.py').stat().st_size))"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    (ROOT/"preflight.stdout.txt").write_text(result.stdout)
    (ROOT/"preflight.stderr.txt").write_text(result.stderr)
    record = {"kind": "CONTAINER_MOUNT_PREFLIGHT_NOT_EXPERIMENT", "command": cmd,
              "exit": result.returncode, "stdout": result.stdout, "stderr": result.stderr,
              "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
              "candidate_invocations": 0, "auditor_invocations": 0,
              "timestamp_utc": datetime.now(timezone.utc).isoformat()}
    (ROOT/"PREFLIGHT.json").write_text(json.dumps(record, sort_keys=True, indent=2)+"\n")
    print(json.dumps({"exit": result.returncode, "stdout": result.stdout.strip(),
                      "stderr": result.stderr.strip()}))
    if result.returncode:
        raise SystemExit("STOP_CONTAINER_PREFLIGHT")


if __name__ == "__main__":
    main()
