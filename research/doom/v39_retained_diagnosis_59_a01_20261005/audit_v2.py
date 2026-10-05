"""Strict raw-derived audit of every field in the retained diagnosis result.

The historical audit.py remains unchanged. This version rebuilds the complete
result projection from the frozen report and event stream, then compares JSON
types and values exactly so booleans cannot alias integer timestamps.
"""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FREEZE_PATH = HERE / "FREEZE.json"
DEFAULT_RESULT_PATH = HERE / "RESULT.json"
REPORT_PATH = "research/doom/results/map01-v39-coast-liveness-live-01/report.json"
EVENTS_PATH = "research/doom/results/map01-v39-coast-liveness-live-01/runtime/events.jsonl"


def load_pinned_inputs(freeze):
    raw_by_path = {}
    source = freeze["source_commit"]
    for path, pin in freeze["inputs"].items():
        raw = subprocess.check_output(["git", "show", f"{source}:{path}"], cwd=ROOT)
        blob = subprocess.check_output(
            ["git", "rev-parse", f"{source}:{path}"], cwd=ROOT, text=True
        ).strip()
        if blob != pin["git_blob"]:
            raise ValueError(f"SOURCE_BLOB_MISMATCH: {path}")
        if hashlib.sha256(raw).hexdigest() != pin["sha256"]:
            raise ValueError(f"SOURCE_HASH_MISMATCH: {path}")
        if len(raw) != pin["bytes"]:
            raise ValueError(f"SOURCE_LENGTH_MISMATCH: {path}")
        raw_by_path[path] = raw
    if set(raw_by_path) != {REPORT_PATH, EVENTS_PATH}:
        raise ValueError("SOURCE_SET_MISMATCH")
    return raw_by_path


def derive_expected_result():
    freeze = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    raw_by_path = load_pinned_inputs(freeze)
    report = json.loads(raw_by_path[REPORT_PATH])
    events = [json.loads(line) for line in raw_by_path[EVENTS_PATH].splitlines()]

    typed_by_cover = {}
    events_by_id = {}
    for row in events:
        event_id = row.get("id")
        if isinstance(event_id, str):
            events_by_id.setdefault(event_id, []).append(row)
            if row.get("event") == "typed_observation":
                typed_by_cover.setdefault(event_id, []).append(row)

    decisions = []
    for raw_decision in report["decisions"]:
        iteration = raw_decision["iteration"]
        cover_id = f"cover-{iteration}"
        observations = typed_by_cover.get(cover_id, [])
        values_by_signal = {"health": [], "ammo": []}
        for observation in observations:
            signals = observation.get("signals", {})
            for signal_name in values_by_signal:
                signal = signals.get(signal_name, {})
                value = signal.get("value")
                if type(value) is int:
                    values_by_signal[signal_name].append(value)

        cover_events = events_by_id.get(cover_id, [])
        accepted = next(
            (event for event in cover_events if event.get("event") == "accepted"), None
        )
        terminal = next(
            (event for event in reversed(cover_events)
             if event.get("event") == "terminal"), None
        )
        action = raw_decision.get("action") or {}
        final_admission = raw_decision.get("final_action_admission") or {}
        invalidation = (raw_decision.get("policy_invalidation")
                        or raw_decision.get("running_action_invalidation"))

        decisions.append({
            "iteration": iteration,
            "model_wait_ms": round(raw_decision.get("model_ns", 0) / 1_000_000, 3),
            "planner_status": raw_decision.get("planner_turn_status"),
            "planner_answer_eligible": raw_decision.get("planner_answer_eligible"),
            "cover_id": cover_id,
            "cover_policy_source_iteration": raw_decision.get("cover_policy_source_iteration"),
            "cover_policy_actions": raw_decision.get("cover_policy"),
            "next_cover_authored": action.get("next_cover"),
            "cover_accept_ns": accepted.get("accepted_ns") if accepted else None,
            "cover_terminal_ns": terminal.get("terminal_ns") if terminal else None,
            "cover_terminal_status": terminal.get("status") if terminal else None,
            "typed_observation_count": len(observations),
            "health_first_last": ([values_by_signal["health"][0],
                                    values_by_signal["health"][-1]]
                                   if values_by_signal["health"] else None),
            "ammo_first_last": ([values_by_signal["ammo"][0],
                                 values_by_signal["ammo"][-1]]
                                if values_by_signal["ammo"] else None),
            "soft_event_count": raw_decision.get("cover_validity_soft_events"),
            "policy_invalidation": invalidation,
            "model_assessment_at_return": action.get("assessment"),
            "returned_action_admission": final_admission.get("status"),
            "returned_action_discarded": raw_decision.get("model_action_discarded"),
            "contingency_branch": raw_decision.get("contingency_branch"),
            "effect_receipts": [{
                "action": effect.get("action"),
                "result": effect.get("result"),
                "scope": effect.get("scope"),
                "after_sequence": effect.get("after_sequence"),
            } for effect in raw_decision.get("effect_receipts", [])],
        })

    score = report.get("score", {})
    score_rows = [event for event in events if event.get("event") == "post_control_score"]
    if len(score_rows) != 1 or score_rows[0] != score:
        raise ValueError("AGGREGATE_SCORE_SOURCE_MISMATCH")

    return {
        "schema": "issue59-v39-retained-diagnosis-result-v1",
        "source_commit": freeze["source_commit"],
        "classification": "PASS_DESCRIPTIVE_DIAGNOSIS_ONLY",
        "event_rows": len(events),
        "typed_observations": sum(
            event.get("event") == "typed_observation" for event in events
        ),
        "decisions": decisions,
        "aggregate_score": {
            "rows": len(score_rows),
            "map_exit": score.get("map_exit"),
            "episode_finished": score.get("episode_finished"),
            "player_dead": score.get("player_dead"),
            "deaths": score.get("death_count"),
            "kills": score.get("kill_count"),
        },
        "limitations": {
            "threat_descriptions_are_model_authored": True,
            "independent_per_decision_task_effect": False,
            "matched_fixed_safe_counterfactual": False,
            "physical_key_occupancy": False,
            "useful_feedback_oracle": False,
            "causal_kill_or_survival_attribution": False,
            "contingency_effect_established": False,
            "live_run_or_replay_performed": False,
        },
        "diagnostic": (
            "The retained trace localizes one typed-health-triggered invalidation and verified-empty release, "
            "but does not identify whether the changing threat descriptions are independently correct or "
            "whether any cover produced useful task progress. The single aggregate score cannot be assigned "
            "to a decision."
        ),
    }


def first_difference(actual, expected, path="$result"):
    if type(actual) is not type(expected):
        return f"{path}: JSON type {type(actual).__name__} != {type(expected).__name__}"
    if isinstance(expected, dict):
        if actual.keys() != expected.keys():
            missing = sorted(expected.keys() - actual.keys())
            extra = sorted(actual.keys() - expected.keys())
            return f"{path}: keys differ; missing={missing}, extra={extra}"
        for key in sorted(expected):
            difference = first_difference(actual[key], expected[key], f"{path}.{key}")
            if difference:
                return difference
        return None
    if isinstance(expected, list):
        if len(actual) != len(expected):
            return f"{path}: list length {len(actual)} != {len(expected)}"
        for index, (actual_item, expected_item) in enumerate(zip(actual, expected)):
            difference = first_difference(actual_item, expected_item, f"{path}[{index}]")
            if difference:
                return difference
        return None
    if actual != expected:
        return f"{path}: value {actual!r} != {expected!r}"
    return None


def audit(result_path=DEFAULT_RESULT_PATH):
    expected = derive_expected_result()
    actual = json.loads(Path(result_path).read_text(encoding="utf-8"))
    difference = first_difference(actual, expected)
    if difference:
        raise ValueError(f"RESULT_MISMATCH: {difference}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--result-path", type=Path, default=DEFAULT_RESULT_PATH)
    args = parser.parse_args()
    audit(args.result_path)
    print("AUDIT_V2_PASS: every result field matches frozen source-derived reconstruction")


if __name__ == "__main__":
    main()
