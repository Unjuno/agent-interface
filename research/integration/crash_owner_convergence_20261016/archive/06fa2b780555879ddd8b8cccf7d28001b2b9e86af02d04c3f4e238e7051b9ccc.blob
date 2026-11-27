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
arm = raw["arms"].get("health_unchanged_acceptance", {})
checks["validity_and_acceptance_recorded"] = (
    arm.get("planner_admission", {}).get("status") == "READY_FOR_ACTION_VALIDITY"
    and arm.get("action_validity", {}).get("status") == "VALID_CURRENT"
    and arm.get("action_admission", {}).get("status") == "READY_FOR_FRESH_EXECUTOR_ADMISSION"
    and arm.get("executor_acceptance_receipt", {}).get("status") == "INPUT_ADMITTED")
checks["xvfb_keydown_and_owner_keyup_verified"] = (
    arm.get("key_press_event", {}).get("type") == 2
    and arm.get("key_release_event", {}).get("type") == 3
    and arm.get("key_release_transition", {}).get("owner_thread_keyup_verified") is True
    and arm.get("key_release_transition", {}).get("owner_thread_keyup_receipt", {}).get("server_keyup_verified") is True
    and arm.get("observer_key_up_after_cleanup") is True
    and arm.get("owner_stopped") is True
    and arm.get("owner_thread_alive") is False)
checks["fake_acceptance_order_mismatch_detected"] = (
    arm.get("key_press_event", {}).get("observed_ns", 0)
    < arm.get("executor_acceptance_receipt", {}).get("executor_admission", {}).get("accepted_ns", 0))
checks["hard_drop_arm_not_run"] = set(raw["arms"]) == {"health_unchanged_acceptance"}
checks["candidate_stop_preserved"] = (
    raw.get("status") == "STOP"
    and bool(raw.get("errors"))
    and "current action did not traverse validity" in raw["errors"][0]
    and raw.get("cleanup", {}).get("xvfb_exit") == 0)
checks["formal_decision"] = "STOP"
checks["audit_result"] = "PASS_RAW_CONSISTENCY" if all(
    value is True for key, value in checks.items()
    if key not in {"raw_sha256", "formal_decision", "audit_result"}) else "FAIL"
out = EXP / "results" / "A01" / "AUDIT.json"
out.write_text(json.dumps(checks, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(checks, sort_keys=True))
if checks["audit_result"] != "PASS_RAW_CONSISTENCY":
    raise SystemExit(1)
