"""Independent audit of the first passing compiled-interface live mechanics pair."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE / "results/compiled-gui-interface-live-04"
FIELDS = ("input_tokens", "cached_input_tokens", "cache_write_input_tokens",
          "output_tokens", "reasoning_output_tokens")


def read(path): return json.loads(path.read_text(encoding="utf-8"))
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def inside(point, box):
    return box[0] <= point[0] < box[0] + box[2] and box[1] <= point[1] < box[1] + box[3]


def main():
    plan = read(ROOT / "preregistration.json")
    for name, digest in plan["sources"].items(): assert sha(HERE / name) == digest, name
    report = read(ROOT / "report.json")
    assert report["passed"] is True
    assert report["decision"] == "ADVANCE_TO_MATCHED_EFFICIENCY_COMPARISON"
    assert all(report["promotion_gates"].values())
    preflight = report["preflight"]
    assert preflight["accepted"] is True and preflight["model_calls"] == 0
    cached = preflight["results"][0]["result"]
    assert cached["cache_hit"] is True and cached["model_call_performed"] is False
    assert report["actual_performed_model_usage_totals"] == {
        "input_tokens": 18792, "cached_input_tokens": 0,
        "cache_write_input_tokens": 0, "output_tokens": 338,
        "reasoning_output_tokens": 108}
    assert len(report["all_model_attempt_ledger"]) == 3
    assert report["all_model_attempt_ledger"][0]["performed"] is False
    actual_attempts = [row for row in report["all_model_attempt_ledger"] if row["performed"]]
    assert len(actual_attempts) == 2
    assert len({row["call_id"] for row in actual_attempts}) == 2
    assert {field: sum(row["usage"][field] for row in actual_attempts)
            for field in FIELDS} == report["actual_performed_model_usage_totals"]

    cases = {row["name"]: row for row in report["cases"]}
    assert set(cases) == {"changed-target", "positive"}
    boxes = report["independent_point_boxes"]
    for case in cases.values():
        points = case["grounding_model"]["grounding"]
        assert inside(points["field_point"], boxes["field"])
        assert inside(points["submit_point"], boxes["submit"])
        assert case["adaptive"]["accounting"]["attempted_calls"] == 1
        assert case["adaptive"]["accounting"]["completed_calls"] == 1
        assert case["adaptive"]["comparison"] == {
            "class": "injected_subpath", "omitted_stages": ["coarse_model"],
            "comparable_to_full_cold": False}
        assert len(case["mint"]["programs"]) == len(case["mint"]["minted"]) == 2
        assert all(row["terminal"]["status"] == "completed" and
                   row["terminal"]["release"]["verified"] is True
                   for row in case["mint"]["programs"])
        assert case["planner_boundaries"] == case["model_visible_images"] == 1
        assert case["compiled_runtime"]["frontier_model_resumptions"] == 0
        assert case["raw_evidence_retention_verified"] is True
        for evidence in case["raw_evidence"]:
            path = ROOT / f"{case['index']}-{case['name']}" / evidence["normalized"]["evidence_ref"]
            assert path.exists() and sha(path) == evidence["image_sha256"]
            assert evidence["field_change_threshold"] == 40
        for action, timing in zip(case["action_records"], case["timings"]["actions"]):
            assert action["terminal"]["status"] == "completed"
            assert action["terminal"]["release"]["verified"] is True
            assert action["terminal"]["release"]["keys_down"] == []
            assert action["terminal"]["release"]["buttons_down"] == []
            assert len(action["pointer_admissions"]) == 2
            assert timing["action"] == action["action"]
            assert abs(timing["action_to_first_useful_feedback_ms"] -
                       (timing["feedback_capture_ns"] - timing["input_ack_ns"]) / 1e6) < 1e-9

    positive = cases["positive"]
    runtime = positive["compiled_runtime"]
    assert positive["adaptive"]["outcome"] == "TASK_SUCCEEDED"
    assert runtime["outcome"] == "TASK_SUCCEEDED" and runtime["reason"] == "method_complete"
    assert runtime["completed_transitions"] == 2 and len(runtime["observations"]) == 3
    assert [row["action"] for row in runtime["transitions"]] == ["enter_token", "submit_form"]
    assert runtime["transitions"][1]["matched_conditions"] == {
        "field_pixels_changed": True, "submit_target_present": True}
    assert runtime["transitions"][1]["observation_sequence"] > runtime["transitions"][0]["observation_sequence"]
    assert positive["raw_evidence"][1]["field_changed_pixels"] == 361
    assert positive["raw_evidence"][2]["normalized"]["predicates"][
        "submission_pixels_changed"] is True
    assert positive["independent_evaluation"]["success"] is True
    assert positive["actual"] == {"value": [positive["goal"]["token"]]}
    assert positive["intervention"] is None and positive["durable_calls"] == 21

    changed = cases["changed-target"]
    changed_runtime = changed["compiled_runtime"]
    assert changed["adaptive"]["outcome"] == "EXECUTION_INCOMPLETE"
    assert changed["adaptive"]["reason"] == "failed"
    assert changed_runtime["outcome"] == "SAFE_YIELD"
    assert changed_runtime["reason"] == "unknown_state"
    assert changed_runtime["completed_transitions"] == 1
    assert [row["action"] for row in changed["action_records"]] == ["enter_token"]
    assert changed["raw_evidence"][1]["normalized"]["predicates"][
        "submit_target_present"] is False
    assert changed["intervention"]["terminal"]["status"] == "completed"
    assert changed["intervention"]["terminal"]["release"]["verified"] is True
    assert changed["independent_evaluation"]["success"] is False
    assert changed["actual"] == {} and changed["durable_calls"] == 18

    audit = {"passed": True, "formal_mechanics_passed": True,
        "positive": {"independent_success": True, "local_transitions": 2,
            "frontier_model_resumptions": 0,
            "action_to_feedback_ms": [row["action_to_first_useful_feedback_ms"]
                                      for row in positive["timings"]["actions"]],
            "first_action_to_semantic_completion_ms": positive["timings"][
                "first_action_to_independent_semantic_completion_ms"],
            "local_runtime_ms": positive["timings"]["local_runtime_elapsed_ms"],
            "grounding_wait_ms": positive["timings"]["grounding_model_wait_ms"]},
        "changed": {"independent_success": False, "local_transitions": 1,
            "submit_target_actions": 0, "typed_runtime_reason": "unknown_state",
            "outer_adaptive_reason": "failed"},
        "fresh_model_calls": 2,
        "fresh_model_usage_totals": report["actual_performed_model_usage_totals"],
        "preflight_model_calls_this_run": 0,
        "known_limit": "adaptive caller v1 collapses nested typed SAFE_YIELD to generic execute failed",
        "decision": "RETAIN_LIVE_MECHANICS;_FIX_OUTER_TYPED_YIELD_BEFORE_EFFICIENCY_ABLATION",
        "scope": "one fresh same-seed positive/changed pair; no baseline, rate, token saving, portability, break-even or human-tempo claim"}
    (ROOT / "audit.json").write_text(json.dumps(audit, indent=2) + "\n",
                                      encoding="utf-8", newline="\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__": main()
