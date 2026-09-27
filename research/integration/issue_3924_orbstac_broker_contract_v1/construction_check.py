"""Excluded construction validation; deliberately invokes no broker/fake."""
import ast
import hashlib
import json
import os
from pathlib import Path

root = Path(__file__).parent
broker = Path("runtime/host_model_ipc_broker_v1.py")
cases = {
    "exit0": ("FAKE_EXIT", "0"),
    "exit23": ("FAKE_EXIT", "23"),
    "timeout": ("FAKE_SLEEP_S", "0.3"),
    "unavailable": ("CODEX_EXE", "/missing/fake-codex"),
    "malformed": (None, None),
    "two-queued": ("FAKE_EXIT", "0"),
}
assert "broker.get(\"returncode\") or 1" in broker.read_text()
freeze = json.loads((root / "FREEZE_02.json").read_text())
assert hashlib.sha256(broker.read_bytes()).hexdigest() == freeze["source"]["broker_sha256"]
assert os.access(root / "fake_codex.py", os.X_OK)
ast.parse((root / "fake_codex.py").read_text())
ast.parse((root / "construct.py").read_text())
ast.parse((root / "formal_runner_02.py").read_text())
for name, expected in cases.items():
    request = json.loads((root / "fixtures" / name / "request.json").read_text())
    environment = json.loads((root / "fixtures" / name / "environment.json").read_text())
    if name == "two-queued":
        assert request is None
    else:
        assert request["request_id"] == name
    if expected[0] is not None:
        assert environment[expected[0]] == expected[1]
assert sorted(p.name for p in (root / "fixtures").iterdir() if p.is_dir() and p.name != "cases") == [
    "exit0", "exit23", "malformed", "one-shot-idle", "timeout", "two-queued", "unavailable"
]
print("CONSTRUCTION_CHECK PASS cases=7 fake_process_invocations=0 broker_invocations=0")
