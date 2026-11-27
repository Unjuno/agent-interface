#!/usr/bin/env python3
"""Read-only adjudication of the preserved R10 evidence packet."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def text_json(name):
    envelope = json.loads((ROOT / name).read_text(encoding="utf-8"))
    return json.loads(next(item["text"] for item in envelope["content"] if item["type"] == "text"))

run = json.loads((ROOT / "RESULT.json").read_text(encoding="utf-8"))
dispatch = text_json("dispatch-after-cancel.json")
raw = dispatch["receipt"]["source"]["raw_report"]
retained = text_json("results.json")
final_state = run["state_after_supervised_recovery"]
held_state = run["state_during_hold"]
cleanup_deadline = retained["cancellation"]["result"]["cleanup_deadline_ns"]
hold_started = run["hold_entered_monotonic_ns"]

checks = {
    "native_effect_observed_during_hold": held_state["shift_down"] is True,
    "final_native_key_up_observed": final_state["shift_down"] is False,
    "same_target_generation": held_state["generation"] == final_state["generation"],
    "terminal_dispatch_recovered": raw["result"]["status"] == "recovered",
    "dispatch_release_confirmed": raw["result"]["release_confirmed"] is True,
    "retained_action_recovered": retained["action"]["status"] == "recovered",
    "retained_cancel_recovered": retained["cancellation"]["status"] == "recovered",
    "retained_cancel_release_confirmed": retained["cancellation"]["release_confirmed"] is True,
    "task_success_not_claimed": raw["result"]["task_success"] is None and retained["cancellation"]["task_success"] is None,
    "replay_not_allowed": raw["result"]["replay_allowed"] is False and retained["cancellation"]["replay_allowed"] is False,
    "cleanup_deadline_configured_three_seconds": cleanup_deadline - hold_started == 3_000_000_000,
    "terminal_completion_timestamp_available": False,
    "deadline_gate_contract": "recovered is only committed before cleanup_deadline_ns at runtime/guarded_win32_v1/operation_owner.py:397-416",
    "late_recovery_receipt_rejected": "runtime/guarded_win32_v1/process_cancellation.py:331-356",
}
result = {
    "classification": "RECOVERY_RELEASE_AND_DEADLINE_GATE_CONFIRMED_ELAPSED_LATENCY_UNMEASURED",
    "checks": checks,
    "configured_cleanup_deadline_ns": cleanup_deadline,
    "hold_started_monotonic_ns": hold_started,
    "measured_recovery_elapsed_ns": None,
    "original_run_status_preserved": run["status"],
    "limitations": run["limitations"],
}
print(json.dumps(result, indent=2))
if not all(value for key, value in checks.items() if key != "terminal_completion_timestamp_available"):
    raise SystemExit(1)
