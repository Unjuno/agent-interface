#!/usr/bin/env python3
"""One-shot driver: invokes the frozen candidate once and retains exact streams."""
import hashlib
import json
import os
import platform
import subprocess
import sys
from pathlib import Path


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    root = Path("/src")
    out = Path("/out")
    out.mkdir(parents=True, exist_ok=True)
    argv = [sys.executable, str(root / "candidate.py"), "--contracts", str(root / "contracts.json"), "--traces", str(root / "traces.json"), "--output", str(out / "candidate.json")]
    result = subprocess.run(argv, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    (out / "candidate.stdout.bin").write_bytes(result.stdout)
    (out / "candidate.stderr.bin").write_bytes(result.stderr)
    status = {
        "invocation_count": 1,
        "argv": argv,
        "exit_code": result.returncode,
        "python": sys.version,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "inputs_sha256": {name: sha(root / name) for name in ("candidate.py", "contracts.json", "traces.json")},
        "raw_sha256": sha(out / "candidate.json") if (out / "candidate.json").exists() else None,
        "stdout_sha256": hashlib.sha256(result.stdout).hexdigest(),
        "stderr_sha256": hashlib.sha256(result.stderr).hexdigest(),
        "environment_network_policy": "WSLc container network=none",
        "gpu_requested": False,
    }
    (out / "candidate.status.json").write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(status, sort_keys=True))
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
