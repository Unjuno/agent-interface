"""Reconstruct a conservative decision/effect crosswalk from frozen V39 raw data."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def blob_at(commit: str, path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=ROOT)


def run() -> dict:
    freeze = json.loads((HERE / "FREEZE.json").read_text())
    source = freeze["source_commit"]
    raw_by_path = {}
    for path, pin in freeze["inputs"].items():
        raw = blob_at(source, path)
        blob = subprocess.check_output(
            ["git", "rev-parse", f"{source}:{path}"], cwd=ROOT, text=True
        ).strip()
        if blob != pin["git_blob"] or hashlib.sha256(raw).hexdigest() != pin["sha256"]:
            raise ValueError(f"source pin mismatch: {path}")
        if len(raw) != pin["bytes"]:
            raise ValueError(f"source byte-count mismatch: {path}")
        raw_by_path[path] = raw

    report = json.loads(raw_by_path[
        "research/doom/results/map01-v39-coast-liveness-live-01/report.json"
    ])
    events = [json.loads(line) for line in raw_by_path[
        "research/doom/results/map01-v39-coast-liveness-live-01/runtime/events.jsonl"
    ].splitlines()]
    typed_by_cover: dict[str, list[dict]] = {}
    event_by_id: dict[str, list[dict]] = {}
    for row in events:
        if isinstance(row.get("id"), str):
            event_by_id.setdefault(row["id"], []).append(row)
        if row.get("event") == "typed_observation" and isinstance(row.get("id"), str):
            typed_by_cover.setdefault(row["id"], []).append(row)

    decisions = []
    for decision in report["decisions"]:
        iteration = decision["iteration"]
        cover_id = f"cover-{iteration}"
        typed = typed_by_cover.get(cover_id, [])
        signals = [row.get("signals", {}) for row in typed]
        health = [s.get("health", {}).get("value") for s in signals
                  if type(s.get("health", {}).get("value")) is int]
        ammo = [s.get("ammo", {}).get("value") for s in signals
                if type(s.get("ammo", {}).get("value")) is int]
        cover_events = event_by_id.get(cover_id, [])
        accepted = next((e for e in cover_events if e.get("event") == "accepted"), None)
        terminal = next((e for e in reversed(cover_events)
                         if e.get("event") == "terminal"), None)
        action = decision.get("action") or {}
        effects = decision.get("effect_receipts", [])
        decisions.append({
            "iteration": iteration,
            "model_wait_ms": round(decision.get("model_ns", 0) / 1_000_000, 3),
            "planner_status": decision.get("planner_turn_status"),
            "planner_answer_eligible": decision.get("planner_answer_eligible"),
            "cover_id": cover_id,
            "cover_policy_source_iteration": decision.get("cover_policy_source_iteration"),
            "cover_policy_actions": decision.get("cover_policy"),
            "next_cover_authored": action.get("next_cover"),
            "cover_accept_ns": accepted.get("accepted_ns") if accepted else None,
            "cover_terminal_ns": terminal.get("terminal_ns") if terminal else None,
            "cover_terminal_status": terminal.get("status") if terminal else None,
            "typed_observation_count": len(typed),
            "health_first_last": [health[0], health[-1]] if health else None,
            "ammo_first_last": [ammo[0], ammo[-1]] if ammo else None,
            "soft_event_count": decision.get("cover_validity_soft_events"),
            "policy_invalidation": (decision.get("policy_invalidation")
                                    or decision.get("running_action_invalidation")),
            "model_assessment_at_return": action.get("assessment"),
            "returned_action_admission": (decision.get("final_action_admission") or {}).get("status"),
            "returned_action_discarded": decision.get("model_action_discarded"),
            "contingency_branch": decision.get("contingency_branch"),
            "effect_receipts": [{
                "action": effect.get("action"),
                "result": effect.get("result"),
                "scope": effect.get("scope"),
                "after_sequence": effect.get("after_sequence"),
            } for effect in effects],
        })

    score = report.get("score", {})
    score_rows = [e for e in events if e.get("event") == "post_control_score"]
    output = {
        "schema": "issue59-v39-retained-diagnosis-result-v1",
        "source_commit": source,
        "classification": "PASS_DESCRIPTIVE_DIAGNOSIS_ONLY",
        "event_rows": len(events),
        "typed_observations": sum(e.get("event") == "typed_observation" for e in events),
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
    return output


if __name__ == "__main__":
    result = run()
    (HERE / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"classification": result["classification"],
                      "decisions": len(result["decisions"]),
                      "score_rows": result["aggregate_score"]["rows"],
                      "limitation": result["diagnostic"]}, indent=2))
