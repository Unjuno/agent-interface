"""Build isolated, bounded case fixtures for the frozen broker contract."""
import json
from pathlib import Path

OUT = Path("/evidence/cases")
SRC = Path("/source")
OUT.mkdir(parents=True, exist_ok=True)
for name, env, request in [
    ("exit0", {"FAKE_EXIT": "0"}, {"request_id": "exit0", "schema": "/repo/schema.json", "working": "/repo", "prompt": "fake"}),
    ("exit23", {"FAKE_EXIT": "23"}, {"request_id": "exit23", "schema": "/repo/schema.json", "working": "/repo", "prompt": "fake"}),
    ("timeout", {"FAKE_EXIT": "0", "FAKE_SLEEP_S": "0.3"}, {"request_id": "timeout", "schema": "/repo/schema.json", "working": "/repo", "prompt": "fake"}),
    ("unavailable", {"CODEX_EXE": "/missing/fake-codex"}, {"request_id": "unavailable", "schema": "/repo/schema.json", "working": "/repo", "prompt": "fake"}),
    ("malformed", {}, {"request_id": "malformed"}),
    ("two-queued", {"FAKE_EXIT": "0"}, None),
]:
    case = OUT / name
    case.mkdir(parents=True, exist_ok=True)
    (case / "request.json").write_text(json.dumps(request) + "\n", encoding="utf-8")
    (case / "environment.json").write_text(json.dumps(env, sort_keys=True) + "\n", encoding="utf-8")
(OUT / "one-shot-idle").mkdir(exist_ok=True)
print("CONSTRUCTION_FIXTURES_READY cases=7 formal_invocations=0")
