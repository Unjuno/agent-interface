"""Excluded source/mount validation. Never invokes the broker or fake child."""
import ast
import hashlib
import json
import os
from pathlib import Path
import shutil

STUDY = Path(__file__).parent
FREEZE = json.loads((STUDY / "FREEZE.json").read_text())
broker = Path("runtime/host_model_ipc_broker_v1.py")
test = Path("runtime/test_host_model_ipc_broker_v1.py")
assert hashlib.sha256(broker.read_bytes()).hexdigest() == FREEZE["source"]["broker_sha256"]
assert hashlib.sha256(test.read_bytes()).hexdigest() == FREEZE["source"]["existing_test_sha256"]
assert "broker.get(\"returncode\") or 1" in broker.read_text()
assert (STUDY / "fake_codex.py").is_file() and os.access(STUDY / "fake_codex.py", os.X_OK)
assert hashlib.sha256((STUDY / "fake_codex.py").read_bytes()).hexdigest() == FREEZE["fake_sha256"]
assert shutil.which("codex") is None
for name in ("fake_codex.py", "formal_runner.py", "audit.py"):
    ast.parse((STUDY / name).read_text())
assert FREEZE["formal_matrix"] == ["exit0", "exit23", "timeout", "unavailable", "malformed", "one-shot-idle", "two-queued"]
print("CONSTRUCTION_CHECK PASS study_mount=present fake_executable=executable source_hashes=2 formal_cases=0 broker_invocations=0 fake_invocations=0 real_codex=absent")
