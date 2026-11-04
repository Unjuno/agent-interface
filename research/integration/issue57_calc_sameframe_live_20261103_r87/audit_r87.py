"""Read-only gate audit for the one-shot r87 Calc attempt."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
ATTEMPT = ROOT / "r87-c11"


def read(name):
    path = ATTEMPT / name
    return json.loads(path.read_text(encoding="utf-8"))


def empty(value):
    return value in (None, "", [], {})


def main():
    gates = {}
    errors = {}
    result = read("result.json")
    compiled = read("compiled-result.json")
    prepare = read("prepare.json")
    descriptor = compiled.get("task_artifact_admission") or {}
    request = compiled.get("task_save_request") or {}
    method = compiled.get("method_receipt") or {}
    observations = method.get("observations") or []
    events = method.get("critical_events") or []
    transitions = method.get("transitions") or []
    save_events = [e for e in events if e.get("event") == "effect_checked"
                   and e.get("action") == "save"]
    save_event = save_events[0] if len(save_events) == 1 else {}

    gates["two_transitions_enter_save_released"] = (
        len(transitions) == 2
        and [row.get("action") for row in transitions] == ["enter", "save"]
        and all(row.get("release_verified") is True for row in transitions)
    )
    if len(observations) >= 2:
        gates["same_digest_across_final_save_observation"] = (
            observations[-1].get("evidence_digest") == observations[-2].get("evidence_digest")
        )
    else:
        gates["same_digest_across_final_save_observation"] = False
    gates["same_frame_save_effect_callback_recorded"] = (
        method.get("outcome") == "SAFE_YIELD"
        and method.get("reason") == "effect_unavailable"
        and [e.get("event") for e in events] == [
            "branch_selected", "action_terminal", "effect_checked",
            "branch_selected", "action_terminal", "effect_checked",
            "runtime_finished",
        ]
        and save_event.get("status") == "unavailable"
        and type(save_event.get("effect_verification_started_ns")) is int
        and type(save_event.get("effect_verification_accepted_ns")) is int
        and save_event["effect_verification_started_ns"]
            <= request.get("save_request_monotonic_ns", -1)
            <= save_event["effect_verification_accepted_ns"]
    )
    root_call_id = prepare.get("call_id")
    gates["single_call_and_generation_bound_save_request"] = (
        request.get("schema") == "agent-interface/calc-task-save-request-v1"
        and request.get("attempt_id") == "issue57-r87-c11"
        and request.get("call_id") == root_call_id
        and request.get("call_id") == descriptor.get("call_id")
        and request.get("process_generation") == descriptor.get("process_generation")
        and request.get("window_generation") == descriptor.get("window_generation")
        and bool(request.get("save_request_id"))
    )

    preclose = read("artifact-read-before-close.json")
    verified = read("verify-task.json")
    effect = verified.get("task_effect") or {}
    parsed = effect.get("parsed_effect") or {}
    controller = effect.get("save_controller") or {}
    method_hash = hashlib.sha256(json.dumps(
        method, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")).hexdigest()
    gates["preclose_artifact_exact_731_864"] = (
        preclose.get("status") == "verified"
        and preclose.get("task_success") is True
        and preclose.get("cells") == {"A1": "731", "A2": "864"}
    )
    gates["postclose_parent_verifier_same_artifact"] = (
        verified.get("status") == "verified"
        and verified.get("task_success") is True
        and parsed.get("status") == "verified"
        and parsed.get("task_success") is True
        and parsed.get("cells") == {"A1": "731", "A2": "864"}
        and effect.get("artifact_sha256") == preclose.get("artifact_sha256")
        and effect.get("save_request_id") == request.get("save_request_id")
        and controller.get("schema") == "agent-interface/calc-registered-save-controller-v1"
        and controller.get("call_id") == root_call_id
        and controller.get("attempt_id") == "issue57-r87-c11"
        and controller.get("process_generation") == request.get("process_generation")
        and controller.get("window_generation") == request.get("window_generation")
        and controller.get("save_request_id") == request.get("save_request_id")
        and controller.get("save_action_id") == save_event.get("action_id")
        and controller.get("method_receipt_sha256") == method_hash
    )

    close = read("close.json")
    release = close.get("release") or {}
    lifecycle = close.get("calc_target_lifecycle") or []
    life = lifecycle[0] if len(lifecycle) == 1 else {}
    target_exit = life.get("target_process_exit_receipt") or {}
    cleanup = life.get("process_group_cleanup") or {}
    gates["owner_release_empty_and_exit_zero"] = (
        close.get("status") == "closed"
        and close.get("verified") is True
        and close.get("release_confirmed") is True
        and empty(release.get("keys_down"))
        and empty(release.get("buttons_down"))
        and close.get("owner_process_exitcode") == 0
    )
    gates["target_and_launcher_natural_exit_zero"] = (
        target_exit.get("status") == "exited"
        and target_exit.get("verified") is True
        and target_exit.get("exit_code") == 0
        and target_exit.get("launcher_exit_code") == 0
        and cleanup.get("clean_exit_verified") is True
    )
    gates["parent_result_task_success_and_no_replay"] = (
        result.get("task_success") is True
        and result.get("release_confirmed") is True
        and result.get("replay_allowed") is False
        and result.get("action_transition_count") == 2
    )

    artifact_path = Path(prepare["artifact_path"])
    # The container path is rooted under /evidence; map its suffix to the host packet.
    suffix = Path(*artifact_path.parts[2:]) if artifact_path.is_absolute() else artifact_path
    host_artifact = ROOT / "r87-c11" / "server-output" / suffix
    if not host_artifact.is_file():
        # The saved artifact path can include the r87-c11 segment already.
        host_artifact = ATTEMPT / "server-output" / prepare["call_id"] / "task-artifact.fods"
    digest = hashlib.sha256(host_artifact.read_bytes()).hexdigest() if host_artifact.is_file() else None
    gates["raw_fods_hash_matches_parent_verifier"] = (
        digest is not None and digest == effect.get("artifact_sha256")
    )

    exit_receipt = read("docker-exit-code.json")
    gates["container_exit_zero"] = exit_receipt.get("exit_code") == 0
    failed = [name for name, passed in gates.items() if not passed]
    report = {
        "schema": "agent-interface/issue57-r87-sameframe-live-audit-v1",
        "attempt_id": "issue57-r87-c11",
        "status": "PASS_SCOPED" if not failed else "FAIL_OR_UNKNOWN",
        "gates": gates,
        "failed_gates": failed,
        "method_outcome": method.get("outcome"),
        "method_reason": method.get("reason"),
        "artifact_sha256": digest,
        "task_cells": parsed.get("cells"),
        "limitations": [
            "one local Docker/Xvfb Calc task; no provider or model call",
            "not a token, price, latency-comparison, WSLc, MAP01, or broad-reliability result",
        ],
    }
    (ROOT / "audit.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n",
                                      encoding="utf-8")
    print(json.dumps(report, sort_keys=True, indent=2))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())



