"""Project v3 caller results into the frozen Issue #57 task-trace contract.

The adapter is intentionally partial: if a v3 result cannot satisfy every
legacy comparison field without dropping an attempt or inventing usage, it
returns HOLD with the complete source envelope and no projected task row.
"""
from __future__ import annotations

import copy

try:
    from .integrated_efficiency_protocol_v1 import (
        EXPECTED_MODEL_CALLS, EXPECTED_ROUTES, LAYOUTS, TASKS, evaluate,
        validate_task,
    )
except ImportError:
    from integrated_efficiency_protocol_v1 import (
        EXPECTED_MODEL_CALLS, EXPECTED_ROUTES, LAYOUTS, TASKS, evaluate,
        validate_task,
    )


USAGE_FIELDS = ("input_tokens", "cached_input_tokens", "cache_write_input_tokens",
                "output_tokens", "reasoning_output_tokens")
TERMINAL_MAP = {"TASK_SUCCEEDED": "completed", "SAFE_STOP": "safe_stop",
                "TASK_NOT_VERIFIED": "failed", "EXECUTION_INCOMPLETE": "failed",
                "CALLER_FAILED": "failed", "TASK_DEFERRED": "failed"}


def _hold(arm, index, task_id, route, caller_result, independent, telemetry, reason):
    return {"schema": "issue57-v3-task-projection-v1", "status": "HOLD",
            "reason": reason, "arm": arm, "task_index": index,
            "task_id": task_id, "route": route,
            "caller_result": copy.deepcopy(caller_result),
            "independent_score": copy.deepcopy(independent),
            "telemetry": copy.deepcopy(telemetry), "task_row": None}


def project_task(arm, index, caller_result, independent_score, telemetry):
    """Return a strict v1 task row or a fail-closed HOLD retaining all input.

    ``telemetry`` requires the existing runner's locally measured fields:
    local observations, durable calls, pointer admissions, release state,
    source-to-completion timing, per-input feedback, and repair receipt.
    """
    if arm not in EXPECTED_MODEL_CALLS or type(index) is not int or not 0 <= index < 6:
        raise ValueError("known frozen arm and task index required")
    task_id, layout, route = TASKS[index], LAYOUTS[index], EXPECTED_ROUTES[arm][index]
    if type(caller_result) is not dict:
        return _hold(arm, index, task_id, route, caller_result,
                     independent_score, telemetry, "public_v3_result_missing")
    if type(telemetry) is not dict:
        return _hold(arm, index, task_id, route, caller_result,
                     independent_score, telemetry, "task_telemetry_missing")
    needed = {"local_observations", "durable_calls", "pointer_admissions",
              "old_target_pointer_admissions", "releases_verified", "elapsed_ns",
              "source_to_completion_ns", "input_feedback_ns", "repair"}
    if set(telemetry) != needed:
        return _hold(arm, index, task_id, route, caller_result,
                     independent_score, telemetry, "task_telemetry_incomplete")
    if type(independent_score) is not dict or set(independent_score) != {
            "submission_count", "exact_submission"}:
        return _hold(arm, index, task_id, route, caller_result,
                     independent_score, telemetry, "independent_score_incomplete")

    attempts = caller_result.get("attempt_ledger")
    if type(attempts) is not list:
        return _hold(arm, index, task_id, route, caller_result,
                     independent_score, telemetry, "caller_attempt_ledger_missing")
    accounting = caller_result.get("accounting")
    if type(accounting) is not dict or accounting.get("attempted_calls") != len(attempts):
        return _hold(arm, index, task_id, route, caller_result,
                     independent_score, telemetry, "caller_attempt_count_mismatch")
    expected_calls = EXPECTED_MODEL_CALLS[arm][index]
    if len(attempts) != expected_calls:
        return _hold(arm, index, task_id, route, caller_result,
                     independent_score, telemetry, "assigned_model_attempt_count_mismatch")

    calls = []
    for attempt in attempts:
        if type(attempt) is not dict:
            return _hold(arm, index, task_id, route, caller_result,
                         independent_score, telemetry, "malformed_attempt_row")
        if attempt.get("status") != "completed":
            return _hold(arm, index, task_id, route, caller_result,
                         independent_score, telemetry, "failed_attempt_not_representable_in_v1")
        if any(type(attempt.get(key)) is not str or not attempt[key]
               for key in ("call_id", "stage", "requested_model", "requested_effort")):
            return _hold(arm, index, task_id, route, caller_result,
                         independent_score, telemetry, "attempt_identity_incomplete")
        usage = attempt.get("usage")
        if type(usage) is not dict or set(usage) != set(USAGE_FIELDS) or any(
                type(usage[field]) is not int or usage[field] < 0 for field in USAGE_FIELDS):
            return _hold(arm, index, task_id, route, caller_result,
                         independent_score, telemetry, "usage_incomplete_or_invalid")
        if (usage["cached_input_tokens"] > usage["input_tokens"]
                or usage["reasoning_output_tokens"] > usage["output_tokens"]):
            return _hold(arm, index, task_id, route, caller_result,
                         independent_score, telemetry, "usage_subset_invalid")
        calls.append({"call_id": attempt["call_id"], "stage": attempt["stage"],
            "requested_model": attempt["requested_model"],
            "requested_effort": attempt["requested_effort"], "usage": copy.deepcopy(usage)})

    outcome = caller_result.get("outcome")
    if type(outcome) is not str or outcome not in TERMINAL_MAP:
        return _hold(arm, index, task_id, route, caller_result,
                     independent_score, telemetry, "caller_outcome_unrecognized")
    exact = independent_score["exact_submission"]
    caller_effect = caller_result.get("task_effect")
    if exact is True and (outcome != "TASK_SUCCEEDED" or caller_effect != "succeeded"):
        return _hold(arm, index, task_id, route, caller_result,
                     independent_score, telemetry,
                     "independent_score_caller_success_disagreement")
    if exact is False and (outcome == "TASK_SUCCEEDED" or caller_effect == "succeeded"):
        return _hold(arm, index, task_id, route, caller_result,
                     independent_score, telemetry,
                     "independent_score_caller_failure_disagreement")
    if caller_effect not in {"succeeded", "failed"}:
        return _hold(arm, index, task_id, route, caller_result,
                     independent_score, telemetry,
                     "caller_effect_unavailable_for_frozen_projection")
    task_row = {"arm": arm, "task_id": task_id, "layout": layout, "route": route,
        "model_calls": calls, "planner_generations": len(attempts),
        "model_visible_images": accounting.get("visible_images_submitted"),
        "local_observations": telemetry["local_observations"],
        "durable_calls": telemetry["durable_calls"],
        "pointer_admissions": telemetry["pointer_admissions"],
        "old_target_pointer_admissions": telemetry["old_target_pointer_admissions"],
        "releases_verified": telemetry["releases_verified"],
        "submission_count": independent_score["submission_count"],
        "exact_submission": independent_score["exact_submission"],
        "typed_outcome": TERMINAL_MAP[outcome],
        "elapsed_ns": telemetry["elapsed_ns"],
        "source_to_completion_ns": telemetry["source_to_completion_ns"],
        "input_feedback_ns": copy.deepcopy(telemetry["input_feedback_ns"]),
        "repair": copy.deepcopy(telemetry["repair"])}
    try:
        checked = validate_task(task_row, arm, index)
    except (TypeError, ValueError) as error:
        return _hold(arm, index, task_id, route, caller_result,
                     independent_score, telemetry,
                     "frozen_v1_task_contract_mismatch:" + str(error))
    return {"schema": "issue57-v3-task-projection-v1", "status": "projected",
            "reason": None, "arm": arm, "task_index": index,
            "task_id": task_id, "route": route,
            "caller_result": copy.deepcopy(caller_result),
            "independent_score": copy.deepcopy(independent_score),
            "telemetry": copy.deepcopy(telemetry), "task_row": checked}


def assemble_complete_trace(projected_rows, preflight_calls, integration_discoveries):
    """Build the frozen v1 trace only if all 18 task rows safely project."""
    if type(projected_rows) is not dict:
        raise ValueError("ordered arm mapping required")
    arms = ("plain", "ephemeral", "persistent")
    if tuple(projected_rows) != arms:
        raise ValueError("frozen arm order required")
    if any(type(projected_rows[arm]) is not list or len(projected_rows[arm]) != 6
           for arm in arms):
        raise ValueError("all six assigned task records per arm required")
    held = [row for arm in arms for row in projected_rows[arm]
            if type(row) is not dict or row.get("status") != "projected"
            or row.get("task_row") is None]
    if held:
        return {"status": "HOLD", "reason": "one_or_more_assigned_rows_not_projectable",
                "held_rows": copy.deepcopy(held),
                "all_rows": copy.deepcopy(projected_rows), "trace": None,
                "preflight_calls": copy.deepcopy(preflight_calls),
                "integration_discoveries": copy.deepcopy(integration_discoveries)}
    for arm in arms:
        for index, envelope in enumerate(projected_rows[arm]):
            if (envelope.get("arm") != arm or envelope.get("task_index") != index
                    or envelope.get("task_id") != TASKS[index]
                    or envelope.get("route") != EXPECTED_ROUTES[arm][index]):
                return {"status": "HOLD", "reason": "assigned_row_identity_mismatch",
                    "held_rows": [copy.deepcopy(envelope)],
                    "all_rows": copy.deepcopy(projected_rows), "trace": None,
                    "preflight_calls": copy.deepcopy(preflight_calls),
                    "integration_discoveries": copy.deepcopy(integration_discoveries)}
    trace = {"schema": "integrated_efficiency_trace_v1",
        "arms": {arm: [copy.deepcopy(item["task_row"]) for item in projected_rows[arm]]
                 for arm in arms},
        "preflight_calls": copy.deepcopy(preflight_calls),
        "integration_discoveries": copy.deepcopy(integration_discoveries)}
    try:
        evaluation = evaluate(trace)
    except (TypeError, ValueError) as error:
        return {"status": "HOLD", "reason": "frozen_evaluator_rejected_trace:" + str(error),
                "held_rows": [], "all_rows": copy.deepcopy(projected_rows), "trace": None,
                "preflight_calls": copy.deepcopy(preflight_calls),
                "integration_discoveries": copy.deepcopy(integration_discoveries)}
    return {"status": "ready_for_frozen_evaluator", "reason": None,
            "held_rows": [], "all_rows": copy.deepcopy(projected_rows),
            "trace": trace, "evaluation": evaluation}
