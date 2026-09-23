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
DISCOVERY_CLASSES = {"existing_requirement_regression", "interface_mismatch",
                     "integration_capability_gap", "benchmark_setup_accounting_defect"}
REQUIRED_DISCOVERY_IDS = {
    "query_url_outside_runtime_text_alphabet",
    "human_point_vertical_misread",
    "missing_handle_record_sequence_assumption",
    "restyled_field_flat_center_patch",
    "pointer_event_name_mismatch",
    "cross_task_duplicate_call_id_gap",
    "target_alias_prefix_character_mismatch",
    "submission_history_materialized_at_finish",
}


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
    value = row["source_to_completion_ns"]
    if value is not None and not _integer(value):
        raise ValueError("optional completion timing must be nonnegative integer")
    feedback = row["input_feedback_ns"]
    if type(feedback) is not list or len(feedback) != row["pointer_admissions"]:
        raise ValueError("one feedback timing per pointer admission required")
    if any(value is not None and not _integer(value) for value in feedback):
        raise ValueError("feedback timings must be nonnegative integers or unavailable")
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
    if type(trace) is not dict or set(trace) != {
            "schema", "arms", "preflight_calls", "integration_discoveries"}:
        raise ValueError("exact comparison trace required")
    if trace["schema"] != "integrated_efficiency_trace_v1":
        raise ValueError("unsupported trace schema")
    if type(trace["arms"]) is not dict or tuple(trace["arms"].keys()) != ARMS:
        raise ValueError("arms must be in frozen plain/ephemeral/persistent order")
    if type(trace["preflight_calls"]) is not dict or tuple(trace["preflight_calls"].keys()) != ARMS:
        raise ValueError("one ordered preflight allocation per arm required")
    discoveries = trace["integration_discoveries"]
    if type(discoveries) is not list:
        raise ValueError("integration discovery list required")
    discovery_ids = set()
    checked_discoveries = []
    for row in discoveries:
        if type(row) is not dict or set(row) != {
                "id", "class", "discovered_phase", "symptom", "blocking_requirement",
                "repair", "regression_test", "accounting_disposition", "status",
                "allocation_invalidated", "overhead"}:
            raise ValueError("exact integration discovery fields required")
        if type(row["id"]) is not str or not row["id"] or row["id"] in discovery_ids:
            raise ValueError("unique integration discovery id required")
        discovery_ids.add(row["id"])
        if row["class"] not in DISCOVERY_CLASSES:
            raise ValueError("recognized integration discovery class required")
        if row["discovered_phase"] not in {"pre_prereg", "formal"}:
            raise ValueError("integration discovery phase required")
        if any(type(row[field]) is not str or not row[field] for field in
               ("symptom", "blocking_requirement", "repair", "regression_test")):
            raise ValueError("bounded integration discovery explanation required")
        if row["accounting_disposition"] not in {
                "formal_included", "engineering_excluded_zero_model", "unavailable"}:
            raise ValueError("integration discovery accounting disposition required")
        if row["status"] not in {"fixed", "retained", "open"}:
            raise ValueError("integration discovery status required")
        if type(row["allocation_invalidated"]) is not bool:
            raise ValueError("boolean allocation invalidation required")
        overhead = row["overhead"]
        if type(overhead) is not dict or set(overhead) != {
                "allocation_id", "model_calls", "input_tokens", "runtime_ns",
                "target_button_down_admissions", "aggregation_scope"}:
            raise ValueError("exact integration discovery overhead required")
        if any(not _integer(overhead[field]) for field in
               ("model_calls", "input_tokens", "target_button_down_admissions")):
            raise ValueError("nonnegative integration discovery overhead required")
        if overhead["runtime_ns"] is not None and not _integer(overhead["runtime_ns"]):
            raise ValueError("runtime overhead must be nonnegative or unavailable")
        if overhead["aggregation_scope"] != "allocation_total_nonadditive_across_shared_defects":
            raise ValueError("integration discovery overhead aggregation scope required")
        if row["discovered_phase"] == "formal" and row["status"] == "fixed" and not row["allocation_invalidated"]:
            raise ValueError("formal repair cannot silently continue the same allocation")
        checked_discoveries.append(copy.deepcopy(row))
    if not REQUIRED_DISCOVERY_IDS <= discovery_ids:
        raise ValueError("known pre-prereg integration discoveries missing")
    arms = {}
    global_call_ids = set()
    for arm in ARMS:
        preflight = trace["preflight_calls"][arm]
        if type(preflight) is not dict or set(preflight) != {
                "call_id", "stage", "requested_model", "requested_effort", "usage",
                "model_visible_images"}:
            raise ValueError("exact preflight call record required")
        if (any(type(preflight[field]) is not str or not preflight[field] for field in
                ("call_id", "stage", "requested_model", "requested_effort"))
                or preflight["stage"] != "schema_preflight"
                or preflight["model_visible_images"] != 0):
            raise ValueError("fresh no-image schema preflight required for each arm")
        usage = preflight["usage"]
        if type(usage) is not dict or set(usage) != set(USAGE_FIELDS):
            raise ValueError("complete preflight usage required")
        if any(not _integer(usage[field]) for field in USAGE_FIELDS):
            raise ValueError("nonnegative preflight usage required")
        if usage["cached_input_tokens"] > usage["input_tokens"]:
            raise ValueError("cached preflight input must be a subset of input")
        if preflight["call_id"] in global_call_ids:
            raise ValueError("duplicate model call id across comparison")
        global_call_ids.add(preflight["call_id"])
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
        token_total = preflight["usage"]["input_tokens"]
        generation_total = 1
        for row in checked:
            token_total += sum(call["usage"]["input_tokens"] for call in row["model_calls"])
            generation_total += row["planner_generations"]
            cumulative_tokens.append(token_total)
            cumulative_generations.append(generation_total)
        arms[arm] = {
            "preflight_call": copy.deepcopy(preflight),
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
    invalidated = any(row["allocation_invalidated"] for row in checked_discoveries)
    if invalidated:
        disposition = "HOLD"
        reason = "formal_allocation_invalidated_by_integration_discovery"
    elif not safety:
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
        "integration_discoveries": checked_discoveries,
    }
