#!/usr/bin/env python3
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
IMAGE = "python@sha256:c3e521df8b2b498a7a682e7e18676771cb80c6b75b8699af886b2d554ce40151"


def main():
    cmd = ["docker", "run", "--pull=never", "--rm", "--network=none", "--read-only", "--tmpfs", "/tmp:rw,noexec,nosuid,size=16m", "--cap-drop=ALL", "--security-opt=no-new-privileges", "--cpus=1", "--memory=1g", "--mount", f"type=bind,src={ROOT/'candidate.py'},dst=/src/candidate.py,readonly", IMAGE, "python", "-B", "-c", "from pathlib import Path; print('bytes='+str(Path('/src/candidate.py').stat().st_size))"]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    rec = {"kind": "CONTAINER_PREFLIGHT_NOT_EXPERIMENT", "command": cmd, "exit": p.returncode, "stdout": p.stdout, "stderr": p.stderr, "candidate_sha256": hashlib.sha256((ROOT/"candidate.py").read_bytes()).hexdigest(), "candidate_invocations": 0, "auditor_invocations": 0, "timestamp_utc": datetime.now(timezone.utc).isoformat()}
    (ROOT/"preflight.stdout.txt").write_text(p.stdout)
    (ROOT/"preflight.stderr.txt").write_text(p.stderr)
    (ROOT/"PREFLIGHT.json").write_text(json.dumps(rec, sort_keys=True, indent=2)+"\n")
    print(json.dumps({"exit": p.returncode, "stdout": p.stdout.strip(), "stderr": p.stderr.strip()}))
    if p.returncode:
        raise SystemExit("STOP_CONTAINER_PREFLIGHT")


if __name__ == "__main__":
    main()
