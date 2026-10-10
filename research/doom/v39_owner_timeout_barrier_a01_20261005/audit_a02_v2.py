"""Read-only audit of the structured A02 pair; does not rerun either arm."""
import hashlib
import json
from pathlib import Path

PKG = Path(__file__).resolve().parent
freeze_bytes = (PKG / "FREEZE-A02.json").read_bytes()
freeze = json.loads(freeze_bytes)
a01_bytes = (PKG / "FREEZE.json").read_bytes()
assert hashlib.sha256(a01_bytes).hexdigest() == freeze["a01_freeze_sha256"]
for item in freeze["locked_files"]:
    data = (PKG / item["path"]).read_bytes()
    assert len(data) == item["bytes"], f"A02 byte mismatch: {item['path']}"
    assert hashlib.sha256(data).hexdigest() == item["sha256"], f"A02 hash mismatch: {item['path']}"
for item in json.loads(a01_bytes)["locked_files"]:
    data = (PKG / item["path"]).read_bytes()
    assert len(data) == item["bytes"], f"A01 byte mismatch: {item['path']}"
    assert hashlib.sha256(data).hexdigest() == item["sha256"], f"A01 hash mismatch: {item['path']}"
provenance = json.loads((PKG / "SOURCE_PROVENANCE.json").read_text(encoding="utf-8"))
assert provenance["all_match"] is True
assert len(provenance["comparisons"]) == 16
assert all(item["matches"] is True for item in provenance["comparisons"])

result = json.loads((PKG / "results" / "a02" / "RESULT.json").read_text(encoding="utf-8"))
assert result["schema"] == "v39-owner-timeout-late-drain-result-v1"
assert result["base_main"] == freeze["base_main"]
assert result["candidate_pr_7805_head"] == freeze["candidate_pr_7805_head"]

for arm in (result["control"], result["candidate"]):
    call_ns = arm["timing"]["barrier_call_end_ns"] - arm["timing"]["barrier_call_start_ns"]
    assert 1_800_000_000 <= call_ns <= 2_500_000_000
    assert arm["terminal"] == {"release_verified": False, "status": "failed"}
    assert arm["physical_empty"] is True
    assert arm["owner_stopped_after_terminal"] is True
    assert arm["event_after_terminal"] is False
    assert arm["owner_releases"][0] == {
        "buttons_down": [], "keys_down": [],
        "per_key_classifications": ["CONFIRMED_PHYSICAL_UP"],
        "reason": "expired", "verified": True,
    }

control = result["control"]
assert control["up_rows"] == []
assert control["bridge_held"] == ["F8"]
assert control["bridge_events"] == ["accepted", "step_started", "input_admission", "terminal"]

candidate = result["candidate"]
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
pre, post = measurement["pre_sample"], measurement["post_sample"]
assert pre["available"] is True and pre["down"] is True and pre["error"] is None
assert post["available"] is True and post["down"] is False and post["error"] is None
assert pre["finished_ns"] <= measurement["release_request_ns"]
assert measurement["release_request_ns"] <= measurement["sync_return_ns"]
assert measurement["sync_return_ns"] <= post["finished_ns"]
assert measurement["adapter_edge"]["interval"] == [pre["finished_ns"], post["finished_ns"]]

capture = (PKG / "TOOL_STDOUT_A02_CAPTURE.txt").read_text(encoding="utf-8")
capture_incomplete = json.loads(capture) != result
assert capture_incomplete is True, "A02 V1 capture discrepancy was not preserved"
assert (PKG / "AUDIT_A02_ATTEMPT_V1.txt").is_file()
print(json.dumps({
    "disposition": "PASS_BOUNDED_LATE_DRAIN_SCOPED",
    "control_stale_F8": True,
    "candidate_up_rows": len(candidate["up_rows"]),
    "candidate_terminal_failed_unverified": True,
    "candidate_bridge_empty": True,
    "candidate_additional_wait_ns": candidate["timing"]["late_drain_wait_ns"],
    "source_provenance_comparisons": len(provenance["comparisons"]),
    "a02_stdout_capture_complete": False,
    "audit_scope": "structured saved candidate output and frozen source hashes; no candidate rerun, exact stdout verification, or real OS input audit",
}, sort_keys=True))
