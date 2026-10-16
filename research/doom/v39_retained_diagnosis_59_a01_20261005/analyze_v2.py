"""Build an additive V39 diagnosis that separates policy and action revocation."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FREEZE_PATH = HERE / "FREEZE.json"
DEFAULT_OUTPUT = HERE / "RESULT_V2.json"
REPORT_PATH = "research/doom/results/map01-v39-coast-liveness-live-01/report.json"
EVENTS_PATH = "research/doom/results/map01-v39-coast-liveness-live-01/runtime/events.jsonl"


def read_pinned_sources(freeze):
    sources = {}
    commit = freeze["source_commit"]
    for path, pin in freeze["inputs"].items():
        blob = subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=ROOT)
        blob_id = subprocess.check_output(
            ["git", "rev-parse", f"{commit}:{path}"], cwd=ROOT, text=True
        ).strip()
        if blob_id != pin["git_blob"]:
            raise ValueError(f"source blob mismatch: {path}")
        if hashlib.sha256(blob).hexdigest() != pin["sha256"]:
            raise ValueError(f"source hash mismatch: {path}")
        if len(blob) != pin["bytes"]:
            raise ValueError(f"source byte-count mismatch: {path}")
        sources[path] = blob
    if set(sources) != {REPORT_PATH, EVENTS_PATH}:
        raise ValueError("unexpected frozen input set")
    return sources


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
    released = next((row for row in rows if row.get("event") == "input_released"), None)
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


def reconstruct():
    freeze = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    sources = read_pinned_sources(freeze)
    report = json.loads(sources[REPORT_PATH])
    events = [json.loads(line) for line in sources[EVENTS_PATH].splitlines()]
    by_id = {}
    typed_by_cover = {}
    for event in events:
        event_id = event.get("id")
        if isinstance(event_id, str):
            by_id.setdefault(event_id, []).append(event)
            if event.get("event") == "typed_observation":
                typed_by_cover.setdefault(event_id, []).append(event)

    decisions = []
    for raw_decision in report["decisions"]:
        iteration = raw_decision["iteration"]
        cover_id = f"cover-{iteration}"
        observations = typed_by_cover.get(cover_id, [])
        signal_values = {"health": [], "ammo": []}
        for observation in observations:
            for signal_name in signal_values:
                value = observation.get("signals", {}).get(signal_name, {}).get("value")
                if type(value) is int:
                    signal_values[signal_name].append(value)

        cover_rows = by_id.get(cover_id, [])
        accepted = next((row for row in cover_rows if row.get("event") == "accepted"), None)
        terminal = next((row for row in reversed(cover_rows)
                         if row.get("event") == "terminal"), None)
        action = raw_decision.get("action") or {}
        final_admission = raw_decision.get("final_action_admission") or {}
        partial = raw_decision.get("partial_execution")
        running_guard = raw_decision.get("running_action_guard") or {}
        plan_id = partial.get("id") if isinstance(partial, dict) else None
        historical_accept = running_guard.get("historical_first_admission") or {}
        if plan_id is not None and historical_accept.get("id") not in (None, plan_id):
            raise ValueError(f"running-action identity mismatch in decision {iteration}")

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
            "health_first_last": ([signal_values["health"][0], signal_values["health"][-1]]
                                   if signal_values["health"] else None),
            "ammo_first_last": ([signal_values["ammo"][0], signal_values["ammo"][-1]]
                                if signal_values["ammo"] else None),
            "soft_event_count": raw_decision.get("cover_validity_soft_events"),
            "policy_invalidation": raw_decision.get("policy_invalidation"),
            "running_action_invalidation": raw_decision.get("running_action_invalidation"),
            "running_action": ({
                "id": plan_id,
                "partial_execution": partial,
                "current_input_authority": running_guard.get("current_input_authority"),
                "physical_release_verified": running_guard.get("physical_release_verified"),
                "lifecycle": _running_action_lifecycle(plan_id, by_id),
            } if plan_id is not None else None),
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
        raise ValueError("aggregate score source mismatch")

    return {
        "schema": "issue59-v39-retained-diagnosis-result-v2",
        "source_commit": freeze["source_commit"],
        "classification": "PASS_DESCRIPTIVE_DIAGNOSIS_ONLY",
        "event_rows": len(events),
        "typed_observations": sum(event.get("event") == "typed_observation" for event in events),
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
            "Decision 3 separates a running action-validity revocation from policy-monitor invalidation: "
            "the admitted plan was canceled after the revocation, owner release was verified empty, and "
            "the terminal reports zero completed steps. The retained trace still cannot verify whether "
            "model-authored threat descriptions are correct or attribute useful progress to a particular "
            "action; the single aggregate score cannot be assigned to a decision."
        ),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-path", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    if args.output_path.exists():
        parser.error(f"output already exists: {args.output_path}")
    result = reconstruct()
    args.output_path.parent.mkdir(parents=True, exist_ok=True)
    args.output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "classification": result["classification"],
        "decisions": len(result["decisions"]),
        "score_rows": result["aggregate_score"]["rows"],
        "decision_3_running_action": result["decisions"][3]["running_action"]["id"],
    }, indent=2))


if __name__ == "__main__":
    main()
