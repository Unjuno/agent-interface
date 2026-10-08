"""Independently verify A02's current-main provenance and retained replay."""
import hashlib
import json
import subprocess
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
A01 = REPO / "research/doom/v39_current_main_cancel_executor_handoff_a01_20261008"
FREEZE = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
RESULT = json.loads((HERE / "RESULT.json").read_text(encoding="utf-8"))
MAIN = FREEZE["current_main_commit"]


def git_blob(revision, path):
    return subprocess.check_output(["git", "-C", str(REPO), "rev-parse", f"{revision}:{path}"], text=True).strip()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


prior = json.loads((A01 / "FREEZE.json").read_text(encoding="utf-8"))
sources = prior["current_main_sources"] + prior["executor_stack_modules"]
assert len(sources) == FREEZE["source_count"] == 13
for item in sources:
    assert git_blob(MAIN, item["path"]) == item["git_blob"], item["path"]
    local = A01 / (item.get("local_path") or f"source/executor_v13_stack/{item['name']}")
    assert local.stat().st_size == item["bytes"], item["path"]
    assert sha(local) == item["sha256"], item["path"]
    assert git_blob(MAIN, item["path"]) == item["git_blob"]

assert RESULT["disposition"] == "PASS_CURRENT_MAIN_SOURCE_ALIGNED_SOFTWARE_REPLAY"
assert RESULT["current_main_commit"] == MAIN
assert RESULT["source_alignment"] == {"matched": 13, "total": 13}
assert RESULT["commands"] == {"replay": 0, "unit": 0, "audit": 0}
assert RESULT["event_order"] == [
    "accepted", "step_started", "controller_cancel_write", "cancel_requested",
    "controller_cancel_flush", "appserver_interrupt_request_written", "input_released",
    "terminal", "appserver_interrupt_response_injected",
]
assert RESULT["verified_empty_release"] == {"verified": True, "keys_down": [], "buttons_down": []}
assert "OK" in ((HERE / "unit.stdout.txt").read_text(encoding="utf-8") +
                 (HERE / "unit.stderr.txt").read_text(encoding="utf-8"))
assert "PASS_CURRENT_MAIN_CROSS_LAYER_ORDER_AUDIT" in (HERE / "audit.stdout.txt").read_text(encoding="utf-8")
assert "PASS_CURRENT_MAIN_HELPER_CROSS_LAYER_RELEASE_BEFORE_INTERRUPT_RESPONSE" in (HERE / "replay.stdout.txt").read_text(encoding="utf-8")

# The historical A01 result and audit must remain byte-identical to main.
for name in ("RESULT.json", "AUDIT.json"):
    original = subprocess.check_output(["git", "-C", str(REPO), "show", f"{MAIN}:research/doom/v39_current_main_cancel_executor_handoff_a01_20261008/{name}"])
    assert hashlib.sha256(original).hexdigest() == sha(A01 / name), name

for line in (HERE / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
    digest, name = line.split("  ", 1)
    assert sha(HERE / name) == digest, name
print("PASS: 13/13 current-main source identities; isolated replay, unit, audit; preserved A01 records")
