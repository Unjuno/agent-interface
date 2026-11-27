"""Independent path enumerator; intentionally does not import diagnostic.py."""
from __future__ import annotations

from fractions import Fraction
from itertools import product
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def rational(text):
    return Fraction(text)


def expected_by_paths(prior, type_success, recovery_probability, recovery_count):
    total = rational("0")
    for index in range(len(prior)):
        weight = rational(prior[index])
        initial = rational(type_success[index])
        total += weight * initial
        unresolved = weight * (1 - initial)
        for _ in range(recovery_count):
            # Enumerate one successful recovery branch and its continuing failure branch.
            total += unresolved * rational(recovery_probability)
            unresolved *= 1 - rational(recovery_probability)
    return total


def reconstruct(model, regime):
    types = model["hidden_types"]
    resource = model["resources"]
    matrix = model["action_success_probability"][regime]
    schedules = []
    for observation in (0, 1):
        if observation:
            plans = list(product(("A", "B"), repeat=len(types)))
        else:
            plans = [("A",) * len(types), ("B",) * len(types)]
        available = resource["horizon_opportunities"] - observation * resource["observation_cost"] - resource["initial_action_cost"] - resource["mandatory_verification_cost"]
        maximum = available // resource["recovery_attempt_cost"]
        for plan in plans:
            per_type = [matrix[action][i] for i, action in enumerate(plan)]
            for recovery_count in range(resource["minimum_recovery_attempts_reserved_after_action"], maximum + 1):
                used = observation * resource["observation_cost"] + resource["initial_action_cost"] + resource["mandatory_verification_cost"] + recovery_count * resource["recovery_attempt_cost"]
                value = expected_by_paths(model["prior"], per_type, resource["recovery_success_probability_per_attempt"], recovery_count)
                schedules.append({
                    "observe": bool(observation),
                    "action_by_type": dict(zip(types, plan)),
                    "recovery_attempts": recovery_count,
                    "verification_opportunities": 1,
                    "opportunities_used": used,
                    "score_exact": str(value),
                })
    return schedules


def audit(candidate, model):
    errors = []
    if candidate.get("schema") != "issue-8630-reserve-diagnostic-candidate-v1":
        errors.append("candidate_schema")
    result = {"schema": "issue-8630-reserve-diagnostic-audit-v1", "errors": [], "regimes": {}}
    for regime in model["action_success_probability"]:
        expected = reconstruct(model, regime)
        actual = candidate.get("regimes", {}).get(regime, {})
        if actual.get("feasible_policies") != expected:
            errors.append(f"policy_reconstruction:{regime}")
        maximum = max(expected, key=lambda row: (rational(row["score_exact"]), row["recovery_attempts"], row["observe"]))
        always = max((row for row in expected if row["observe"]), key=lambda row: rational(row["score_exact"]))
        never = max((row for row in expected if not row["observe"]), key=lambda row: rational(row["score_exact"]))
        if actual.get("joint_optimum") != maximum:
            errors.append(f"joint_optimum:{regime}")
        if actual.get("always_observe") != always or actual.get("never_observe") != never:
            errors.append(f"fixed_control:{regime}")
        if any(row["verification_opportunities"] != 1 or row["recovery_attempts"] < model["resources"]["minimum_recovery_attempts_reserved_after_action"] or row["opportunities_used"] > model["resources"]["horizon_opportunities"] for row in expected):
            errors.append(f"hard_gate_or_budget:{regime}")
        result["regimes"][regime] = {
            "policy_count": len(expected),
            "joint_score": maximum["score_exact"],
            "always_observe_score": always["score_exact"],
            "never_observe_score": never["score_exact"],
            "joint_observes": maximum["observe"],
        }
    expected_choices = {"informative": True, "weak_signal": False}
    for regime, choice in expected_choices.items():
        if result["regimes"].get(regime, {}).get("joint_observes") is not choice:
            errors.append(f"decision_gate:{regime}")
        if result["regimes"].get(regime, {}).get("joint_score") == result["regimes"].get(regime, {}).get("always_observe_score") and choice is False:
            errors.append(f"weak_case_must_beat_observe:{regime}")
        if result["regimes"].get(regime, {}).get("joint_score") == result["regimes"].get(regime, {}).get("never_observe_score") and choice is True:
            errors.append(f"informative_case_must_beat_skip:{regime}")
    result["errors"] = errors
    result["disposition"] = "PASS_DIAGNOSTIC" if not errors else "FAIL_DIAGNOSTIC"
    return result


def main():
    model = json.loads((ROOT / "MODEL.json").read_text())
    candidate = json.loads(sys.stdin.read())
    print(json.dumps(audit(candidate, model), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
