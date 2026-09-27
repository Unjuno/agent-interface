"""Run exactly one runner, then an isolated-process independent raw audit."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

SRC = Path("/src")
OUT = Path("/out")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def invoke(script: str):
    result = subprocess.run([sys.executable, str(SRC / script)], cwd="/",
                            text=True, encoding="utf-8", errors="replace",
                            capture_output=True, check=False)
    (OUT / (script + ".stdout.txt")).write_text(result.stdout, encoding="utf-8")
    (OUT / (script + ".stderr.txt")).write_text(result.stderr, encoding="utf-8")
    (OUT / (script + ".exit")).write_text(str(result.returncode) + "\n",
                                          encoding="ascii")
    return {"exit": result.returncode, "stdout": result.stdout,
            "stderr": result.stderr}


def main() -> int:
    runner = invoke("runner.py")
    audit = invoke("audit.py") if runner["exit"] == 0 else {
        "exit": None, "stdout": "", "stderr": "not run: runner failed"
    }
    execution = {
        "runner": runner, "audit": audit,
        "image_id": os.environ.get("FROZEN_IMAGE_ID"),
        "source_sha256": {
            name: sha(SRC / name) for name in
            ("host_model_ipc_broker_v1.py", "runner.py", "audit.py", "formal.py",
             "test_harness.py")
        },
    }
    (OUT / "execution.json").write_text(
        json.dumps(execution, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    files = {}
    for path in sorted(OUT.rglob("*")):
        if path.is_file() and path.name != "manifest.json":
            files[str(path.relative_to(OUT))] = {
                "sha256": sha(path), "bytes": path.stat().st_size,
            }
    (OUT / "manifest.json").write_text(json.dumps({
        "files": files, "source_sha256": execution["source_sha256"],
        "image_id": execution["image_id"],
    }, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return 0 if runner["exit"] == 0 and audit["exit"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

