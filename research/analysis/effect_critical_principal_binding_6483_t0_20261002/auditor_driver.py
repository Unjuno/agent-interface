#!/usr/bin/env python3
"""Run the independent auditor once and preserve exact output streams."""
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    src, candidate, out = Path("/src"), Path("/candidate/candidate.json"), Path("/audit")
    argv = [sys.executable, str(src / "auditor.py"), "--scenarios", str(src / "scenarios.json"), "--oracle", str(src / "oracle.json"), "--candidate", str(candidate), "--output", str(out / "audit.json")]
    proc = subprocess.run(argv, cwd=src, capture_output=True, check=False)
    (out / "auditor.stdout.bin").write_bytes(proc.stdout)
    (out / "auditor.stderr.bin").write_bytes(proc.stderr)
    status = {
        "invocation_count": 1,
        "argv": argv,
        "exit_code": proc.returncode,
        "python": sys.version,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "source_sha256": {name: sha(src / name) for name in ("auditor.py", "scenarios.json", "oracle.json")},
        "candidate_raw_sha256": sha(candidate),
        "audit_sha256": sha(out / "audit.json") if (out / "audit.json").exists() else None,
        "stdout_sha256": hashlib.sha256(proc.stdout).hexdigest(),
        "stderr_sha256": hashlib.sha256(proc.stderr).hexdigest(),
        "network": "none",
        "gpu_requested": False,
    }
    (out / "auditor.status.json").write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(status, sort_keys=True))
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
