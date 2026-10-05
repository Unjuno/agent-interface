"""Independent saved-output, provenance, and event-order audit for A02."""
import hashlib
import json
from pathlib import Path

PKG = Path(__file__).resolve().parent
freeze = json.loads((PKG / "FREEZE-A02.json").read_text(encoding="utf-8"))
a01_freeze_bytes = (PKG / "FREEZE.json").read_bytes()
assert hashlib.sha256(a01_freeze_bytes).hexdigest() == freeze["a01_freeze_sha256"]
for item in freeze["locked_files"]:
    data = (PKG / item["path"]).read_bytes()
    assert len(data) == item["bytes"], f"byte count mismatch: {item['path']}"
    assert hashlib.sha256(data).hexdigest() == item["sha256"], f"hash mismatch: {item['path']}"
for item in json.loads(a01_freeze_bytes)["locked_files"]:
    data = (PKG / item["path"]).read_bytes()
    assert len(data) == item["bytes"], f"A01 byte count mismatch: {item['path']}"
    assert hashlib.sha256(data).hexdigest() == item["sha256"], f"A01 hash mismatch: {item['path']}"

result_bytes = (PKG / "results" / "a02" / "RESULT.json").read_bytes()
result = json.loads(result_bytes)
stdout = (PKG / "TOOL_STDOUT_A02_CAPTURE.txt").read_text(encoding="utf-8")
assert stdout == json.dumps(result, sort_keys=True) + "\n", "captured stdout mismatch"
assert result["base_main"] == freeze["base_main"]
assert result["candidate_pr_7805_head"] == freeze["candidate_pr_7805_head"]

control = result["control"]
candidate = result["candidate"]
for arm in (control, candidate):
    call_ns = arm["timing"]["barrier_call_end_ns"] - arm["timing"]["barrier_call_start_ns"]
    assert 1_800_000_000 <= call_ns <= 2_500_000_000
    assert arm["terminal"] == {"release_verified": False, "status": "failed"}
    assert arm["physical_empty"] is True
    assert arm["owner_stopped_after_terminal"] is True
    assert arm["event_after_terminal"] is False
    assert arm["owner_releases"][0]["reason"] == "expired"
    assert arm["owner_releases"][0]["verified"] is True
    assert arm["owner_releases"][0]["keys_down"] == []
    assert arm["owner_releases"][0]["per_key_classifications"] == ["CONFIRMED_PHYSICAL_UP"]

assert control["up_rows"] == []
assert control["bridge_held"] == ["F8"]
assert control["bridge_events"][-1] == "terminal"

assert candidate["timing"]["owner_stopped_within_bound"] is True
assert 0 <= candidate["timing"]["late_drain_wait_ns"] <= 1_500_000_000
assert candidate["bridge_held"] == []
assert candidate["bridge_events"] == [
    "accepted", "step_started", "input_admission", "input_release_measurement", "terminal"
]
assert len(candidate["up_rows"]) == 1
up = candidate["up_rows"][0]
assert up["event"] == "input_release_measurement"
assert (up["id"], up["step"], up["key"]) == ("timeout-a02-candidate", 0, "F8")
assert up["reason"] == "expired"
assert up["grants_input_authority"] is False
assert up["application_consumption_observed"] is False
measurement = up["physical_key_measurement"]
assert measurement["classification"] == "CONFIRMED_PHYSICAL_UP"
assert measurement["identity_status"] == "RETIRED"
assert measurement["grants_input_authority"] is False
assert measurement["edge"] == "up"
assert measurement["adapter_edge"]["status"] == "CONFIRMED_PHYSICAL_UP"
assert measurement["adapter_edge"]["grants_input_authority"] is False
pre = measurement["pre_sample"]
post = measurement["post_sample"]
assert pre["available"] is True and pre["down"] is True and pre["error"] is None
assert post["available"] is True and post["down"] is False and post["error"] is None
assert pre["finished_ns"] <= measurement["release_request_ns"]
assert measurement["release_request_ns"] <= measurement["sync_return_ns"]
assert measurement["sync_return_ns"] <= post["finished_ns"]
assert measurement["adapter_edge"]["interval"] == [pre["finished_ns"], post["finished_ns"]]

print(json.dumps({
    "disposition": "PASS_BOUNDED_LATE_DRAIN_SCOPED",
    "baseline_stale_F8": True,
    "candidate_up_rows": len(candidate["up_rows"]),
    "candidate_terminal_failed_unverified": True,
    "candidate_bridge_empty": True,
    "a02_frozen_file_count": len(freeze["locked_files"]),
    "a01_frozen_file_count": len(json.loads(a01_freeze_bytes)["locked_files"]),
    "candidate_release_bracket_ns": measurement["adapter_edge"]["interval"][1]-measurement["adapter_edge"]["interval"][0],
    "audit_scope": "saved paired fake-display output and source hashes; no candidate rerun, real OS input, or application-effect audit",
}, sort_keys=True))
