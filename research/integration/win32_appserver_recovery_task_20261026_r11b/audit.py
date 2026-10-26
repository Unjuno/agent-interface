"""Independent preregistration/raw and AppServer-to-recovery Win32 R11 audit."""
import hashlib
import json
from pathlib import Path

PACKET = Path(__file__).resolve().parent
RUN = PACKET / "run"


def verify(path, base):
    errors = []
    rows = path.read_text(encoding="utf-8").splitlines()
    for row in rows:
        expected, relative = row.split("  ", 1)
        target = base / relative
        actual = hashlib.sha256(target.read_bytes()).hexdigest() if target.is_file() else None
        if actual != expected:
            errors.append({"path": relative, "expected": expected, "actual": actual})
    return {"entries": len(rows), "errors": errors}


pretrial = verify(PACKET / "PRETRIAL_SHA256SUMS", PACKET)
raw = verify(RUN / "SHA256SUMS", RUN)
d = json.loads((RUN / "result.json").read_text(encoding="utf-8"))
model = d.get("model_decision") or {}
oracle = d.get("task_oracle") or {}
oracle_receipt = ((oracle.get("task_effect") or {}).get("receipt") or {})
retained = d.get("task_retained_result") or {}
action = retained.get("action") or {}
timing_path = RUN / "effect-verification-audit.json"
timing = json.loads(timing_path.read_text(encoding="utf-8")) if timing_path.is_file() else {}
events = d.get("task_fixture_events") or []
expected_effect = {"saved": True, "text": "office", "clicked": True}
submitted = d.get("submitted_task_program") or {}
ops = submitted.get("ops") or []
pointer = next((op for op in ops if op.get("op") == "pointer_move"), {})
task_checks = d.get("task_phase_checks") or {}
compiled_observations = d.get("compiled_observations") or []
first_compiled_observation = compiled_observations[0] if compiled_observations else {}

checks = {
    "attempt_and_final_classification": d.get("attempt_id") == "win32-appserver-recovery-r11b-20261026" and d.get("classification") == "PASS_RECOVERY_FRESH_GENERATION_TASK",
    "required_python_runtime": d.get("python_version", "").startswith("3.13.14"),
    "bounded_phase1_recovery": ((d.get("recovery_phase") or {}).get("classification") == "PASS_SCOPED_BOUNDED_RECOVERY" and (d.get("recovery_phase") or {}).get("release_confirmed") is True and type((d.get("recovery_phase") or {}).get("cleanup_latency_ns")) is int and 0 <= (d.get("recovery_phase") or {}).get("cleanup_latency_ns") < 3_000_000_000),
    "phase1_same_generation_readback": (d.get("recovery_phase") or {}).get("same_generation_readback_up") is True,
    "old_fixture_retired_before_fresh": d.get("recovery_fixture_exit_code") == 0 and (d.get("fresh_task_preflight") or {}).get("fixture_pid") != (d.get("fresh_task_preflight") or {}).get("previous_fixture_pid"),
    "fresh_generation_differs": ((d.get("fresh_task_preflight") or {}).get("native_identity") or {}).get("target_generation") != (d.get("recovery_phase") or {}).get("old_target_generation"),
    "old_generation_refusal_before_input": ((d.get("stale_generation_probe") or {}).get("refusal_reason") == "TARGET_GENERATION_CHANGED" and (d.get("stale_generation_probe") or {}).get("input_dispatched") is False and (d.get("stale_generation_probe") or {}).get("effect_file_present") is False),
    "real_appserver_turn_and_bounded_coordinate": (model.get("status") == "completed" and model.get("model") == "gpt-6.1-sol" and model.get("effort") == "low" and type((model.get("answer") or {}).get("x")) is int and type((model.get("answer") or {}).get("y")) is int and 24 <= model["answer"]["x"] <= 300 and 24 <= model["answer"]["y"] <= 150),
    "usage_matches_appserver_protocol_journal": (model.get("usage", {}).get("status") == "reported" and model.get("usage_matches_backend_journal") is True),
    "same_generation_after_model_wait": (model.get("grounding_generation") == ((d.get("fresh_task_preflight") or {}).get("native_identity") or {}).get("target_generation") and first_compiled_observation.get("target_generation") == model.get("grounding_generation") and type(first_compiled_observation.get("capture_started_ns")) is int and first_compiled_observation["capture_started_ns"] >= model.get("model_returned_monotonic_ns", -1)),
    "model_coordinate_is_compiled_action_coordinate": (type(pointer.get("x")) is int and type(pointer.get("y")) is int and pointer.get("x") == (model.get("answer") or {}).get("x") and pointer.get("y") == (model.get("answer") or {}).get("y")),
    "one_compiled_standard_action": ((d.get("compiled_task_receipt") or {}).get("outcome") == "TASK_SUCCEEDED" and len((d.get("compiled_task_receipt") or {}).get("standard_action_call_ids", [])) == 1 and (d.get("compiled_task_receipt") or {}).get("standard_action_call_ids", [None])[0] == d.get("task_action_call_id")),
    "action_release_and_native_neutral_readback": d.get("task_action_release_confirmed") is True and action.get("release_confirmed") is True and all((d.get("task_neutral_readback") or {}).get(key) is False for key in ("SHIFT", "CTRL", "S", "left_button")),
    "exact_fixture_effect_and_event_order": d.get("independent_effect") == expected_effect and sum(e.get("kind") == "click" for e in events) == 1 and [e.get("code") for e in events if e.get("kind") == "char"] == list(map(ord, "office")) and sum(e.get("kind") == "save" for e in events) == 1,
    "post_observation_after_dispatch_response": timing.get("status") == "succeeded" and timing.get("post_observation_fresh_after_dispatch_return") is True and type(timing.get("post_observation_capture_started_ns")) is int and timing["post_observation_capture_started_ns"] > timing.get("dispatch_response_returned_ns", -1),
    "independent_oracle_exact_binding": oracle.get("status") == "verified" and oracle.get("task_success") is True and oracle_receipt.get("outcome") == "success" and oracle_receipt.get("oracle_id") == "321a2f10e7784cb3aa71f8d1b5f0721e" and oracle_receipt.get("call_id") == retained.get("call_id") == d.get("task_action_call_id") and oracle_receipt.get("operation_id") == action.get("operation_id") and oracle_receipt.get("target_generation") == ((d.get("fresh_task_preflight") or {}).get("native_identity") or {}).get("target_generation"),
    "cleanup_and_foreground_restoration": ((d.get("cleanup") or {}).get("fixture_exit_code") == 0 and (d.get("cleanup") or {}).get("foreground_before") == (d.get("cleanup") or {}).get("foreground_after_restore") and d.get("appserver_closed") is True),
    "no_wslc_or_docker": d.get("wslc_used") is False and d.get("docker_used") is False,
}

audit = {"attempt_id": d.get("attempt_id"), "classification": d.get("classification"),
    "pretrial_hash_audit": pretrial, "raw_hash_audit": raw,
    "checks": checks, "audit_pass": all(checks.values()) and
        not pretrial["errors"] and not raw["errors"]}
(PACKET / "audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n",
    encoding="utf-8", newline="\n")
print(json.dumps(audit, indent=2, sort_keys=True))
if not audit["audit_pass"]:
    raise SystemExit(1)

