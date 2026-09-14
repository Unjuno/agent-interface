"""Validate and score the finite Issue #57 three-arm live trace."""

from __future__ import annotations

import copy


ARMS = ("plain", "ephemeral", "persistent")
TASKS = tuple(f"task-{index}" for index in range(1, 7))
LAYOUTS = ("A", "A", "A", "B", "B", "B")
EXPECTED_MODEL_CALLS = {"plain": (1, 1, 1, 1, 1, 1),
                        "ephemeral": (1, 1, 1, 1, 1, 1),
                        "persistent": (1, 0, 0, 1, 0, 0)}
EXPECTED_ROUTES = {"plain": ("cold",) * 6,
                   "ephemeral": ("cold",) * 6,
                   "persistent": ("cold", "reuse", "reuse", "repair", "reuse", "reuse")}
USAGE_FIELDS = ("input_tokens", "cached_input_tokens", "cache_write_input_tokens",
                "output_tokens", "reasoning_output_tokens")


def _integer(value) -> bool:
    return type(value) is int and value >= 0


def validate_task(row: dict, arm: str, index: int) -> dict:
    required = {
        "arm", "task_id", "layout", "route", "model_calls", "planner_generations",
        "model_visible_images", "local_observations", "durable_calls",
        "pointer_admissions", "old_target_pointer_admissions", "releases_verified",
        "submission_count", "exact_submission", "typed_outcome", "elapsed_ns",
        "source_to_completion_ns", "input_feedback_ns", "repair",
    }
    if type(row) is not dict or set(row) != required:
        raise ValueError("exact task trace fields required")
    if row["arm"] != arm or row["task_id"] != TASKS[index] or row["layout"] != LAYOUTS[index]:
        raise ValueError("task identity/order/layout mismatch")
    if row["route"] != EXPECTED_ROUTES[arm][index]:
        raise ValueError("route differs from frozen arm schedule")
    calls = row["model_calls"]
    if type(calls) is not list or len(calls) != EXPECTED_MODEL_CALLS[arm][index]:
        raise ValueError("model call count differs from frozen arm schedule")
    seen = set()
    for call in calls:
        if type(call) is not dict or set(call) != {
                "call_id", "stage", "requested_model", "requested_effort", "usage"}:
            raise ValueError("exact model call record required")
        if not all(type(call[key]) is str and call[key] for key in
                   ("call_id", "stage", "requested_model", "requested_effort")):
            raise ValueError("model identity fields required")
        if call["call_id"] in seen:
            raise ValueError("duplicate model call id")
        seen.add(call["call_id"])
        usage = call["usage"]
        if type(usage) is not dict or set(usage) != set(USAGE_FIELDS):
            raise ValueError("complete model usage required")
        if any(not _integer(usage[field]) for field in USAGE_FIELDS):
            raise ValueError("nonnegative model usage required")
        if usage["cached_input_tokens"] > usage["input_tokens"]:
            raise ValueError("cached input must be a subset of input")
    for field in ("planner_generations", "model_visible_images", "local_observations",
                  "durable_calls", "pointer_admissions", "old_target_pointer_admissions",
                  "submission_count", "elapsed_ns"):
        if not _integer(row[field]):
            raise ValueError("nonnegative integer required for " + field)
    if row["planner_generations"] != len(calls) or row["model_visible_images"] != len(calls):
        raise ValueError("each planned model call must be one image-backed generation")
    if type(row["releases_verified"]) is not bool or type(row["exact_submission"]) is not bool:
        raise ValueError("boolean correctness fields required")
    if row["typed_outcome"] not in {"completed", "safe_stop", "failed"}:
        raise ValueError("typed task outcome required")
    for field in ("source_to_completion_ns", "input_feedback_ns"):
        value = row[field]
        if value is not None and not _integer(value):
            raise ValueError("optional timing must be nonnegative integer")
    repair = row["repair"]
    if type(repair) is not dict or set(repair) != {
            "required", "old_reference_status", "old_reference_pointer_admissions",
            "attempted", "succeeded"}:
        raise ValueError("exact repair record required")
    if any(type(repair[key]) is not bool for key in ("required", "attempted", "succeeded")):
        raise ValueError("boolean repair fields required")
    if not _integer(repair["old_reference_pointer_admissions"]):
        raise ValueError("repair pointer admission count required")
    expected_repair = arm == "persistent" and index == 3
    if repair["required"] != expected_repair:
        raise ValueError("repair requirement differs from frozen schedule")
    if expected_repair:
        if (repair["old_reference_status"] not in {"missing", "stale", "association_changed"}
                or repair["old_reference_pointer_admissions"] != 0
                or not repair["attempted"]):
            raise ValueError("repair must first refuse old references without pointer input")
    else:
        if repair != {"required": False, "old_reference_status": None,
                      "old_reference_pointer_admissions": 0,
                      "attempted": False, "succeeded": False}:
            raise ValueError("repair evidence is only allowed at persistent task-4")
    return copy.deepcopy(row)


def evaluate(trace: dict) -> dict:
    if type(trace) is not dict or set(trace) != {"schema", "arms"}:
        raise ValueError("exact comparison trace required")
    if trace["schema"] != "integrated_efficiency_trace_v1":
        raise ValueError("unsupported trace schema")
    if type(trace["arms"]) is not dict or tuple(trace["arms"].keys()) != ARMS:
        raise ValueError("arms must be in frozen plain/ephemeral/persistent order")
    arms = {}
    global_call_ids = set()
    for arm in ARMS:
        rows = trace["arms"][arm]
        if type(rows) is not list or len(rows) != 6:
            raise ValueError("exact six-task arm required")
        checked = [validate_task(row, arm, index) for index, row in enumerate(rows)]
        for row in checked:
            for call in row["model_calls"]:
                if call["call_id"] in global_call_ids:
                    raise ValueError("duplicate model call id across comparison")
                global_call_ids.add(call["call_id"])
        cumulative_tokens = []
        cumulative_generations = []
        token_total = generation_total = 0
        for row in checked:
            token_total += sum(call["usage"]["input_tokens"] for call in row["model_calls"])
            generation_total += row["planner_generations"]
            cumulative_tokens.append(token_total)
            cumulative_generations.append(generation_total)
        arms[arm] = {
            "tasks": checked,
            "correct": all(row["typed_outcome"] == "completed"
                           and row["submission_count"] == 1
                           and row["exact_submission"]
                           and row["releases_verified"] for row in checked),
            "cumulative_input_tokens": cumulative_tokens,
            "cumulative_planner_generations": cumulative_generations,
            "elapsed_ns": sum(row["elapsed_ns"] for row in checked),
            "old_target_pointer_admissions": sum(
                row["old_target_pointer_admissions"] for row in checked),
        }
    persistent = arms["persistent"]
    repair = persistent["tasks"][3]["repair"]
    safety = (persistent["correct"] and persistent["old_target_pointer_admissions"] == 0
              and repair["succeeded"])
    break_even = None
    for index in range(6):
        if (persistent["cumulative_input_tokens"][index]
                < arms["plain"]["cumulative_input_tokens"][index]
                and persistent["cumulative_input_tokens"][index]
                < arms["ephemeral"]["cumulative_input_tokens"][index]):
            break_even = index + 1
            break
    beats_tokens = all(persistent["cumulative_input_tokens"][-1]
                       < arms[arm]["cumulative_input_tokens"][-1]
                       for arm in ("plain", "ephemeral"))
    beats_generations = all(persistent["cumulative_planner_generations"][-1]
                            < arms[arm]["cumulative_planner_generations"][-1]
                            for arm in ("plain", "ephemeral"))
    if not safety:
        disposition = "REJECT"
        reason = "persistent_correctness_repair_or_old_target_gate_failed"
    elif not all(arms[arm]["correct"] for arm in ARMS):
        disposition = "HOLD"
        reason = "reference_arm_comparability_failed"
    elif beats_tokens and beats_generations and break_even is not None and break_even <= 4:
        disposition = "RETAIN"
        reason = "frozen_efficiency_and_correctness_gates_passed"
    else:
        disposition = "REJECT"
        reason = "frozen_token_generation_or_break_even_gate_failed"
    return {
        "schema": "integrated_efficiency_evaluation_v1",
        "arms": arms,
        "observed_break_even_task": break_even,
        "beats_both_input_tokens_by_task_6": beats_tokens,
        "beats_both_planner_generations_by_task_6": beats_generations,
        "persistent_faster_than_both_descriptive": all(
            persistent["elapsed_ns"] < arms[arm]["elapsed_ns"]
            for arm in ("plain", "ephemeral")),
        "disposition": disposition,
        "reason": reason,
    }
