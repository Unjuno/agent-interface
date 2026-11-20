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
DEFAULT_V2_RESULT_PATH = HERE / "RESULT_V2.json"
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


def _release_projection(event):
    if event is None:
        return None
    owner = event.get("owner_release") or event.get("release") or {}
    return {
        "event": owner.get("event"),
        "verified": owner.get("verified"),
        "verified_ns": owner.get("verified_ns"),
        "reason": owner.get("reason"),
        "keys_down": owner.get("keys_down"),
        "buttons_down": owner.get("buttons_down"),
        "grants_input_authority": event.get("grants_input_authority"),
    }


def _running_action_lifecycle(plan_id, events_by_id):
    if plan_id is None:
        return None
    rows = events_by_id.get(plan_id, [])
    accepted = next((row for row in rows if row.get("event") == "accepted"), None)
    cancelled = next((row for row in rows if row.get("event") == "cancel_requested"), None)
    released_rows = [row for row in rows if row.get("event") == "input_released"]
    if len(released_rows) > 1:
        raise ValueError(f"multiple input-release rows for {plan_id}")
    released = released_rows[0] if released_rows else None
    terminal = next((row for row in reversed(rows) if row.get("event") == "terminal"), None)
    return {
        "accepted": ({
            "accepted_ns": accepted.get("accepted_ns"),
            "steps": accepted.get("steps"),
            "program_sha256": accepted.get("program_sha256"),
        } if accepted else None),
        "cancel_requested": ({
            "requested_ns": cancelled.get("requested_ns"),
            "matched": cancelled.get("matched"),
        } if cancelled else None),
        "input_released": ({
            "published_ns": released.get("published_ns"),
            "owner_release": _release_projection(released),
            "program_terminal_pending": released.get("program_terminal_pending"),
        } if released else None),
        "terminal": ({
            "status": terminal.get("status"),
            "terminal_ns": terminal.get("terminal_ns"),
            "steps_completed": terminal.get("steps_completed"),
            "semantic_completion": terminal.get("semantic_completion"),
            "release": _release_projection(terminal.get("release")),
        } if terminal else None),
    }


def derive_expected_v2_result():
    expected = derive_expected_result()
    freeze = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    raw = load_pinned_inputs(freeze)
    report = json.loads(raw[REPORT_PATH])
    events = [json.loads(line) for line in raw[EVENTS_PATH].splitlines()]
    events_by_id = {}
    for event in events:
        if isinstance(event.get("id"), str):
            events_by_id.setdefault(event["id"], []).append(event)

    if len(expected["decisions"]) != len(report["decisions"]):
        raise ValueError("decision-count mismatch between derived report and raw result")
    for summarized, raw_decision in zip(expected["decisions"], report["decisions"]):
        partial = raw_decision.get("partial_execution")
        guard = raw_decision.get("running_action_guard") or {}
        plan_id = partial.get("id") if isinstance(partial, dict) else None
        historical = guard.get("historical_first_admission") or {}
        if plan_id is not None and historical.get("id") not in (None, plan_id):
            raise ValueError(f"running-action identity mismatch in decision {raw_decision['iteration']}")

        summarized["policy_invalidation"] = raw_decision.get("policy_invalidation")
        summarized["running_action_invalidation"] = raw_decision.get("running_action_invalidation")
        summarized["running_action"] = ({
            "id": plan_id,
            "partial_execution": partial,
            "current_input_authority": guard.get("current_input_authority"),
            "physical_release_verified": guard.get("physical_release_verified"),
            "lifecycle": _running_action_lifecycle(plan_id, events_by_id),
        } if plan_id is not None else None)

    expected["schema"] = "issue59-v39-retained-diagnosis-result-v2"
    expected["diagnostic"] = (
        "Decision 3 separates a running action-validity revocation from policy-monitor invalidation: "
        "the admitted plan was canceled after the revocation, owner release was verified empty, and "
        "the terminal reports zero completed steps. The retained trace still cannot verify whether "
        "model-authored threat descriptions are correct or attribute useful progress to a particular "
        "action; the single aggregate score cannot be assigned to a decision."
    )
    return expected


def audit(result_path=DEFAULT_V2_RESULT_PATH):
    legacy_expected = derive_expected_result()
    legacy_actual = json.loads(DEFAULT_RESULT_PATH.read_text(encoding="utf-8"))
    legacy_difference = first_difference(legacy_actual, legacy_expected, "$legacy_result")
    if legacy_difference:
        raise ValueError(f"LEGACY_RESULT_MISMATCH: {legacy_difference}")

    expected = derive_expected_v2_result()
    actual = json.loads(Path(result_path).read_text(encoding="utf-8"))
    difference = first_difference(actual, expected)
    if difference:
        raise ValueError(f"RESULT_MISMATCH: {difference}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--result-path", type=Path, default=DEFAULT_V2_RESULT_PATH)
    args = parser.parse_args()
    audit(args.result_path)
    print("AUDIT_V2_PASS: legacy result preserved; every v2 field matches frozen source-derived reconstruction")


if __name__ == "__main__":
    main()
