#!/usr/bin/env python3
"""Exact finite-model comparison for Issue #5428 T1; no randomness."""
from fractions import Fraction as F
from itertools import product
import json

LOSSES = {
    "reversible": F(1, 4),
    "compensable": F(1, 2),
    "costly_to_reverse": F(1, 1),
    "one_shot": F(2, 1),
}
PRIORS = (F(1, 10), F(1, 4), F(1, 2))  # P(target=bad)
ACCURACIES = (F(1, 2), F(3, 4), F(9, 10))
WAIT_COSTS = (F(1, 4), F(3, 4))
ALT_UTILITY = F(3, 4)
GOOD_UTILITY = F(2, 1)


def frac(value):
    return {"n": value.numerator, "d": value.denominator}


def posterior_and_mass(p_bad, accuracy, signal_bad):
    likelihood_bad = accuracy if signal_bad else 1 - accuracy
    likelihood_good = 1 - accuracy if signal_bad else accuracy
    mass = p_bad * likelihood_bad + (1 - p_bad) * likelihood_good
    if mass == 0:
        return None, F(0)
    return p_bad * likelihood_bad / mass, mass


def primary_value(p_bad, loss):
    return (1 - p_bad) * GOOD_UTILITY - p_bad * loss


def best_action(primary, alternative):
    choices = [(F(0), "NOOP")]
    if alternative:
        choices.append((ALT_UTILITY, "ALTERNATIVE"))
    if primary is not None:
        choices.append((primary, "PRIMARY"))
    # Tie-break toward the less irreversible action: NOOP, then alternative, then primary.
    priority = {"NOOP": 0, "ALTERNATIVE": 1, "PRIMARY": 2}
    return max(choices, key=lambda item: (item[0], -priority[item[1]]))


def probe_value(case, include_alternative):
    if not case["gate_open"] or not case["deadline_slack"]:
        return None, []
    branches = []
    total = F(0)
    for signal_bad in (False, True):
        posterior, mass = posterior_and_mass(case["p_bad"], case["accuracy"], signal_bad)
        if mass == 0:
            continue
        primary = primary_value(posterior, case["loss"]) if case["primary_survives"] else None
        alternative = include_alternative and case["alternative_after"]
        utility, action = best_action(primary, alternative)
        total += mass * utility
        branches.append({"signal": "bad" if signal_bad else "good", "mass": frac(mass),
                         "posterior_bad": frac(posterior), "action": action,
                         "utility": frac(utility)})
    return total - case["wait_cost"], branches


def primary_only_evsi(case):
    prior_value = max(F(0), primary_value(case["p_bad"], case["loss"]))
    posterior_value = F(0)
    for signal_bad in (False, True):
        posterior, mass = posterior_and_mass(case["p_bad"], case["accuracy"], signal_bad)
        if mass:
            posterior_value += mass * max(F(0), primary_value(posterior, case["loss"]))
    return posterior_value - prior_value


def make_cases():
    dimensions = product(
        LOSSES.items(), PRIORS, ACCURACIES, WAIT_COSTS,
        (False, True),  # deadline_slack: probe takes one tick
        (False, True),  # alternative available immediately
        (False, True),  # alternative survives one-tick wait
        (False, True),  # primary route survives one-tick wait
        (False, True),  # hard authority/safety gate
    )
    for index, values in enumerate(dimensions):
        (irreversibility, loss), p_bad, accuracy, wait_cost, deadline, alt_now, alt_after, primary_after, gate = values
        yield {
            "case_id": f"case-{index:04d}", "irreversibility": irreversibility,
            "loss": loss, "p_bad": p_bad, "accuracy": accuracy,
            "wait_cost": wait_cost, "deadline_slack": deadline,
            "alternative_now": alt_now, "alternative_after": alt_after,
            "primary_survives": primary_after, "gate_open": gate,
        }


def evaluate(case):
    immediate_primary = primary_value(case["p_bad"], case["loss"]) if case["gate_open"] else None
    immediate_value, immediate_action = best_action(
        immediate_primary, case["gate_open"] and case["alternative_now"])
    full_probe, full_branches = probe_value(case, include_alternative=True)
    primary_probe, primary_branches = probe_value(case, include_alternative=False)
    reference_value = max(immediate_value, full_probe if full_probe is not None else F(-10**9))

    safety_action, safety_value = immediate_action, immediate_value
    evsi = primary_only_evsi(case) if case["gate_open"] else F(0)
    if full_probe is not None and evsi > case["wait_cost"]:
        voi_action, voi_value, voi_branches = "WAIT_PROBE", full_probe, full_branches
    else:
        voi_action, voi_value, voi_branches = immediate_action, immediate_value, []

    if full_probe is not None and full_probe > immediate_value:
        option_action, option_value, option_branches = "WAIT_PROBE", full_probe, full_branches
    else:
        option_action, option_value, option_branches = immediate_action, immediate_value, []

    option_without_alt = max(immediate_value, primary_probe if primary_probe is not None else F(-10**9))
    option_premium = reference_value - option_without_alt
    probe_selected = option_action == "WAIT_PROBE"
    route_deadline_loss = int(probe_selected and not case["primary_survives"])
    primary_commit = int(option_action == "PRIMARY")
    gated_commit_violations = int(not case["gate_open"] and any(
        item["action"] == "PRIMARY" for item in option_branches))
    return {
        "case_id": case["case_id"], "irreversibility": case["irreversibility"],
        "p_bad": frac(case["p_bad"]), "probe_accuracy": frac(case["accuracy"]),
        "wait_cost": frac(case["wait_cost"]), "deadline_slack": case["deadline_slack"],
        "alternative_now": case["alternative_now"], "alternative_after": case["alternative_after"],
        "primary_survives": case["primary_survives"], "gate_open": case["gate_open"],
        "evsi_primary_only": frac(evsi), "option_premium_vs_primary_only": frac(option_premium),
        "reference_value": frac(reference_value),
        "safety_only": {"action": safety_action, "value": frac(safety_value),
                         "regret": frac(reference_value - safety_value)},
        "voi_only": {"action": voi_action, "value": frac(voi_value),
                     "regret": frac(reference_value - voi_value), "branches": voi_branches},
        "option_aware": {"action": option_action, "value": frac(option_value),
                         "regret": frac(reference_value - option_value), "branches": option_branches},
        "option_probe_induced_primary_deadline_loss": route_deadline_loss,
        "option_primary_commit": primary_commit,
        "hard_gate_violations": gated_commit_violations,
    }


def main():
    cases = list(make_cases())
    rows = [evaluate(case) for case in cases]
    print(json.dumps({
        "schema": "issue-5428-real-option-t1-v1",
        "scenario_count": len(rows), "latent_states_per_case": 2,
        "probe_signals_per_case": 2, "randomness": "none",
        "policies": ["SAFETY_ONLY", "VOI_ONLY", "OPTION_AWARE_ONE_STEP"],
        "constants": {"good_utility": frac(GOOD_UTILITY), "safe_alternative_utility": frac(ALT_UTILITY)},
        "runs": rows,
    }, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
