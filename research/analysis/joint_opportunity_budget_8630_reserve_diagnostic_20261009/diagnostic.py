"""Closed-form policy enumeration for the Issue #8630 reserve diagnostic."""
from __future__ import annotations

from fractions import Fraction
from itertools import product
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def load_model():
    return json.loads((ROOT / "MODEL.json").read_text())


def frac(value):
    return Fraction(value)


def score(prior, success_by_type, recovery_p, attempts):
    """Expected verified success from an initial action and N recoveries."""
    total = Fraction(0)
    for type_index, type_prior in enumerate(prior):
        action_success = success_by_type[type_index]
        recovered = 1 - (1 - recovery_p) ** attempts
        total += frac(type_prior) * (action_success + (1 - action_success) * recovered)
    return total


def action_plans(observe, types):
    if observe:
        return list(product(("A", "B"), repeat=len(types)))
    return [("A",) * len(types), ("B",) * len(types)]


def feasible_rows(model, regime):
    types = model["hidden_types"]
    prior = model["prior"]
    probabilities = model["action_success_probability"][regime]
    horizon = model["resources"]["horizon_opportunities"]
    obs_cost = model["resources"]["observation_cost"]
    action_cost = model["resources"]["initial_action_cost"]
    verify_cost = model["resources"]["mandatory_verification_cost"]
    recovery_cost = model["resources"]["recovery_attempt_cost"]
    minimum_recovery = model["resources"]["minimum_recovery_attempts_reserved_after_action"]
    recovery_p = frac(model["resources"]["recovery_success_probability_per_attempt"])
    rows = []
    for observe in (False, True):
        max_recoveries = (horizon - obs_cost * int(observe) - action_cost - verify_cost) // recovery_cost
        for plan in action_plans(observe, types):
            success_by_type = [frac(probabilities[action][i]) for i, action in enumerate(plan)]
            for attempts in range(minimum_recovery, max_recoveries + 1):
                opportunities_used = obs_cost * int(observe) + action_cost + verify_cost + recovery_cost * attempts
                rows.append({
                    "observe": observe,
                    "action_by_type": dict(zip(types, plan)),
                    "recovery_attempts": attempts,
                    "verification_opportunities": 1,
                    "opportunities_used": opportunities_used,
                    "score_exact": str(score(prior, success_by_type, recovery_p, attempts)),
                })
    return rows


def best(rows, observe=None):
    candidates = [row for row in rows if observe is None or row["observe"] is observe]
    return max(candidates, key=lambda row: (frac(row["score_exact"]), row["recovery_attempts"], row["observe"]))


def result(model):
    out = {"schema": "issue-8630-reserve-diagnostic-candidate-v1", "regimes": {}}
    for regime in model["action_success_probability"]:
        rows = feasible_rows(model, regime)
        out["regimes"][regime] = {
            "feasible_policy_count": len(rows),
            "joint_optimum": best(rows),
            "always_observe": best(rows, True),
            "never_observe": best(rows, False),
            "feasible_policies": rows,
        }
    return out


def main():
    print(json.dumps(result(load_model()), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
