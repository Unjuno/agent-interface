#!/usr/bin/env python3
"""Exact generated scenario family for Issue #5444 T7; deterministic, no RNG."""
from itertools import product
import json

LOW_RECEIPT_WEIGHT = 0.075
THRESHOLD = 0.3
COMPENSATION_THRESHOLDS = tuple(range(5))


def build_scenarios():
    scenarios = []
    for action_class, truth, compensation, votes in product(
        ("reversible", "irreversible"), ("safe", "unsafe"), range(5), product((0, 1), repeat=4)
    ):
        score = sum((2 * vote - 1) * LOW_RECEIPT_WEIGHT for vote in votes)
        scenarios.append({
            "scenario_id": f"{action_class}-{truth}-c{compensation}-v{''.join(map(str, votes))}",
            "action_class": action_class,
            "oracle_truth": truth,
            "compensation_cost": compensation,
            "authority_receipt": "UNKNOWN",
            "low_verifier_votes": list(votes),
            "low_verifier_score": round(score, 12),
            "vote_flips_to_unanimous_support": 4 - sum(votes),
            "weighted_breakdown_flips_if_commit": 1 if all(votes) else None,
        })
    return scenarios


def evaluate(scenarios):
    summaries = []
    for threshold in COMPENSATION_THRESHOLDS:
        policies = {
            "UNKNOWN_FAIL_CLOSED": [],
            "UNKNOWN_AS_ZERO": [],
            "REVERSIBLE_COMPENSATION_FILTER": [],
        }
        for row in scenarios:
            affirmative = row["low_verifier_score"] >= THRESHOLD
            policies["UNKNOWN_FAIL_CLOSED"].append(False)
            policies["UNKNOWN_AS_ZERO"].append(affirmative)
            policies["REVERSIBLE_COMPENSATION_FILTER"].append(
                affirmative and row["action_class"] == "reversible"
                and row["compensation_cost"] <= threshold
            )
        metrics = {}
        for name, decisions in policies.items():
            commits = sum(decisions)
            unsafe_commits = sum(
                decision and row["oracle_truth"] == "unsafe"
                for decision, row in zip(decisions, scenarios)
            )
            safe_total = sum(row["oracle_truth"] == "safe" for row in scenarios)
            safe_abstentions = sum(
                (not decision) and row["oracle_truth"] == "safe"
                for decision, row in zip(decisions, scenarios)
            )
            irreversible_unknown_commits = sum(
                decision and row["action_class"] == "irreversible"
                and row["authority_receipt"] == "UNKNOWN"
                for decision, row in zip(decisions, scenarios)
            )
            metrics[name] = {
                "scenario_coverage": len(decisions),
                "commits": commits,
                "commit_fraction_of_grid": commits / len(scenarios),
                "unsafe_commits": unsafe_commits,
                "unsafe_fraction_of_grid": unsafe_commits / len(scenarios),
                "safe_abstentions": safe_abstentions,
                "safe_abstention_fraction": safe_abstentions / safe_total,
                "irreversible_unknown_commits": irreversible_unknown_commits,
            }
        summaries.append({"compensation_threshold": threshold, "policies": metrics})
    return summaries


def main():
    scenarios = build_scenarios()
    print(json.dumps({
        "experiment": "issue-5444-breakdown-t7-generated-family",
        "scenario_count": len(scenarios),
        "scenario_generation": {
            "dimensions": {
                "action_class": ["reversible", "irreversible"],
                "oracle_truth": ["safe", "unsafe"],
                "compensation_cost": [0, 1, 2, 3, 4],
                "four_low_receipt_votes": "full Cartesian binary profile",
                "authority_receipt": "UNKNOWN in every generated scenario",
            },
            "low_receipt_weight": LOW_RECEIPT_WEIGHT,
            "commit_score_threshold": THRESHOLD,
            "uncertainty_note": "constructed exhaustive stress grid; fractions are coverage counts, not probabilities or confidence intervals",
        },
        "scenarios": scenarios,
        "sweep": evaluate(scenarios),
        "scope": "finite hand-authored evidence model; no real-source or calibrated-safety claim",
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
