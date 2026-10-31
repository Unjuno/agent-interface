"""Exact-rational prior-set diagnostic for a frozen finite check model."""
from fractions import Fraction
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def rational(value):
    return Fraction(value)


def net_value(case, prior):
    gross = ((1 - prior) * rational(case["false_completion_loss"])
             if case["check_reveals_state"] else Fraction(0))
    return gross, gross - rational(case["check_cost"])


def action_for(net):
    # Frozen tie policy: a zero net value stops optional acquisition.
    return "CONTINUE" if net > 0 else "STOP"


def gated_action(case, action):
    if not case["mandatory_checks_complete"]:
        return "YIELD_MANDATORY_INCOMPLETE"
    if action == "CONTINUE" and not case["check_feasible_by_deadline"]:
        return "YIELD_CHECK_INFEASIBLE"
    return action


def evaluate_case(case):
    priors = [rational(value) for value in case["plausible_priors_good"]]
    point = rational(case["point_prior_good"])
    if not priors or point not in priors or any(p < 0 or p > 1 for p in priors):
        raise ValueError("prior set must be nonempty, contain the point prior, and stay in [0,1]")

    prior_evaluations = []
    for prior in priors:
        gross, net = net_value(case, prior)
        prior_evaluations.append({
            "prior_good": str(prior),
            "gross_value": str(gross),
            "net_value": str(net),
            "decision": action_for(net),
        })

    point_gross, point_net = net_value(case, point)
    margin = rational(case["confidence_margin"])
    point_voi = {"gross_value": str(point_gross), "net_value": str(point_net),
                 "decision": gated_action(case, action_for(point_net))}
    point_plus_margin = {
        "gross_value": str(point_gross), "net_value": str(point_net),
        "margin": str(margin),
        "decision": gated_action(case, "CONTINUE" if point_net > margin else "STOP"),
    }

    if not case["mandatory_checks_complete"]:
        label = "YIELD_MANDATORY_INCOMPLETE"
    else:
        choices = {row["decision"] for row in prior_evaluations}
        if choices == {"STOP"}:
            label = "ROBUST_STOP"
        elif choices == {"CONTINUE"}:
            label = ("ROBUST_CONTINUE" if case["check_feasible_by_deadline"]
                     else "YIELD_CHECK_INFEASIBLE")
        else:
            label = "PRIOR_SENSITIVE"

    return {
        "case_id": case["id"],
        "point_voi": point_voi,
        "point_plus_margin": point_plus_margin,
        "prior_set_decision": label,
        "prior_evaluations": prior_evaluations,
        "mandatory_checks_complete": case["mandatory_checks_complete"],
        "check_feasible_by_deadline": case["check_feasible_by_deadline"],
    }


def main():
    cases = json.loads((HERE / "cases.json").read_text(encoding="utf-8"))
    results = [evaluate_case(case) for case in cases]
    output = {"schema": "voi-prior-set-robustness-candidate-v1", "results": results}
    destination = HERE / "results" / "candidate.raw.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
