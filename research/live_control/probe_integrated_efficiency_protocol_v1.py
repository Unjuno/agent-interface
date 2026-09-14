"""Positive and fail-closed controls for the integrated trace evaluator."""

import copy
import json
from pathlib import Path

from integrated_efficiency_protocol_v1 import ARMS, EXPECTED_MODEL_CALLS, EXPECTED_ROUTES, LAYOUTS, TASKS, evaluate


HERE = Path(__file__).resolve().parent


def repair(required=False):
    return ({"required": True, "old_reference_status": "missing",
             "old_reference_pointer_admissions": 0, "attempted": True, "succeeded": True}
            if required else
            {"required": False, "old_reference_status": None,
             "old_reference_pointer_admissions": 0, "attempted": False, "succeeded": False})


def trace():
    arms = {}
    for arm in ARMS:
        rows = []
        for index, task_id in enumerate(TASKS):
            count = EXPECTED_MODEL_CALLS[arm][index]
            calls = [{"call_id": f"{arm}-{task_id}-{call}", "stage": "grounding",
                      "requested_model": "gpt-5.6-luna", "requested_effort": "low",
                      "usage": {"input_tokens": 9000, "cached_input_tokens": 0,
                                "cache_write_input_tokens": 0, "output_tokens": 100,
                                "reasoning_output_tokens": 40}}
                     for call in range(count)]
            rows.append({"arm": arm, "task_id": task_id, "layout": LAYOUTS[index],
                         "route": EXPECTED_ROUTES[arm][index], "model_calls": calls,
                         "planner_generations": count, "model_visible_images": count,
                         "local_observations": 3, "durable_calls": 5,
                         "pointer_admissions": 2, "old_target_pointer_admissions": 0,
                         "releases_verified": True, "submission_count": 1,
                         "exact_submission": True, "typed_outcome": "completed",
                         "elapsed_ns": 1_000_000_000, "source_to_completion_ns": 900_000_000,
                         "input_feedback_ns": [80_000_000, 90_000_000],
                         "repair": repair(arm == "persistent" and index == 3)})
        arms[arm] = rows
    discoveries = json.loads((HERE / "integrated_efficiency_discoveries_v1.json").read_text(
        encoding="utf-8"))
    preflight = {arm: {"call_id": f"preflight-{arm}", "stage": "schema_preflight",
                       "requested_model": "gpt-5.6-luna", "requested_effort": "low",
                       "usage": {"input_tokens": 8000, "cached_input_tokens": 0,
                                 "cache_write_input_tokens": 0, "output_tokens": 40,
                                 "reasoning_output_tokens": 0},
                       "model_visible_images": 0} for arm in ARMS}
    return {"schema": "integrated_efficiency_trace_v1", "arms": arms,
            "preflight_calls": preflight,
            "integration_discoveries": discoveries}


def must_reject(value, expected):
    try:
        evaluate(value)
    except ValueError as exc:
        assert expected in str(exc), (expected, str(exc))
    else:
        raise AssertionError("invalid trace accepted: " + expected)


def main():
    valid = trace()
    result = evaluate(valid)
    assert result["disposition"] == "RETAIN"
    assert result["observed_break_even_task"] == 2
    wrong_schedule = copy.deepcopy(valid)
    wrong_schedule["arms"]["persistent"][1]["model_calls"] = copy.deepcopy(
        wrong_schedule["arms"]["plain"][1]["model_calls"])
    must_reject(wrong_schedule, "model call count")
    stale_input = copy.deepcopy(valid)
    stale_input["arms"]["persistent"][3]["repair"]["old_reference_pointer_admissions"] = 1
    must_reject(stale_input, "without pointer input")
    duplicate_id = copy.deepcopy(valid)
    duplicate_id["arms"]["plain"][1]["model_calls"][0]["call_id"] = (
        duplicate_id["arms"]["plain"][0]["model_calls"][0]["call_id"])
    must_reject(duplicate_id, "across comparison")
    duplicate_preflight = copy.deepcopy(valid)
    duplicate_preflight["preflight_calls"]["ephemeral"]["call_id"] = (
        duplicate_preflight["preflight_calls"]["plain"]["call_id"])
    must_reject(duplicate_preflight, "across comparison")
    missing_feedback = copy.deepcopy(valid)
    missing_feedback["arms"]["plain"][0]["input_feedback_ns"].pop()
    must_reject(missing_feedback, "per pointer admission")
    wrong_side_effect = copy.deepcopy(valid)
    wrong_side_effect["arms"]["persistent"][2]["exact_submission"] = False
    rejected = evaluate(wrong_side_effect)
    assert rejected["disposition"] == "REJECT"
    no_gain = copy.deepcopy(valid)
    for row in no_gain["arms"]["persistent"]:
        for call in row["model_calls"]:
            call["usage"]["input_tokens"] = 30_000
    assert evaluate(no_gain)["disposition"] == "REJECT"
    missing_discovery = copy.deepcopy(valid)
    missing_discovery["integration_discoveries"].pop()
    must_reject(missing_discovery, "known pre-prereg")
    silent_formal_repair = copy.deepcopy(valid)
    silent_formal_repair["integration_discoveries"][0]["discovered_phase"] = "formal"
    must_reject(silent_formal_repair, "silently continue")
    invalidated = copy.deepcopy(valid)
    invalidated["integration_discoveries"][0].update(
        discovered_phase="formal", status="open", allocation_invalidated=True,
        accounting_disposition="formal_included")
    held = evaluate(invalidated)
    assert held["disposition"] == "HOLD"
    print(json.dumps({"passed": True, "positive": result["disposition"],
                      "controls": 10}, indent=2))


if __name__ == "__main__":
    main()
