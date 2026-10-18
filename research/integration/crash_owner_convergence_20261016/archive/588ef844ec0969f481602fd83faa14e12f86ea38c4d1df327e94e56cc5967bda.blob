import hashlib
import json
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
checks["both_arms_present"] = set(raw["arms"]) == {
    "health_drop_invalidates", "health_unchanged_control"}
checks["hard_drop_guard_invalidated"] = (
    raw["arms"]["health_drop_invalidates"]["monitor_invalidation"]["outcome"]["status"]
        == "HARD_INVALIDATED"
    and raw["arms"]["health_drop_invalidates"]["health_guard_outcome"]["current_value"] == 80)
checks["production_cancel_terminal_keyup"] = (
    raw["arms"]["health_drop_invalidates"]["executor_terminal"]["status"] == "cancelled"
    and raw["arms"]["health_drop_invalidates"]["executor_terminal"]["release"]["verified"] is True
    and raw["arms"]["health_drop_invalidates"]["key_down_after_cancel"] is False
    and raw["arms"]["health_drop_invalidates"]["key_release_event"] is not None
    and raw["arms"]["health_drop_invalidates"]["observer_key_up_after_cleanup"] is True)
transition = raw["arms"]["health_drop_invalidates"]["release_transitions"][0]
owner_receipt = transition["owner_thread_keyup_receipt"]
checks["owner_receipt_verified"] = (
    transition["owner_thread_keyup_verified"] is True
    and owner_receipt["server_keyup_verified"] is True
    and owner_receipt["server_sync_completed"] is True
    and owner_receipt["server_key_down_after_keyup"] is False
    and owner_receipt["key_state_source"] == "x11_query_keymap")
checks["answer_and_action_rejected"] = (
    raw["arms"]["health_drop_invalidates"]["planner_cancellation_requested"] is True
    and raw["arms"]["health_drop_invalidates"]["answer_eligible"] is False
    and raw["arms"]["health_drop_invalidates"]["final_admission"]["status"]
        == "REJECTED_POLICY_INVALIDATED"
    and raw["arms"]["health_drop_invalidates"]["final_admission"]["executor_admission"] is None)
checks["control_preserved_but_requires_action_validity"] = (
    raw["arms"]["health_unchanged_control"]["monitor_invalidation"] is None
    and raw["arms"]["health_unchanged_control"]["cancel_result"] is None
    and raw["arms"]["health_unchanged_control"]["answer_eligible"] is True
    and raw["arms"]["health_unchanged_control"]["key_down_after_cancel"] is True
    and raw["arms"]["health_unchanged_control"]["final_admission"]["status"]
        == "READY_FOR_ACTION_VALIDITY")
checks["xvfb_clean_exit"] = raw["cleanup"].get("xvfb_exit") == 0
checks["formal_status_preserved"] = (
    raw["status"] == "STOP" and bool(raw["errors"])
    and "unchanged control did not preserve policy" in raw["errors"][0])
checks["audit_result"] = "PASS_RAW_CONSISTENCY" if all(
    value is True for key, value in checks.items()
    if key not in {"raw_sha256", "audit_result"}) else "FAIL"
out = EXP / "results" / "A01" / "AUDIT.json"
out.write_text(json.dumps(checks, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(checks, sort_keys=True))
if checks["audit_result"] != "PASS_RAW_CONSISTENCY":
    raise SystemExit(1)
