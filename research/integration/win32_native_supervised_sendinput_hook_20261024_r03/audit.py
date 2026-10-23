"""Independent read-only audit of the single native supervisor run."""
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
EXPECTED_CONDITIONS = "13233cc44e899994c718e436f35f9e1b1d578d7331f5ebd751a3e56b49b78938"
EXPECTED_SOURCES = {
    "probe.py": "72037b78c32e36f840bcd7378a016e375c85061ad82ee8acb18afeeed38c4865",
    "runtime/backends/win32_v1/backend.py": "7d936a1cff39b38ec695eb97c90c706f38c91b650faa9adf3c6950270a5334e0",
    "runtime/guarded_win32_v1/operation_owner.py": "3a3d868510d1c41250516aacaddac9daed428a7eab72ca336d3b9684c90ba342",
    "runtime/guarded_win32_v1/process_cancellation.py": "49202af88ced51a73c4218d113f118a57ad9f63f73fdd3b134cd31f41f9dfec6",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def result_message(trace, role):
    rows = trace.get(role + "_messages", [])
    return next((row for row in rows if isinstance(row, dict)
                 and row.get("operation_id")), None)


def main():
    raw_path = ROOT / "raw.json"
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    condition_hash = digest(ROOT / "conditions.json")
    source_hashes = {name: digest(ROOT / name if name == "probe.py"
                                   else REPO_ROOT / name)
                     for name in EXPECTED_SOURCES}
    raw_hash = digest(raw_path)
    trace = raw.get("helper_trace", {})
    process_trace = raw.get("timed_process_trace", {})
    producer_events = raw.get("producer_events", [])
    hook_entries = [row for row in producer_events if row.get("kind") == "hook_entry"]
    hook_returns = [row for row in producer_events if row.get("kind") == "hook_return"]
    send_returns = [row for row in producer_events if row.get("kind") == "send_down_return"]
    recovery = result_message(trace, "recovery")
    observation = result_message(trace, "observer")
    horizon = raw.get("horizon_observer")
    cancel_started = raw.get("cancel_started_ns")
    cancel_returned = raw.get("cancel_returned_ns")
    exit_observed = process_trace.get("producer_exit_observed_ns")
    release_started = recovery.get("release_started_ns") if recovery else None
    release_returned = recovery.get("release_returned_ns") if recovery else None
    observer_ns = observation.get("observed_ns") if observation else None

    checks = {
        "frozen_conditions_hash": condition_hash == EXPECTED_CONDITIONS,
        "frozen_source_hashes": all(source_hashes[name] == value
                                     for name, value in EXPECTED_SOURCES.items()),
        "one_prestarted_recovery_and_observer": len(raw.get("prestarted_helpers", [])) == 2
            and all(row.get("ready") is True for row in raw.get("prestarted_helpers", [])),
        "real_target_generation_bound": bool(raw.get("target_generation"))
            and len(raw.get("target_generation", "")) == 64
            and raw.get("target_generation_after") == raw.get("target_generation"),
        "producer_target_generation_matched": any(row.get("kind") == "send_down_begin"
            and row.get("target_generation") == raw.get("target_generation")
            for row in producer_events),
        "injected_f13_callback_entered": len(hook_entries) == 1
            and hook_entries[0].get("vk") == 0x7C
            and bool(hook_entries[0].get("flags", 0) & 0x10),
        "producer_did_not_return_from_blocked_sendinput": not hook_returns and not send_returns,
        "producer_exit_confirmed": type(exit_observed) is int
            and raw.get("cleanup", {}).get("producer_retired") is True,
        "cancel_response_at_most_250ms": type(cancel_started) is int
            and type(cancel_returned) is int
            and 0 <= cancel_returned - cancel_started <= 250_000_000,
        "recovery_requested_exactly_once": len([row for row in trace.get("recovery_requests", [])
            if isinstance(row, dict) and row.get("request_id")]) == 1,
        "producer_retired_before_recovery_up": type(exit_observed) is int
            and type(release_started) is int and exit_observed <= release_started,
        "recovery_generation_matches": recovery is not None
            and recovery.get("helper_generation_before") == raw.get("target_generation")
            and recovery.get("helper_generation_after") == raw.get("target_generation"),
        "native_release_verified": recovery is not None
            and recovery.get("release_accepted") is True
            and isinstance(recovery.get("release"), dict)
            and recovery["release"].get("verified") is True,
        "independent_immediate_readback_up": observation is not None
            and observation.get("neutral") is True
            and observation.get("f13_down") is False
            and observation.get("helper_generation_before") == raw.get("target_generation")
            and observation.get("helper_generation_after") == raw.get("target_generation"),
        "recovery_within_2500ms": type(cancel_started) is int
            and type(release_returned) is int
            and 0 <= release_returned - cancel_started <= 2_500_000_000,
        "owner_recovered_and_kept_task_unknown": raw.get("owner_terminal", {}).get("status") == "recovered"
            and raw.get("owner_terminal", {}).get("release_confirmed") is True
            and raw.get("task_success") is None
            and raw.get("replay_allowed") is False,
        "late_state_observer_after_1500ms": isinstance(horizon, dict)
            and isinstance(observer_ns, int)
            and type(horizon.get("observed_ns")) is int
            and horizon["observed_ns"] >= observer_ns + 1_500_000_000
            and horizon.get("neutral") is True
            and horizon.get("f13_down") is False
            and horizon.get("target_generation_before") == raw.get("target_generation")
            and horizon.get("target_generation_after") == raw.get("target_generation"),
        "no_emergency_release_required": raw.get("cleanup", {}).get("emergency_release_attempted") is False,
        "cleanup_complete": raw.get("cleanup", {}).get("supervisor_closed") is True
            and raw.get("cleanup", {}).get("supervisor_thread_exited") is True
            and raw.get("cleanup", {}).get("producer_retired") is True
            and raw.get("cleanup", {}).get("fixture_destroyed") is True
            and raw.get("cleanup", {}).get("backend_close", {}).get("status") == "closed",
        "no_runner_errors": raw.get("errors") == [],
    }
    evidence_missing = any(value is None for value in (
        raw.get("target_generation"), exit_observed, release_started,
        release_returned, recovery, observation, horizon))
    if all(checks.values()):
        disposition = "PASS"
    elif evidence_missing or not checks["frozen_conditions_hash"] or not checks["frozen_source_hashes"]:
        disposition = "UNKNOWN"
    else:
        disposition = "FAIL"
    audit = {
        "packet": raw.get("packet"), "disposition": disposition,
        "method": "independent read-only hashes, IPC receipts, process timing, runtime release receipt, and backend state readback",
        "hashes": {"conditions.json": condition_hash, "raw.json": raw_hash,
                   "audit.py": digest(ROOT / "audit.py"), **source_hashes},
        "checks": checks,
        "measurements": {
            "callback_entry_ns": hook_entries[0].get("callback_entry_ns") if hook_entries else None,
            "cancel_response_ms": raw.get("cancel_response_ms"),
            "producer_exit_observed_ns": exit_observed,
            "recovery_up_started_ns": release_started,
            "recovery_up_returned_ns": release_returned,
            "independent_readback_ns": observer_ns,
            "horizon_observer_ns": horizon.get("observed_ns") if isinstance(horizon, dict) else None,
            "recovery_elapsed_ms": ((release_returned - cancel_started) / 1e6
                if isinstance(release_returned, int) and isinstance(cancel_started, int) else None),
        },
        "scope": "one Windows host and one finite WH_KEYBOARD_LL callback-stall schedule; no standard public caller or task-effect qualification",
    }
    out = ROOT / "audit.json"
    with out.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(audit, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps(audit, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
