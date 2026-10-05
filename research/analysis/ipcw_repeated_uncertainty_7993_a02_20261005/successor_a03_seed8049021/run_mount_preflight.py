#!/usr/bin/env python3
"""Exercise pinned-image read-only source and default read-write output mounts."""
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
IMAGE = "python@sha256:c3e521df8b2b498a7a682e7e18676771cb80c6b75b8699af886b2d554ce40151"


def main():
    output = ROOT / "preflight-output"
    output.mkdir(exist_ok=True)
    source = ROOT / "PROTOCOL.md"
    command = ["docker", "run", "--pull=never", "--rm", "--network=none", "--read-only",
               "--tmpfs", "/tmp:rw,noexec,nosuid,size=16m", "--cap-drop=ALL",
               "--security-opt=no-new-privileges", "--cpus=1", "--memory=1g",
               "--mount", f"type=bind,src={source},dst=/input.md,readonly",
               "--mount", f"type=bind,src={output},dst=/out", IMAGE,
               "python", "-B", "-c",
               "from pathlib import Path; s=Path('/input.md').read_text(); Path('/out/mount-smoke.txt').write_text(str(len(s))); print('readonly_bytes='+str(len(s))+' output_write=ok')"]
    completed = subprocess.run(command, text=True, capture_output=True, timeout=60)
    (ROOT / "preflight-stdout.txt").write_text(completed.stdout)
    (ROOT / "preflight-stderr.txt").write_text(completed.stderr)
    marker = output / "mount-smoke.txt"
    record = {
        "kind": "MOUNT_SYNTAX_PREFLIGHT_NOT_CANDIDATE",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "command": command, "exit": completed.returncode,
        "stdout": completed.stdout, "stderr": completed.stderr,
        "readonly_source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "output_marker_sha256": hashlib.sha256(marker.read_bytes()).hexdigest() if marker.exists() else None,
        "candidate_invocations": 0, "auditor_invocations": 0,
    }
    (ROOT / "PREFLIGHT.json").write_text(json.dumps(record, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"exit": completed.returncode, "output_marker": marker.exists(),
                      "stdout": completed.stdout.strip(), "stderr": completed.stderr.strip()}))
    if completed.returncode or not marker.exists():
        raise SystemExit("STOP_MOUNT_PREFLIGHT")


if __name__ == "__main__":
    main()
