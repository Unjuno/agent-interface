"""Fail-closed, independent verifier for the A16 two-decision recovery predicate.

This post-run verifier does not modify the frozen A16 allocation or its source.
It requires positive evidence that a fresh plan exists and was not discarded.
"""
from __future__ import annotations

import json
from pathlib import Path


def is_hard_health_guard(decision: dict) -> bool:
    invalidation = decision.get("policy_invalidation") or {}
    health = invalidation.get("outcomes", {}).get("health", {})
    return (invalidation.get("reason") == "health:below_hard_minimum" or
            (health.get("status") == "HARD_INVALIDATED" and
             health.get("reason") == "below_hard_minimum"))


def analyze(decisions: list[dict], decision_cap: int) -> dict:
    if not decisions or type(decision_cap) is not int or decision_cap < 1:
        raise ValueError("decisions and positive decision cap are required")
    iterations = [row.get("iteration") for row in decisions]
    if any(type(value) is not int or value < 1 for value in iterations):
        raise ValueError("each decision requires a positive integer iteration")
    if len(set(iterations)) != len(iterations):
        raise ValueError("decision iterations must be unique")
    if any(value > decision_cap for value in iterations):
        raise ValueError("decision iteration exceeds the preregistered cap")

    rows = []
    for guard in decisions:
        if not is_hard_health_guard(guard):
            continue
        iteration = guard["iteration"]
        invalidation = guard.get("policy_invalidation") or {}
        invalidation_sequence = invalidation.get("sequence")
        if type(invalidation_sequence) is not int or invalidation_sequence < 0:
            rows.append({"iteration": iteration,
                         "classification": "insufficient_guard_receipt"})
            continue

        candidates = [row for row in decisions
                      if iteration < row["iteration"] <= iteration + 2]
        recovery = [row for row in candidates
                    if type(row.get("fresh_sequence_at_plan")) is int and
                    row["fresh_sequence_at_plan"] > invalidation_sequence and
                    row.get("model_action_discarded") is False]
        malformed = [row for row in candidates
                     if type(row.get("model_action_discarded")) is not bool]
        observed_max = max(iterations)
        required_followups = set(range(iteration + 1, iteration + 3))
        observed_followups = {row["iteration"] for row in candidates}
        missing_followups = sorted(required_followups - observed_followups)
        if malformed:
            classification = "auditor_input_invalid"
        elif recovery:
            classification = "recovered_within_two_decisions"
        elif observed_max >= iteration + 2:
            classification = ("auditor_input_invalid" if missing_followups else
                              "observable_recovery_missed")
        else:
            classification = "right_censored_by_episode_or_decision_cap"
        rows.append({
            "iteration": iteration,
            "classification": classification,
            "fresh_recovery_decisions_within_two": [r["iteration"] for r in recovery],
            "candidate_followup_decisions": [r["iteration"] for r in candidates],
            "missing_followup_decisions": missing_followups,
            "malformed_discarded_fields": [r["iteration"] for r in malformed],
            "required_followup_through_iteration": iteration + 2,
            "last_observed_decision_iteration": observed_max,
            "decision_cap": decision_cap,
        })
    names = ("recovered_within_two_decisions", "observable_recovery_missed",
             "right_censored_by_episode_or_decision_cap", "insufficient_guard_receipt",
             "auditor_input_invalid")
    return {"hard_health_guard_count": len(rows),
            "classifications": {name: sum(r["classification"] == name for r in rows)
                                for name in names},
            "guards": rows}


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    parser.add_argument("--decision-cap", type=int, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = json.loads(args.report.read_text(encoding="utf-8"))
    result = {"schema": "a16-independent-strict-recovery-audit-v1",
              "scope": "independent post-run reclassification; not live control evidence",
              **analyze(report.get("decisions", []), args.decision_cap)}
    payload = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
