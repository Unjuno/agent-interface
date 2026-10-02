"""Independent iterative replay. Does not import the candidate simulator."""
from fractions import Fraction
import argparse
import json


def frac(value):
    return Fraction(str(value))


def encode(value):
    if isinstance(value, Fraction):
        return str(value)
    if isinstance(value, dict):
        return {key: encode(item) for key, item in value.items()}
    return value


def replay_cell(fixture, risk_rate, guarded):
    max_steps = fixture["max_proposals_per_episode"]
    tp = frac(fixture["guard_confusion"]["true_positive_reject"])
    fp = frac(fixture["guard_confusion"]["false_positive_reject"])
    paths = []
    for world in fixture["worlds"]:
        paths.append({
            "mass": frac(world["weight"]),
            "harmful_world": world["true_harmful"],
            "proposals": 0, "retries": 0, "refusals": 0, "risky_proposals": 0,
            "harmful_risky": 0, "harmful_risky_refused": 0,
            "terminal": None,
        })

    for step in range(max_steps):
        following = []
        for path in paths:
            if path["terminal"] is not None:
                following.append(path)
                continue
            proposal_options = ((False, 1 - risk_rate), (True, risk_rate))
            for is_risky, proposal_p in proposal_options:
                if proposal_p == 0:
                    continue
                harmful = is_risky and path["harmful_world"]
                if guarded:
                    refusal_p = tp if harmful else fp
                else:
                    refusal_p = Fraction(0)
                for refused, decision_p in ((True, refusal_p), (False, 1 - refusal_p)):
                    if decision_p == 0:
                        continue
                    node = dict(path)
                    node["mass"] *= proposal_p * decision_p
                    node["proposals"] += 1
                    node["retries"] += int(step > 0)
                    node["risky_proposals"] += int(is_risky)
                    node["harmful_risky"] += int(harmful)
                    node["harmful_risky_refused"] += int(harmful and refused)
                    if refused:
                        node["refusals"] += 1
                        if step == max_steps - 1:
                            node["terminal"] = "unfinished"
                    else:
                        node["terminal"] = "harm" if harmful else "success"
                    following.append(node)
        paths = following

    mass = sum((p["mass"] for p in paths), Fraction(0))
    proposals = sum((p["mass"] * p["proposals"] for p in paths), Fraction(0))
    retries = sum((p["mass"] * p["retries"] for p in paths), Fraction(0))
    refusals = sum((p["mass"] * p["refusals"] for p in paths), Fraction(0))
    risky = sum((p["mass"] * p["risky_proposals"] for p in paths), Fraction(0))
    dangerous = sum((p["mass"] * p["harmful_risky"] for p in paths), Fraction(0))
    danger_refused = sum((p["mass"] * p["harmful_risky_refused"] for p in paths), Fraction(0))
    harms = sum((p["mass"] for p in paths if p["terminal"] == "harm"), Fraction(0))
    incomplete = sum((p["mass"] for p in paths if p["terminal"] == "unfinished"), Fraction(0))
    admitted = proposals - refusals
    if mass != 1:
        raise ValueError("auditor path mass does not conserve launch denominator")
    return {
        "all_launched_weight": mass,
        "proposal_refusal_fraction": refusals / proposals if proposals else Fraction(0),
        "expected_refusals_per_launch": refusals / mass,
        "per_admitted_action_harm_fraction": harms / admitted if admitted else Fraction(0),
        "task_harm_fraction": harms / mass,
        "unfinished_fraction": incomplete / mass,
        "expected_proposals_per_launch": proposals / mass,
        "expected_retries_per_launch": retries / mass,
        "proposal_work_units_per_launch": proposals / mass,
        "risky_proposal_fraction": risky / proposals if proposals else Fraction(0),
        "risky_rejection_rate": danger_refused / dangerous if dangerous else Fraction(0),
        "guard_true_positive_fraction": danger_refused / dangerous if dangerous else Fraction(0),
        "guard_false_positive_fraction": fp if guarded else Fraction(0),
    }


def replay(fixture):
    policies = fixture["policies"]
    conservative = frac(policies["conservative_risky_probability"])
    compensated = frac(policies["compensated_risky_probability"])
    protective = frac(policies["protective_risky_probability"])
    cells = {
        "fixed_conservative_guard_on": replay_cell(fixture, conservative, True),
        "fixed_conservative_guard_off": replay_cell(fixture, conservative, False),
        "guard_induced_aggressive_guard_on": replay_cell(fixture, compensated, True),
        "guard_induced_aggressive_guard_off": replay_cell(fixture, compensated, False),
    }
    null = replay_cell(fixture, conservative, True)
    protect = replay_cell(fixture, protective, True)
    margin = frac(fixture["harm_materiality_margin"])

    def flagged(profile):
        return (
            profile["risky_proposal_fraction"] > null["risky_proposal_fraction"]
            and profile["task_harm_fraction"] > null["task_harm_fraction"] + margin
        )

    return encode({
        "cells": cells,
        "controls": {
            "compensation_detected": flagged(cells["guard_induced_aggressive_guard_on"]),
            "null": {**null, "compensation_detected": flagged(null)},
            "protective": {**protect, "compensation_detected": flagged(protect)},
            "harm_materiality_margin": margin,
        },
        "schema": "guard-proposal-risk-t0-v1",
    })


def audit(fixture, candidate):
    errors = []
    try:
        expected = replay(fixture)
        if candidate != expected:
            errors.append("candidate output differs from independent exact replay")
        controls = expected["controls"]
        if not controls["compensation_detected"]:
            errors.append("planted compensation case not detected")
        if controls["null"]["compensation_detected"]:
            errors.append("null control falsely detected as compensation")
        if controls["protective"]["compensation_detected"]:
            errors.append("protective control falsely detected as compensation")
        for cell in expected["cells"].values():
            if cell["all_launched_weight"] != "1":
                errors.append("all-launched denominator not conserved")
                break
        if expected["cells"]["guard_induced_aggressive_guard_on"]["risky_rejection_rate"] != fixture["guard_confusion"]["true_positive_reject"]:
            errors.append("conditional risky-action rejection rate disagrees with frozen TPR")
    except Exception as exc:  # audit failures are data, not an implicit pass
        expected = {}
        errors.append(f"independent replay error: {type(exc).__name__}: {exc}")
    return {
        "schema": "guard-proposal-risk-audit-v1",
        "status": "PASS_METHOD_SCOPED" if not errors else "FAIL_CANDIDATE_MISMATCH",
        "candidate_and_auditor_separate": True,
        "replayed_world_weight": "1" if not errors or expected else "0",
        "compensation_control_caught": bool(expected.get("controls", {}).get("compensation_detected")),
        "null_control_not_flagged": not bool(expected.get("controls", {}).get("null", {}).get("compensation_detected")),
        "protective_control_not_flagged": not bool(expected.get("controls", {}).get("protective", {}).get("compensation_detected")),
        "errors": errors,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    with open(args.input, encoding="utf-8") as handle:
        fixture = json.load(handle)
    with open(args.candidate, encoding="utf-8") as handle:
        candidate = json.load(handle)
    result = audit(fixture, candidate)
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps(result, sort_keys=True))
    if result["status"] != "PASS_METHOD_SCOPED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
