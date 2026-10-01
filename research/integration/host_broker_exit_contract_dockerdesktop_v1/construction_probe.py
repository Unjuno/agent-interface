from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

from test_contract import BROKER, FAKE_SOURCE


STUDY = Path(__file__).resolve().parent
OUT = Path(os.environ.get("OUT_DIR", "/out"))
FAKE = Path("/tmp/construction-fake-codex")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


for path in (BROKER, STUDY / "test_contract.py", STUDY / "audit_contract.py"):
    compile(path.read_bytes(), str(path), "exec")
FAKE.write_bytes(FAKE_SOURCE)
FAKE.chmod(0o755)
capture = OUT / "fake-capture.json"
OUT.mkdir(parents=True, exist_ok=True)
env = os.environ.copy()
env.update({"FAKE_CAPTURE_PATH": str(capture), "FAKE_EXIT": "0", "FAKE_SLEEP_S": "0"})
proc = subprocess.run([str(FAKE)], input="construction-only\n", text=True,
                      capture_output=True, env=env, timeout=5)
result = {"classification": "PASS_FAKE_ONLY_CONTAINER_CONSTRUCTION" if proc.returncode == 0 else "STOP",
          "broker_sha256": sha256(BROKER.read_bytes()),
          "test_sha256": sha256((STUDY / "test_contract.py").read_bytes()),
          "audit_sha256": sha256((STUDY / "audit_contract.py").read_bytes()),
          "fake_sha256": sha256(FAKE_SOURCE),
          "python": sys.version, "platform": platform.platform(), "machine": platform.machine(),
          "fake_exit": proc.returncode, "fake_stdout": proc.stdout, "fake_stderr": proc.stderr,
          "fake_capture": json.loads(capture.read_text(encoding="utf-8")) if capture.exists() else None}
(OUT / "construction.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n",
                                        encoding="utf-8")
print(json.dumps(result, sort_keys=True))
raise SystemExit(0 if proc.returncode == 0 else 1)
