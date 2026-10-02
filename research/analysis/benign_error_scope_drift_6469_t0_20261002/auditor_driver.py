#!/usr/bin/env python3
"""One-shot driver: invokes independent auditor once and retains exact streams."""
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    root = Path("/src")
    out = Path("/audit")
    candidate = Path("/candidate/candidate.json")
    argv = [sys.executable, str(root / "auditor.py"), "--contracts", str(root / "contracts.json"), "--traces", str(root / "traces.json"), "--candidate", str(candidate), "--output", str(out / "audit.json")]
    result = subprocess.run(argv, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    (out / "auditor.stdout.bin").write_bytes(result.stdout)
    (out / "auditor.stderr.bin").write_bytes(result.stderr)
    status = {
        "invocation_count": 1,
        "argv": argv,
        "exit_code": result.returncode,
        "python": sys.version,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "inputs_sha256": {name: sha(root / name) for name in ("auditor.py", "contracts.json", "traces.json")},
        "candidate_raw_sha256": sha(candidate),
        "audit_sha256": sha(out / "audit.json") if (out / "audit.json").exists() else None,
        "stdout_sha256": hashlib.sha256(result.stdout).hexdigest(),
        "stderr_sha256": hashlib.sha256(result.stderr).hexdigest(),
        "environment_network_policy": "WSLc container network=none",
        "gpu_requested": False,
    }
    (out / "auditor.status.json").write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(status, sort_keys=True))
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
