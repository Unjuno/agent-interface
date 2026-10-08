"""Independent raw-event reconstruction for the frozen Mindustry allocation.

This module imports neither the live runner nor its route/controller code. It
accepts only event-level records, reconstructs the inherited trace, and feeds
that trace to the unchanged #1679 decision evaluator. Aggregate task summaries
from a runner are deliberately not accepted by the raw schema.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import argparse
import re
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPOSITORY = next(parent for parent in HERE.parents if (parent / ".git").exists())
LIVE = REPOSITORY / "research" / "live_control"
TASKS = ("A1", "A2", "A3", "B1", "B2", "B3")
LAYOUTS = ("A", "A", "A", "B", "B", "B")
ARMS = ("plain", "ephemeral", "persistent")
ROUTES = {
    "plain": ("cold",) * 6,
    "ephemeral": ("cold",) * 6,
    "persistent": ("cold", "reuse", "reuse", "repair", "reuse", "reuse"),
}
CALL_COUNTS = {
    "plain": (1,) * 6,
    "ephemeral": (1,) * 6,
    "persistent": (1, 0, 0, 1, 0, 0),
}
USAGE_FIELDS = {"input_tokens", "cached_input_tokens", "cache_write_input_tokens",
                "output_tokens", "reasoning_output_tokens"}
SCORE_SCOPE = (
    "one changed-geometry Mindustry placement; no delivery or route-completion claim")
RAW_FIELDS = {"schema", "allocation_id", "source_identity", "model_identity",
              "preflight_events", "arms"}
TASK_FIELDS = {"task_id", "layout", "route", "started_ns", "ended_ns",
               "observation_events", "model_call_events", "durable_call_ids",
               "input_events", "input_feedback_events", "release_events",
               "submission_events", "score_event", "repair_events"}


class RawAuditError(ValueError):
    """Malformed, incomplete, or internally contradictory event evidence."""


def _sha(value: object, *, prefix: str | None = None) -> bool:
    if type(value) is not str:
        return False
    if prefix is not None:
        if not value.startswith(prefix):
            return False
        value = value[len(prefix):]
    return re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _nonnegative(value: object) -> bool:
    return type(value) is int and value >= 0


def _positive(value: object) -> bool:
    return type(value) is int and value > 0


def _load_evaluator():
    path = LIVE / "integrated_efficiency_protocol_v1.py"
    spec = importlib.util.spec_from_file_location("frozen_mindustry_efficiency", path)
    if spec is None or spec.loader is None:
        raise RawAuditError("frozen decision evaluator unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.evaluate


def _validate_source_identity(source: object) -> None:
    fields = {"commit", "preregistration_sha256", "runner_sha256",
              "raw_auditor_sha256", "decision_evaluator_sha256",
              "mod_sha256", "jar_sha256", "save_sha256",
              "container_image_digest"}
    if type(source) is not dict or set(source) != fields:
        raise RawAuditError("exact frozen source/image identity required")
    if type(source["commit"]) is not str or not re.fullmatch(r"[0-9a-f]{40}", source["commit"]):
        raise RawAuditError("full source commit required")
    for field in fields - {"commit", "container_image_digest"}:
        if not _sha(source[field]):
            raise RawAuditError("invalid SHA-256 identity: " + field)
    if not _sha(source["container_image_digest"], prefix="sha256:"):
        raise RawAuditError("immutable container image digest required")


def _validate_usage(usage: object) -> None:
    if type(usage) is not dict or set(usage) != USAGE_FIELDS:
        raise RawAuditError("exact raw model usage fields required")
    if any(not _nonnegative(usage[key]) for key in USAGE_FIELDS):
        raise RawAuditError("raw usage must be nonnegative integers")
    if usage["cached_input_tokens"] > usage["input_tokens"]:
        raise RawAuditError("cached input exceeds input tokens")


def _validate_preflight(events: object, model: dict) -> dict:
    if type(events) is not list or len(events) != len(ARMS):
        raise RawAuditError("exactly one raw preflight event per arm required")
    result = {}
    for event in events:
        required = {"arm", "call_id", "stage", "requested_model",
                    "requested_effort", "usage", "image_count"}
        if type(event) is not dict or set(event) != required:
            raise RawAuditError("exact preflight event fields required")
        arm = event["arm"]
        if arm not in ARMS or arm in result:
            raise RawAuditError("preflight arm missing, duplicate, or unknown")
        if (type(event["call_id"]) is not str or not event["call_id"]
                or event["stage"] != "schema_preflight"
                or event["requested_model"] != model["requested_model"]
                or event["requested_effort"] != model["requested_effort"]
                or event["image_count"] != 0):
            raise RawAuditError("preflight identity/stage/image contract mismatch")
        _validate_usage(event["usage"])
        result[arm] = {key: event[key] for key in
                       ("call_id", "stage", "requested_model", "requested_effort", "usage")}
        result[arm]["model_visible_images"] = event["image_count"]
    if tuple(result) != ARMS:
        raise RawAuditError("preflight events must preserve frozen arm order")
    return result


def _score_passes(score: object) -> bool:
    fields = {"status", "contract_satisfied", "wrong_target", "collateral_tiles",
              "source_preserved", "core_preserved", "copper_delta",
              "paused_idle_completion", "guard_tiles", "scope", "checked_ns"}
    if type(score) is not dict or set(score) != fields:
        raise RawAuditError("exact independent score event required")
    if score["status"] not in {"VERIFIED", "SAFE_STOP", "FAILED"}:
        raise RawAuditError("unknown independent score status")
    if (type(score["contract_satisfied"]) is not bool
            or type(score["wrong_target"]) is not bool
            or type(score["source_preserved"]) is not bool
            or type(score["core_preserved"]) is not bool
            or type(score["paused_idle_completion"]) is not bool
            or type(score["collateral_tiles"]) is not list
            or type(score["copper_delta"]) is not int
            or type(score["guard_tiles"]) is not int
            or not _positive(score["checked_ns"])
            or score["scope"] != SCORE_SCOPE):
        raise RawAuditError("invalid independent score evidence types or scope")
    return (score["status"] == "VERIFIED"
            and score["contract_satisfied"] is True
            and score["wrong_target"] is False
            and score["collateral_tiles"] == []
            and score["source_preserved"] is True
            and score["core_preserved"] is True
            and score["copper_delta"] == -1
            and score["paused_idle_completion"] is True
            and score["guard_tiles"] == 112)


def _reconstruct_task(raw: object, arm: str, index: int,
                      model: dict, global_ids: set[str]) -> dict:
    if type(raw) is not dict or set(raw) != TASK_FIELDS:
        raise RawAuditError("raw task must contain exact event collections; aggregates refused")
    task_id, layout, route = TASKS[index], LAYOUTS[index], ROUTES[arm][index]
    if (raw["task_id"], raw["layout"], raw["route"]) != (task_id, layout, route):
        raise RawAuditError("raw task order/layout/route differs from preregistration")
    started, ended = raw["started_ns"], raw["ended_ns"]
    if not _positive(started) or not _positive(ended) or ended <= started:
        raise RawAuditError("monotonic task start/end interval required")

    observations = raw["observation_events"]
    if type(observations) is not list or not observations:
        raise RawAuditError("at least one raw local observation required")
    by_sequence = {}
    last_capture = -1
    for observation in observations:
        keys = {"sequence", "capture_ns", "image_sha256", "model_visible"}
        if type(observation) is not dict or set(observation) != keys:
            raise RawAuditError("exact observation event required")
        sequence, capture = observation["sequence"], observation["capture_ns"]
        if (not _positive(sequence) or not _positive(capture)
                or sequence in by_sequence or capture < last_capture
                or not _sha(observation["image_sha256"])
                or type(observation["model_visible"]) is not bool
                or not started <= capture <= ended):
            raise RawAuditError("invalid, unordered, or duplicate observation evidence")
        last_capture = capture
        by_sequence[sequence] = observation

    calls = raw["model_call_events"]
    if type(calls) is not list or len(calls) != CALL_COUNTS[arm][index]:
        raise RawAuditError("raw task model-call count differs from frozen schedule")
    normalized_calls = []
    for call in calls:
        fields = {"call_id", "stage", "requested_model", "requested_effort",
                  "usage", "source_sequence", "image_sha256"}
        if type(call) is not dict or set(call) != fields:
            raise RawAuditError("exact model call event required")
        identifier = call["call_id"]
        if (type(identifier) is not str or not identifier or identifier in global_ids
                or call["requested_model"] != model["requested_model"]
                or call["requested_effort"] != model["requested_effort"]
                or type(call["stage"]) is not str or not call["stage"]
                or not _positive(call["source_sequence"]) or not _sha(call["image_sha256"])):
            raise RawAuditError("model call identity/source evidence mismatch")
        global_ids.add(identifier)
        _validate_usage(call["usage"])
        source = by_sequence.get(call["source_sequence"])
        if (source is None or source["model_visible"] is not True
                or source["image_sha256"] != call["image_sha256"]):
            raise RawAuditError("call image does not bind to a model-visible observation")
        normalized_calls.append({key: call[key] for key in
            ("call_id", "stage", "requested_model", "requested_effort", "usage")})
    visible = [item for item in observations if item["model_visible"]]
    if (len(visible) != len(calls)
            or {item["sequence"] for item in visible}
               != {call["source_sequence"] for call in calls}):
        raise RawAuditError("every visible image must bind one-to-one to a model call")

    durable_ids = raw["durable_call_ids"]
    if (type(durable_ids) is not list
            or any(type(value) is not str or not value for value in durable_ids)
            or len(set(durable_ids)) != len(durable_ids)):
        raise RawAuditError("unique durable call IDs required")

    inputs = raw["input_events"]
    if type(inputs) is not list:
        raise RawAuditError("raw input event list required")
    attempts = {}
    admitted = []
    old_admitted = 0
    for event in inputs:
        keys = {"attempt_id", "status", "old_reference", "admission_ns"}
        if type(event) is not dict or set(event) != keys:
            raise RawAuditError("exact input admission event required")
        attempt = event["attempt_id"]
        if type(attempt) is not str or not attempt or attempt in attempts:
            raise RawAuditError("unique input attempt id required")
        if type(event["old_reference"]) is not bool or event["status"] not in {"ADMITTED", "REFUSED"}:
            raise RawAuditError("typed input status and reference age required")
        if event["status"] == "ADMITTED":
            if (not _positive(event["admission_ns"])
                    or not started <= event["admission_ns"] <= ended):
                raise RawAuditError("admitted input needs an in-task monotonic timestamp")
            admitted.append(event)
            old_admitted += int(event["old_reference"])
        elif event["admission_ns"] is not None:
            raise RawAuditError("refused input cannot have an admission timestamp")
        attempts[attempt] = event

    feedback_rows = raw["input_feedback_events"]
    if type(feedback_rows) is not list:
        raise RawAuditError("raw input-feedback events required")
    feedback_by_id = {}
    for row in feedback_rows:
        if type(row) is not dict or set(row) != {"attempt_id", "observed_ns"}:
            raise RawAuditError("exact input feedback event required")
        key, observed = row["attempt_id"], row["observed_ns"]
        if (key not in attempts or attempts[key]["status"] != "ADMITTED"
                or key in feedback_by_id or not _positive(observed)
                or observed < attempts[key]["admission_ns"] or observed > ended):
            raise RawAuditError("feedback must follow exactly one admitted input")
        feedback_by_id[key] = observed

    releases = raw["release_events"]
    if type(releases) is not list:
        raise RawAuditError("raw release event list required")
    release_by_id = {}
    for row in releases:
        keys = {"attempt_id", "released_ns", "button_up", "keys_empty", "receipt_id"}
        if type(row) is not dict or set(row) != keys:
            raise RawAuditError("exact independent release receipt required")
        key = row["attempt_id"]
        if (key not in attempts or attempts[key]["status"] != "ADMITTED"
                or key in release_by_id or not _positive(row["released_ns"])
                or row["released_ns"] < attempts[key]["admission_ns"]
                or row["released_ns"] > ended
                or type(row["button_up"]) is not bool
                or type(row["keys_empty"]) is not bool
                or type(row["receipt_id"]) is not str or not row["receipt_id"]):
            raise RawAuditError("release receipt must bind one admitted input")
        release_by_id[key] = row
    if set(release_by_id) != {row["attempt_id"] for row in admitted}:
        raise RawAuditError("every admitted input requires exactly one release receipt")
    if any(not row["button_up"] or not row["keys_empty"]
           for row in release_by_id.values()):
        releases_verified = False
    else:
        releases_verified = bool(admitted)

    submissions = raw["submission_events"]
    if type(submissions) is not list:
        raise RawAuditError("raw independent submission events required")
    for row in submissions:
        if (type(row) is not dict or set(row) != {"submission_id", "at_ns", "exact_effect"}
                or type(row["submission_id"]) is not str or not row["submission_id"]
                or not _positive(row["at_ns"]) or not started <= row["at_ns"] <= ended
                or type(row["exact_effect"]) is not bool):
            raise RawAuditError("exact independent submission event required")
    if len({row["submission_id"] for row in submissions}) != len(submissions):
        raise RawAuditError("duplicate independent submission event")
    exact_submission = (len(submissions) == 1 and submissions[0]["exact_effect"] is True)

    score = raw["score_event"]
    score_pass = _score_passes(score)
    if not started <= score["checked_ns"] <= ended:
        raise RawAuditError("score event outside task interval")
    if score["status"] == "VERIFIED" and not (score_pass and exact_submission and releases_verified):
        raise RawAuditError("positive private score contradicts raw task/effect/release evidence")
    if score["status"] == "SAFE_STOP" and submissions:
        raise RawAuditError("safe stop cannot contain a task submission")
    typed_outcome = ("completed" if score["status"] == "VERIFIED" else
                     "safe_stop" if score["status"] == "SAFE_STOP" else "failed")

    repairs = raw["repair_events"]
    required_repair = arm == "persistent" and index == 3
    if type(repairs) is not list or len(repairs) != int(required_repair):
        raise RawAuditError("repair events differ from frozen B1-only repair schedule")
    if required_repair:
        repair = repairs[0]
        keys = {"old_reference_status", "old_reference_sequence", "observed_sequence",
                "old_reference_pointer_admitted", "fresh_call_id", "fresh_source_sequence"}
        if type(repair) is not dict or set(repair) != keys:
            raise RawAuditError("exact B1 repair evidence required")
        fresh_call = next((call for call in calls if call["call_id"] == repair["fresh_call_id"]), None)
        if (repair["old_reference_status"] not in {"missing", "stale", "association_changed"}
                or not _positive(repair["old_reference_sequence"])
                or not _positive(repair["observed_sequence"])
                or repair["observed_sequence"] <= repair["old_reference_sequence"]
                or repair["old_reference_pointer_admitted"] is not False
                or not _positive(repair["fresh_source_sequence"])
                or repair["fresh_source_sequence"] <= repair["old_reference_sequence"]
                or old_admitted != 0 or fresh_call is None
                or fresh_call["stage"] != "repair"
                or fresh_call["source_sequence"] != repair["fresh_source_sequence"]):
            raise RawAuditError("B1 repair must refuse old input and bind one fresh repair call")
        old_status = repair["old_reference_status"]
        repair_attempted = True
        repair_succeeded = True
    else:
        if repairs:
            raise RawAuditError("repair evidence is only allowed on persistent B1")
        old_status, repair_attempted, repair_succeeded = None, False, False

    feedback_ns = []
    for event in admitted:
        observed = feedback_by_id.get(event["attempt_id"])
        feedback_ns.append(None if observed is None else observed - event["admission_ns"])
    source_ns = min(item["capture_ns"] for item in observations)
    completion_ns = score["checked_ns"] - source_ns if typed_outcome == "completed" else None
    if completion_ns is not None and completion_ns < 0:
        raise RawAuditError("completion precedes source observation")

    return {
        "arm": arm, "task_id": f"task-{index + 1}", "layout": layout, "route": route,
        "model_calls": normalized_calls, "planner_generations": len(normalized_calls),
        "model_visible_images": len(visible), "local_observations": len(observations),
        "durable_calls": len(durable_ids), "pointer_admissions": len(admitted),
        "old_target_pointer_admissions": old_admitted,
        "releases_verified": releases_verified,
        "submission_count": len(submissions), "exact_submission": exact_submission,
        "typed_outcome": typed_outcome, "elapsed_ns": ended - started,
        "source_to_completion_ns": completion_ns,
        "input_feedback_ns": feedback_ns,
        "repair": {"required": required_repair, "old_reference_status": old_status,
                   "old_reference_pointer_admissions": old_admitted,
                   "attempted": repair_attempted, "succeeded": repair_succeeded},
    }


def reconstruct(raw: object) -> dict:
    """Rebuild the exact frozen evaluator trace from raw event collections."""
    if type(raw) is not dict or set(raw) != RAW_FIELDS:
        raise RawAuditError("exact raw allocation fields required; summary fields are forbidden")
    if (raw["schema"] != "mindustry_three_arm_raw_events_v1"
            or type(raw["allocation_id"]) is not str or not raw["allocation_id"]):
        raise RawAuditError("unsupported raw allocation identity")
    _validate_source_identity(raw["source_identity"])
    model = raw["model_identity"]
    if (type(model) is not dict or set(model) != {"requested_model", "requested_effort"}
            or any(type(model[key]) is not str or not model[key]
                   for key in ("requested_model", "requested_effort"))):
        raise RawAuditError("exact requested model/effort identity required")
    preflight = _validate_preflight(raw["preflight_events"], model)
    arms_raw = raw["arms"]
    if type(arms_raw) is not dict or set(arms_raw) != set(ARMS):
        raise RawAuditError("raw arm records must contain exactly the frozen arms")
    global_ids = {row["call_id"] for row in preflight.values()}
    if len(global_ids) != len(ARMS):
        raise RawAuditError("duplicate preflight call IDs")
    arms = {}
    for arm in ARMS:
        tasks = arms_raw[arm]
        if type(tasks) is not list or len(tasks) != len(TASKS):
            raise RawAuditError("six raw task records required per arm")
        arms[arm] = [_reconstruct_task(task, arm, index, model, global_ids)
                     for index, task in enumerate(tasks)]
    discoveries_path = LIVE / "integrated_efficiency_discoveries_v1.json"
    discoveries = json.loads(discoveries_path.read_text(encoding="utf-8"))
    return {"schema": "integrated_efficiency_trace_v1", "arms": arms,
            "preflight_calls": preflight,
            "integration_discoveries": discoveries}


def audit(raw_bytes: bytes, expected_source_identity: dict | None = None) -> dict:
    """Audit bytes and optionally bind them to a separately frozen identity.

    Without the separately supplied freeze identity this is construction-only:
    internally well-formed self-reported hashes are not source verification.
    """
    digest = hashlib.sha256(raw_bytes).hexdigest()
    try:
        raw = json.loads(raw_bytes)
        trace = reconstruct(raw)
        if expected_source_identity is not None:
            _validate_source_identity(expected_source_identity)
            if raw["source_identity"] != expected_source_identity:
                raise RawAuditError("raw source identity differs from independent freeze")
        result = _load_evaluator()(trace)
        return {"schema": "mindustry_three_arm_raw_audit_v1",
                "audit": ("PASS_RAW_RECONSTRUCTION" if expected_source_identity is not None
                          else "PASS_CONSTRUCTION_ONLY"),
                "source_identity_verified": expected_source_identity is not None,
                "raw_sha256": digest, "errors": [], "evaluation": result,
                "scope": "raw event reconstruction plus frozen #1679 decision; no live claim"}
    except (ValueError, TypeError, KeyError, json.JSONDecodeError) as error:
        return {"schema": "mindustry_three_arm_raw_audit_v1",
                "audit": "HOLD_RAW_RECONSTRUCTION", "raw_sha256": digest,
                "source_identity_verified": False,
                "errors": [str(error)], "evaluation": None,
                "scope": "raw event reconstruction plus frozen #1679 decision; no live claim"}


def audit_file(path: Path, freeze_path: Path) -> dict:
    """Run a formal raw audit against a separately retained identity freeze."""
    freeze = json.loads(Path(freeze_path).read_bytes())
    if type(freeze) is dict and set(freeze) == {"source_identity"}:
        freeze = freeze["source_identity"]
    return audit(Path(path).read_bytes(), expected_source_identity=freeze)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw", type=Path, help="immutable raw allocation JSON")
    parser.add_argument("--freeze", type=Path, required=True,
                        help="separately retained source-identity freeze JSON")
    args = parser.parse_args(argv)
    result = audit_file(args.raw, args.freeze)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if result["audit"] == "PASS_RAW_RECONSTRUCTION" else 1


if __name__ == "__main__":
    raise SystemExit(main())
