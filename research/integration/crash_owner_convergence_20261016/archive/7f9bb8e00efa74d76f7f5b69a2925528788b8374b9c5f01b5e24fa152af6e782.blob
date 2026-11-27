import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXP = ROOT.parent
FREEZE = json.loads((EXP / "FREEZE.json").read_text(encoding="utf-8"))
RAW_PATH = EXP / "results" / "A01" / "RAW.json"
raw = json.loads(RAW_PATH.read_text(encoding="utf-8"))
checks = {}
checks["raw_sha256"] = hashlib.sha256(RAW_PATH.read_bytes()).hexdigest()
checks["source_hashes_match"] = all(
    hashlib.sha256((EXP / "SOURCE" / name).read_bytes()).hexdigest() == digest
    for name, digest in FREEZE["source_sha256"].items())
checks["candidate_hash_matches"] = (
    hashlib.sha256((EXP / "SOURCE" / "candidate.py").read_bytes()).hexdigest()
    == FREEZE["candidate_sha256"])
checks["input_hashes_match"] = all(
    hashlib.sha256((EXP / "INPUTS" / name).read_bytes()).hexdigest() == digest
    for name, digest in FREEZE["input_sha256"].items())
checks["raw_has_two_arms"] = set(raw["arms"]) == {
    "visual_changed", "same_frame_control"}
checks["raw_runtime_errors_empty"] = raw["errors"] == []
checks["both_had_real_x_keydown"] = all(
    arm["key_press_event"] is not None
    and arm["key_press_event"]["keycode"] == arm["keycode"]
    and arm["key_down_before_new_frame"] is True
    and arm["key_down_during_pending_turn"] is True
    and arm["key_down_after_answer"] is True
    for arm in raw["arms"].values())
checks["changed_frame_did_not_invalidate"] = (
    raw["arms"]["visual_changed"]["monitor_invalidation"] is None
    and raw["arms"]["visual_changed"]["answer_eligible"] is True
    and raw["arms"]["visual_changed"]["final_status"]
        == "READY_FOR_FRESH_EXECUTOR_ADMISSION"
    and raw["arms"]["visual_changed"]["executor_admission"] is None)
checks["same_frame_control_unchanged"] = (
    raw["arms"]["same_frame_control"]["monitor_invalidation"] is None
    and raw["arms"]["same_frame_control"]["answer_eligible"] is True
    and raw["arms"]["same_frame_control"]["final_status"]
        == "READY_FOR_FRESH_EXECUTOR_ADMISSION")
checks["owner_close_released_each_key"] = all(
    arm["owner_close_record"] is not None
    and arm["owner_close_record"]["verified"] is True
    and arm["owner_close_record"]["key_state_source"] == "x11_query_keymap"
    and arm["owner_closed"] is True
    and arm["owner_stopped"] is True
    and arm["owner_thread_alive"] is False
    and arm["key_release_event"] is not None
    and arm["key_release_event"]["keycode"] == arm["keycode"]
    and arm["observer_key_up_after_close"] is True
    for arm in raw["arms"].values())
checks["xvfb_clean_exit"] = raw["cleanup"].get("xvfb_exit") == 0
checks["candidate_stop_reason_reproduced_from_raw"] = (
    raw["status"] == "STOP" and raw["errors"] == []
    and raw["cleanup"] == {"xvfb_exit": 0})
checks["formal_decision"] = "STOP"
checks["audit_result"] = "PASS_RAW_CONSISTENCY" if all(
    value is True for key, value in checks.items()
    if key not in {"raw_sha256", "formal_decision", "audit_result"}) else "FAIL"
out = ROOT.parent / "results" / "A01" / "AUDIT.json"
out.write_text(json.dumps(checks, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(checks, sort_keys=True))
if checks["audit_result"] != "PASS_RAW_CONSISTENCY":
    raise SystemExit(1)
