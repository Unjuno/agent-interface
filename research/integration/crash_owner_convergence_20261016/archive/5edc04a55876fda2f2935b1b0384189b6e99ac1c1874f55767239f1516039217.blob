#!/usr/bin/env python3
"""Audit A01 raw evidence only; never invokes the candidate."""
import hashlib, json, pathlib, sys
root = pathlib.Path(__file__).resolve().parents[1]
freeze = json.loads((root / "FREEZE.json").read_text())
raw = json.loads((root / "results/A01/RAW.json").read_text())
arm = raw["arms"]["active_hard_health_invalidation"]
events = arm["executor_events"]
press_ns = arm["key_press_event"]["observed_ns"]
release_ns = arm["key_release_event"]["observed_ns"]
accepted_ns = arm["executor_acceptance"]["accepted_ns"]
terminal = next(e for e in events if e["event"] == "terminal")
release = terminal["release"]
transition = release["owner_transitions"][0]
receipt = transition["owner_thread_keyup_receipt"]
invalidation = arm["monitor_invalidation"]
final = arm["final_admission"]
planner = final["planner_terminal"]
checks = {
    "candidate_status_complete": raw["status"] == "CANDIDATE_COMPLETE",
    "candidate_errors_empty": raw["errors"] == [],
    "xvfb_exit_zero": raw["cleanup"]["xvfb_exit"] == 0,
    "source_hashes_match_freeze": all(hashlib.sha256((root / "SOURCE" / name).read_bytes()).hexdigest() == digest for name, digest in freeze["source_sha256"].items()),
    "input_hashes_match_freeze": all(hashlib.sha256((root / "INPUTS" / name).read_bytes()).hexdigest() == digest for name, digest in freeze["input_sha256"].items()),
    "candidate_hash_matches_freeze": hashlib.sha256((root / "SOURCE/candidate.py").read_bytes()).hexdigest() == freeze["candidate_sha256"],
    "executor_accepted_before_keypress": accepted_ns < press_ns,
    "key_down_at_observation": arm["key_down_when_observation_arrived"] is True,
    "hard_health_invalidation": invalidation["outcome"]["status"] == "HARD_INVALIDATED" and invalidation["outcome"]["current_value"] == 80,
    "cancel_matched": arm["executor_cancel_matched"] is True and arm["planner_cancellation_requested"] is True,
    "cancelled_terminal_verified_release": terminal["status"] == "cancelled" and release["verified"] is True and release["keys_down"] == [],
    "owner_explicit_keyup_verified": receipt["event"] == "owner_explicit_keyup" and receipt["server_keyup_verified"] is True and receipt["server_sync_completed"] is True and receipt["server_key_down_after_keyup"] is False,
    "independent_x_keyup_before_planner_return": release_ns < planner["terminal_observed_ns"] and arm["xvfb_key_up_after_terminal"] is True,
    "planner_answer_ineligible": planner["answer_eligible"] is False and arm["planner_answer_eligible"] is False,
    "final_admission_rejected_invalidated": final["status"] == "REJECTED_POLICY_INVALIDATED" and final["input_authority_admitted"] is False,
    "executor_and_owner_stopped": arm["executor_active_after_terminal"] is False and arm["owner_closed"] is True and arm["owner_stopped"] is True and arm["owner_thread_alive"] is False,
}
failed = [k for k, v in checks.items() if not v]
result = {"schema":"v39-executor-cancel-active-key-xvfb-audit-a01-v1", "decision":"PASS_METHOD_SCOPED" if not failed else "STOP", "checks":checks, "failed":failed, "timing_ns":{"executor_accepted":accepted_ns,"x_keypress":press_ns,"x_keyrelease":release_ns,"planner_terminal":planner["terminal_observed_ns"]}}
out = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else root / "AUDITOR/audit.json"
out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps(result, sort_keys=True))
sys.exit(bool(failed))
