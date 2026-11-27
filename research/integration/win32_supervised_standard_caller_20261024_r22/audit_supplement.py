"""Additive R22 evidence check using final event rows; never rewrites audit.json."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = json.loads((HERE / "raw.json").read_text(encoding="utf-8"))
AUDIT = json.loads((HERE / "audit.json").read_text(encoding="utf-8"))
CONDITIONS = json.loads((HERE / "conditions.json").read_text(encoding="utf-8"))
trial = CONDITIONS["trial"]
fixture = RAW.get("fixture") or {}
generation = (fixture.get("target_identity") or {}).get("generation")
hook = RAW.get("hook_stopped") or {}
events = hook.get("events") or []
down = next((item for item in events if item.get("message") == 0x0100
             and item.get("vk") == ord("Q")), {})
up = next((item for item in events if item.get("message") == 0x0101
           and item.get("vk") == ord("Q")), {})
cancel = RAW.get("public_cancel") or {}
producer = RAW.get("producer_identity_from_cancel") or {}
exit_witness = RAW.get("producer_exit_witness") or {}
polls = RAW.get("result_readbacks") or []
recovered_poll = {}
recovered_row = {}
for item in polls:
    response = item.get("response") or {}
    row = response.get("result") if isinstance(response.get("result"), dict) else response
    row = row if isinstance(row, dict) else {}
    cancellation = row.get("cancellation") or {}
    if cancellation.get("status") == "recovered":
        recovered_poll, recovered_row = item, row
cancellation = recovered_row.get("cancellation") or {}
custody = cancellation.get("result") or {}
readback = RAW.get("independent_readback") or {}
raw_hash = hashlib.sha256((HERE / "raw.json").read_bytes()).hexdigest()

checks = []
def check(name, passed, evidence):
    checks.append({"name": name, "passed": bool(passed), "evidence": evidence})

check("frozen_audit_is_preserved",
    AUDIT.get("status") == "FAIL_OR_UNKNOWN" and AUDIT.get("passed") == 8
    and AUDIT.get("total") == 10,
    {"frozen_audit_status": AUDIT.get("status"),
     "passed": AUDIT.get("passed"), "total": AUDIT.get("total"),
     "failed_checks": [item.get("name") for item in AUDIT.get("checks", [])
                       if not item.get("passed")]})
check("callback_return_is_retained_in_final_event_row",
    type(down.get("callback_return_ns")) is int
    and down.get("callback_return_ns") == hook.get("callback_return_ns")
    and type(cancel.get("returned_monotonic_ns")) is int
    and cancel["returned_monotonic_ns"] < down["callback_return_ns"]
    and hook.get("blocked_q_down_suppressed") is not True,
    {"callback_return_ns": down.get("callback_return_ns"),
     "final_hook_callback_return_ns": hook.get("callback_return_ns"),
     "cancel_return_ns": cancel.get("returned_monotonic_ns"),
     "hold_snapshot_callback_return_ns": (RAW.get("post_cancel_io_hold") or {})
         .get("hook_trace_after_release", {}).get("callback_return_ns"),
     "suppressed": hook.get("blocked_q_down_suppressed")})
check("producer_exit_and_q_up_follow_forwarded_down",
    exit_witness.get("status") == "exited"
    and exit_witness.get("pid") == producer.get("pid")
    and exit_witness.get("creation_time_100ns") == producer.get("creation_time_100ns")
    and type(exit_witness.get("observed_monotonic_ns")) is int
    and exit_witness["observed_monotonic_ns"] >= down.get("callback_return_ns", 0)
    and type(up.get("callback_entry_ns")) is int
    and up["callback_entry_ns"] > down.get("callback_return_ns", 0),
    {"producer_identity": producer, "producer_exit": exit_witness,
     "q_down_event": down, "q_up_event": up})
check("public_cancellation_receipt_confirms_bounded_recovery",
    cancellation.get("status") == "recovered"
    and cancellation.get("release_confirmed") is True
    and cancellation.get("replay_allowed") is False
    and cancellation.get("task_success") is None
    and custody.get("phase") == "recovered"
    and custody.get("release_confirmed") is True
    and custody.get("operation_id") == cancellation.get("action_operation_id")
    and custody.get("target_generation") == generation
    and type(recovered_poll.get("returned_monotonic_ns")) is int
    and type(cancel.get("started_monotonic_ns")) is int
    and (recovered_poll["returned_monotonic_ns"] - cancel["started_monotonic_ns"])
       / 1_000_000 <= trial.get("recovery_deadline_ms", 0),
    {"cancellation": cancellation, "custody": custody,
     "recovery_poll_return_ns": recovered_poll.get("returned_monotonic_ns"),
     "cancel_start_ns": cancel.get("started_monotonic_ns"),
     "recovery_ms": ((recovered_poll["returned_monotonic_ns"]
         - cancel["started_monotonic_ns"]) / 1_000_000
         if type(recovered_poll.get("returned_monotonic_ns")) is int
         and type(cancel.get("started_monotonic_ns")) is int else None)})
check("independent_readback_confirms_same_generation_q_up",
    readback.get("status") == "observed"
    and readback.get("generation_before") == generation
    and readback.get("generation_after") == generation
    and readback.get("q_down") is False
    and readback.get("process_retired") is True
    and type(readback.get("started_monotonic_ns")) is int
    and readback["started_monotonic_ns"] >= down.get("callback_return_ns", 2**63)
    and not RAW.get("emergency_q_up"),
    {"readback": readback, "callback_return_ns": down.get("callback_return_ns"),
     "emergency_q_up": RAW.get("emergency_q_up")})
check("exact_task_effect_and_host_cleanup_are_preserved",
    RAW.get("effect_readback") == trial.get("expected_effect")
    and fixture.get("effect") == trial.get("expected_effect")
    and RAW.get("hook_stopped", {}).get("thread_exited") is True
    and fixture.get("exit_code") == 0
    and fixture.get("window_exists_after_exit") is False
    and RAW.get("foreground_restore", {}).get("restored") is True,
    {"effect": RAW.get("effect_readback"), "fixture_exit": fixture.get("exit_code"),
     "window_exists_after_exit": fixture.get("window_exists_after_exit"),
     "hook_stopped": hook.get("thread_exited"),
     "foreground_restore": RAW.get("foreground_restore")})

retained = RAW.get("retained_report") or {}
action = (retained.get("supervision") or {}).get("action") or {}
close = (RAW.get("public_close") or {}).get("response") or {}
check("terminal_action_gap_is_explicitly_retained",
    action.get("status") == "running"
    and close.get("status") == "closed"
    and close.get("release_confirmed") is False
    and retained.get("task_success") is None,
    {"retained_action_status": action.get("status"),
     "close_status": close.get("status"),
     "close_release_confirmed": close.get("release_confirmed"),
     "task_success": retained.get("task_success")})

passed = sum(row["passed"] for row in checks)
result = {"schema": "win32-supervised-standard-caller-r22-supplement-v1",
    "attempt_id": CONDITIONS.get("attempt_id"), "raw_sha256": raw_hash,
    "frozen_audit_sha256": hashlib.sha256((HERE / "audit.json").read_bytes()).hexdigest(),
    "status": "PARTIAL" if passed == len(checks) else "FAIL_OR_UNKNOWN",
    "checks_passed": passed, "checks_total": len(checks), "checks": checks,
    "limited_finding": "One 250ms callback hold produced a public recovered/release-confirmed receipt and independent same-generation Q-up after callback return; the retained dispatch action still says running, and session close reports release_confirmed=false.",
    "overall_task_success": None,
    "audit_correction": "The frozen audit's two failures read callback_return_ns from hook_trace_after_release, a snapshot taken before the callback thread stored the return time. This supplement uses the final hook event row and hook_stopped snapshot; audit.json is unchanged."}
(HERE / "audit_supplement.json").write_text(
    json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({"status": result["status"], "checks_passed": passed,
                  "checks_total": len(checks), "raw_sha256": raw_hash}, sort_keys=True))
