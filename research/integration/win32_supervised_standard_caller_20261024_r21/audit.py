"""Frozen, read-only audit for one bounded standard-caller recovery trial."""
from __future__ import annotations
import json
import hashlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONDITIONS = json.loads((HERE / "conditions.json").read_text(encoding="utf-8"))
RAW = json.loads((HERE / "raw.json").read_text(encoding="utf-8"))
trial = CONDITIONS["trial"]
checks = []

def check(name, passed, evidence=None):
    checks.append({"name": name, "passed": bool(passed), "evidence": evidence})

def row_of(response):
    row = response.get("result") if isinstance(response.get("result"), dict) else response
    return row if isinstance(row, dict) else {}

fixture = RAW.get("fixture", {})
generation = (fixture.get("target_identity") or {}).get("generation")
observation = RAW.get("public_observation", {}).get("raw_report", {})
validation = RAW.get("public_validation", {}).get("response", {})
program = RAW.get("program", {})
cancel = RAW.get("public_cancel", {})
hook = (RAW.get("post_cancel_io_hold") or {}).get("hook_trace_after_release") or {}
hold = RAW.get("post_cancel_io_hold") or {}
producer = RAW.get("producer_identity_from_cancel") or {}
exit_witness = RAW.get("producer_exit_witness") or {}
responses = [item.get("response", {}) for item in RAW.get("result_readbacks", [])]
rows = [row_of(item) for item in responses]
recoveries = [row for row in rows if (row.get("cancellation") or {}).get("status") == "recovered"]
recovered = recoveries[-1] if recoveries else {}
cancellation = recovered.get("cancellation") or {}
owner_result = cancellation.get("result") or {}
recovery_poll = next((item for item in reversed(RAW.get("result_readbacks", []))
    if (row_of(item.get("response", {})).get("cancellation") or {}).get("status")
       == "recovered"), {})
readback = RAW.get("independent_readback") or {}
expected_effect = trial["expected_effect"]

check("attempt_source_and_clean_tracked_tree",
    RAW.get("attempt_id") == CONDITIONS.get("attempt_id")
    and RAW.get("source_commit") == CONDITIONS.get("source_commit")
    and RAW.get("source_tracked_tree_clean") is True,
    {"attempt": RAW.get("attempt_id"), "source_commit": RAW.get("source_commit"),
     "tracked_tree_clean": RAW.get("source_tracked_tree_clean")})
hash_failures = {}
for name, expected in CONDITIONS.get("source_sha256", {}).items():
    source_path = (HERE / name) if name in {"probe.py", "audit.py", "preflight.py"} else (HERE.parents[2] / name)
    try:
        actual = hashlib.sha256(source_path.read_bytes()).hexdigest()
    except OSError:
        actual = None
    if actual != expected:
        hash_failures[name] = {"expected": expected, "actual": actual}
check("frozen_source_hashes_match", not hash_failures, hash_failures)
check("owned_fixture_generation_matches_public_observation",
    fixture.get("pid") == (fixture.get("target_identity", {}).get("owner") or {}).get("pid")
    and isinstance(generation, str) and len(generation) == 64
    and observation.get("target_generation") == generation,
    {"fixture_pid": fixture.get("pid"), "generation": generation,
     "observation_generation": observation.get("target_generation")})
check("one_validated_dispatch_and_one_cancel",
    validation.get("static_valid") is True and validation.get("status") == "valid"
    and RAW.get("dispatch_attempts") == 1
    and program.get("program_id") == trial.get("program_id")
    and program.get("ops") == trial.get("operations")
    and program.get("source", {}).get("target_generations", {}).get("fixture") == generation
    and isinstance(RAW.get("public_cancel"), dict)
    and cancel.get("response", {}).get("status") == "pending"
    and (cancel.get("elapsed_ms") or float("inf")) <= 1000,
    {"validation": validation, "dispatch_attempts": RAW.get("dispatch_attempts"),
     "cancel": cancel.get("response"), "cancel_elapsed_ms": cancel.get("elapsed_ms")})
hook_events = hook.get("events", [])
callback_entry = hook.get("callback_entry_ns")
callback_return = hook.get("callback_return_ns")
hold_ms = ((hold.get("ended_monotonic_ns", 0) - hold.get("started_monotonic_ns", 0))
           / 1_000_000 if type(hold.get("ended_monotonic_ns")) is int
           and type(hold.get("started_monotonic_ns")) is int else None)
check("injected_q_callback_was_held_and_forwarded_after_cancel",
    hook.get("vk") == ord("Q") and hook.get("flags", 0) & 0x10
    and type(callback_entry) is int and type(callback_return) is int
    and type(cancel.get("returned_monotonic_ns")) is int
    and callback_return > cancel["returned_monotonic_ns"]
    and hold_ms is not None and hold_ms >= trial.get("post_cancel_hook_hold_ms", 0) - 50
    and hook.get("blocked_q_down_suppressed") is not True
    and any(event.get("message") == 0x0100 and event.get("callback_return_ns")
            and not event.get("suppressed") for event in hook_events),
    {"hold_ms": hold_ms, "callback_entry_ns": callback_entry,
     "callback_return_ns": callback_return, "cancel": cancel,
     "events": hook_events})
check("exact_producer_identity_retired",
    exit_witness.get("status") == "exited"
    and exit_witness.get("pid") == producer.get("pid")
    and exit_witness.get("creation_time_100ns") == producer.get("creation_time_100ns")
    and type(exit_witness.get("observed_monotonic_ns")) is int,
    {"producer": producer, "exit_witness": exit_witness})
recovery_ns = recovery_poll.get("returned_monotonic_ns")
check("public_recovery_receipt_confirms_release_within_bound",
    bool(recovered) and cancellation.get("release_confirmed") is True
    and owner_result.get("release_confirmed") is True
    and cancellation.get("replay_allowed") is False
    and cancellation.get("task_success") is None
    and type(recovery_ns) is int and type(cancel.get("started_monotonic_ns")) is int
    and (recovery_ns - cancel["started_monotonic_ns"]) / 1_000_000
        <= trial.get("recovery_deadline_ms", 0),
    {"cancellation": cancellation, "owner_result": owner_result,
     "recovery_elapsed_ms": ((recovery_ns - cancel["started_monotonic_ns"])/1_000_000
        if type(recovery_ns) is int and type(cancel.get("started_monotonic_ns")) is int else None)})
check("independent_same_generation_q_up_after_callback_return",
    readback.get("status") == "observed"
    and readback.get("generation_before") == generation
    and readback.get("generation_after") == generation
    and readback.get("q_down") is False
    and readback.get("process_retired") is True
    and type(callback_return) is int
    and type(readback.get("started_monotonic_ns")) is int
    and readback["started_monotonic_ns"] >= callback_return
    and not RAW.get("emergency_q_up"),
    {"readback": readback, "callback_return_ns": callback_return,
     "emergency_cleanup": RAW.get("emergency_q_up")})
check("exact_fixture_effect_is_independently_retained",
    RAW.get("effect_readback") == expected_effect
    and fixture.get("effect") == expected_effect,
    {"effect_readback": RAW.get("effect_readback"), "fixture_effect": fixture.get("effect"),
     "expected": expected_effect})
close_rows = RAW.get("public_close_attempts", [])
close_statuses = [item.get("response", {}).get("status") for item in close_rows]
check("fixture_hook_and_foreground_cleanup",
    fixture.get("exit_code") == 0 and fixture.get("window_exists_after_exit") is False
    and RAW.get("hook_stopped", {}).get("thread_exited") is True
    and RAW.get("foreground_restore", {}).get("restored") is True
    and bool(close_statuses) and close_statuses[-1] == "closed",
    {"fixture": fixture, "hook_stopped": RAW.get("hook_stopped"),
     "foreground_restore": RAW.get("foreground_restore"),
     "close_statuses": close_statuses,
     "session_close_report": RAW.get("session_close_report")})

passed = sum(item["passed"] for item in checks)
result = {"schema": "win32-supervised-standard-caller-r21-audit-v1",
    "attempt_id": CONDITIONS.get("attempt_id"),
    "source_commit": CONDITIONS.get("source_commit"),
    "status": "PASS" if passed == len(checks) else "FAIL_OR_UNKNOWN",
    "passed": passed, "total": len(checks), "checks": checks,
    "claim_scope": "one finite 250ms standard-caller callback hold; no release while callback is blocked"}
(HERE / "audit.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                                 encoding="utf-8")
print(json.dumps({"status": result["status"], "passed": passed,
                  "total": len(checks)}, sort_keys=True))
