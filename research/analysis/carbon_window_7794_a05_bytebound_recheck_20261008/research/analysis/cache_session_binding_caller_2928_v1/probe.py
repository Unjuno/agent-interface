"""Shadow-only boundary probe for #2928's current-main acquisition caller."""
import hashlib
import importlib.util
import json
import platform
import sys
from pathlib import Path

FREEZE = Path(__file__).with_name("FREEZE.json")
freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
source = Path(sys.argv[1]).resolve()
source_bytes = source.read_bytes()
sha256 = hashlib.sha256(source_bytes).hexdigest()
git_blob = hashlib.sha1(b"blob " + str(len(source_bytes)).encode() + b"\0" + source_bytes).hexdigest()
assert sha256 == freeze["subject_sha256"], sha256
assert git_blob == freeze["subject_git_blob"], git_blob

spec = importlib.util.spec_from_file_location("frozen_subject", source)
subject = importlib.util.module_from_spec(spec)
spec.loader.exec_module(subject)

rows = []
clock_value = 0

def clock():
    global clock_value
    clock_value += 10
    return clock_value

for case in freeze["cases"]:
    cache = {"target_id": "target-1", "cached_session_id": case["cached_session_id"]}
    observed = {"reuse_payload": None, "final_payload": None, "execute_calls": 0}

    def reuse_revalidate(payload):
        observed["reuse_payload"] = payload
        return {"status": "revalidated"}

    def final_revalidate(payload):
        observed["final_payload"] = payload
        return {"status": "revalidated"}

    def execute(payload):
        observed["execute_calls"] += 1
        return {"status": "safe_yield", "reason": "unknown_state", "completed_actions": 0}

    adapters = {
        "reuse_revalidate": reuse_revalidate,
        "final_revalidate": final_revalidate,
        "execute": execute,
        "verify_effect": lambda _: {"status": "unavailable"},
    }
    route_spec = {
        "target": "synthetic-target",
        "route": "reuse",
        "coarse_origin": "caller_provided",
        "provided_coarse": None,
        "cached_target": cache,
        "local_repair_on": [],
        "repair_on": [],
        "session_id": case["request_session_id"],
    }
    result = subject.run(route_spec, adapters, clock=clock, id_factory=lambda: "unused")
    rows.append({
        "case_id": case["case_id"],
        "request_session_id": case["request_session_id"],
        "cached_session_id": cache["cached_session_id"],
        "reuse_payload": observed["reuse_payload"],
        "final_payload": observed["final_payload"],
        "execute_adapter_calls": observed["execute_calls"],
        "completed_actions": result.get("execution_progress", {}).get("completed_actions", 0),
        "outcome": result["outcome"],
        "effect": result["task_effect"],
    })

raw = {
    "schema": "issue-2928-current-caller-session-binding-raw-v1",
    "source_git_blob": git_blob,
    "source_sha256": sha256,
    "python": sys.version,
    "platform": platform.platform(),
    "rows": rows,
}
out = Path(sys.argv[2])
out.write_text(json.dumps(raw, sort_keys=True, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"rows": len(rows), "out": str(out), "outcome": [r["outcome"] for r in rows]}))
