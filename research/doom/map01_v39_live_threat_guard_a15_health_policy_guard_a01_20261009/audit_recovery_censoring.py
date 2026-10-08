"""Post-run recovery audit that separates missed recovery from right censoring."""
from pathlib import Path
import json

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
ALLOC = "map01-v39-live-threat-guard-a15-health-policy-guard-20261009"
ROOT = REPO / "results-local/doom" / ALLOC


def is_hard_health_guard(decision):
    invalidation = decision.get("policy_invalidation") or {}
    health = invalidation.get("outcomes", {}).get("health", {})
    return (invalidation.get("reason") == "health:below_hard_minimum" or
            (health.get("status") == "HARD_INVALIDATED" and
             health.get("reason") == "below_hard_minimum"))


def analyze(decisions, decision_cap):
    if not decisions or type(decision_cap) is not int or decision_cap < 1:
        raise ValueError("decisions and positive decision cap are required")
    rows = []
    for guard in decisions:
        if not is_hard_health_guard(guard):
            continue
        iteration = guard.get("iteration")
        invalidation_sequence = (guard.get("policy_invalidation") or {}).get("sequence")
        if type(iteration) is not int or type(invalidation_sequence) is not int:
            rows.append({"iteration": iteration, "classification": "insufficient_guard_receipt"})
            continue
        recovery = [row for row in decisions
                    if type(row.get("iteration")) is int and
                    iteration < row["iteration"] <= iteration + 2 and
                    type(row.get("fresh_sequence_at_plan")) is int and
                    row["fresh_sequence_at_plan"] > invalidation_sequence and
                    row.get("model_action_discarded") is not True]
        observed_max = max((row.get("iteration", -1) for row in decisions
                            if type(row.get("iteration")) is int), default=-1)
        if recovery:
            classification = "recovered_within_two_decisions"
        elif observed_max >= iteration + 2:
            classification = "observable_recovery_missed"
        else:
            classification = "right_censored_by_episode_or_decision_cap"
        rows.append({"iteration": iteration, "classification": classification,
                     "fresh_recovery_decisions_within_two": [row.get("iteration") for row in recovery],
                     "required_followup_through_iteration": iteration + 2,
                     "last_observed_decision_iteration": observed_max,
                     "decision_cap": decision_cap})
    counts = {name: sum(row.get("classification") == name for row in rows)
              for name in ("recovered_within_two_decisions",
                           "observable_recovery_missed",
                           "right_censored_by_episode_or_decision_cap",
                           "insufficient_guard_receipt")}
    return {"hard_health_guard_count": len(rows), "classifications": counts, "guards": rows}


def main():
    freeze = json.loads((ROOT / "FREEZE.json").read_text())
    report = json.loads((ROOT / "episode/report.json").read_text())
    result = {
        "schema": "map01-v39-live-threat-guard-a15-health-policy-guard-censoring-v1",
        "allocation": ALLOC,
        "scope": "post-run classification of observed follow-up opportunity",
        **analyze(report.get("decisions", []), freeze["runtime"]["iterations"]),
    }
    (ROOT / "A15_RECOVERY_CENSORING.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
