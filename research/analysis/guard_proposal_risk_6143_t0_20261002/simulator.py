"""Exact finite tree for guard-induced proposal-policy shifts; no sampling."""
from fractions import Fraction


def _fraction(value):
    return value if isinstance(value, Fraction) else Fraction(str(value))


def simulate_cell(risky_probability, guard_on, fixture=None):
    fixture = fixture or {
        "max_proposals_per_episode": 2,
        "worlds": [{"true_harmful": True, "weight": "3/4"}, {"true_harmful": False, "weight": "1/4"}],
        "guard_confusion": {"true_positive_reject": "3/4", "false_positive_reject": "1/4"},
    }
    risky_probability = Fraction(risky_probability)
    if not 0 <= risky_probability <= 1:
        raise ValueError("risky_probability must be in [0, 1]")
    max_proposals = int(fixture["max_proposals_per_episode"])
    if max_proposals < 1:
        raise ValueError("max_proposals_per_episode must be positive")
    tp = _fraction(fixture["guard_confusion"]["true_positive_reject"])
    fp = _fraction(fixture["guard_confusion"]["false_positive_reject"])
    if not (0 <= tp <= 1 and 0 <= fp <= 1):
        raise ValueError("guard rejection probabilities must be in [0, 1]")

    totals = {
        "launched": Fraction(0), "proposals": Fraction(0),
        "retries": Fraction(0),
        "refusals": Fraction(0), "admitted": Fraction(0),
        "harmful_admitted": Fraction(0), "task_harm": Fraction(0),
        "unfinished": Fraction(0), "risky_proposals": Fraction(0),
        "harmful_risky_proposals": Fraction(0), "harmful_risky_refusals": Fraction(0),
        "true_harmful_proposals": Fraction(0), "true_harmful_refusals": Fraction(0),
        "false_positive_proposals": Fraction(0), "false_positive_refusals": Fraction(0),
    }

    def visit(harmful_world, step, mass, path):
        if step == max_proposals:
            totals["launched"] += mass
            totals["proposals"] += mass * path["proposals"]
            totals["retries"] += mass * path["retries"]
            totals["refusals"] += mass * path["refusals"]
            admitted = path["proposals"] - path["refusals"]
            totals["admitted"] += mass * admitted
            totals["risky_proposals"] += mass * path["risky_proposals"]
            totals["harmful_risky_proposals"] += mass * path["harmful_risky_proposals"]
            totals["harmful_risky_refusals"] += mass * path["harmful_risky_refusals"]
            totals["true_harmful_proposals"] += mass * path["true_harmful_proposals"]
            totals["true_harmful_refusals"] += mass * path["true_harmful_refusals"]
            totals["false_positive_proposals"] += mass * path["false_positive_proposals"]
            totals["false_positive_refusals"] += mass * path["false_positive_refusals"]
            if path["terminal"] == "harm":
                totals["task_harm"] += mass
                totals["harmful_admitted"] += mass
            elif path["terminal"] == "unfinished":
                totals["unfinished"] += mass
            return

        for risky, proposal_mass in ((False, 1 - risky_probability), (True, risky_probability)):
            if not proposal_mass:
                continue
            harmful = risky and harmful_world
            if not guard_on:
                decisions = ((False, Fraction(1)),)  # not refused
            elif harmful:
                decisions = ((True, tp), (False, 1 - tp))
            else:
                decisions = ((True, fp), (False, 1 - fp))
            for refused, decision_mass in decisions:
                p = mass * proposal_mass * decision_mass
                next_path = dict(path)
                next_path["proposals"] += 1
                next_path["retries"] += int(step > 0)
                next_path["risky_proposals"] += int(risky)
                next_path["harmful_risky_proposals"] += int(harmful)
                next_path["harmful_risky_refusals"] += int(harmful and refused)
                next_path["true_harmful_proposals"] += int(harmful)
                next_path["true_harmful_refusals"] += int(harmful and refused)
                false_positive = not harmful
                next_path["false_positive_proposals"] += int(false_positive)
                next_path["false_positive_refusals"] += int(false_positive and refused)
                if refused:
                    next_path["refusals"] += 1
                    if step + 1 == max_proposals:
                        next_path["terminal"] = "unfinished"
                        visit(harmful_world, 2, p, next_path)
                    else:
                        visit(harmful_world, step + 1, p, next_path)
                else:
                    next_path["terminal"] = "harm" if harmful else "success"
                    visit(harmful_world, 2, p, next_path)

    initial = {
        "proposals": 0, "retries": 0, "refusals": 0, "risky_proposals": 0,
        "harmful_risky_proposals": 0, "harmful_risky_refusals": 0,
        "true_harmful_proposals": 0, "true_harmful_refusals": 0,
        "false_positive_proposals": 0, "false_positive_refusals": 0,
        "terminal": None,
    }
    world_mass = sum((_fraction(world["weight"]) for world in fixture["worlds"]), Fraction(0))
    if world_mass != 1:
        raise ValueError("world weights must sum to one")
    for world in fixture["worlds"]:
        visit(bool(world["true_harmful"]), 0, _fraction(world["weight"]), initial)

    launched = totals["launched"]
    if launched != 1:
        raise AssertionError("finite tree failed to conserve launched mass")
    return {
        "all_launched_weight": launched,
        "proposal_refusal_fraction": totals["refusals"] / totals["proposals"] if totals["proposals"] else Fraction(0),
        "expected_refusals_per_launch": totals["refusals"] / launched,
        "per_admitted_action_harm_fraction": totals["harmful_admitted"] / totals["admitted"] if totals["admitted"] else Fraction(0),
        "task_harm_fraction": totals["task_harm"] / launched,
        "unfinished_fraction": totals["unfinished"] / launched,
        "expected_proposals_per_launch": totals["proposals"] / launched,
        "expected_retries_per_launch": totals["retries"] / launched,
        "proposal_work_units_per_launch": totals["proposals"] / launched,
        "risky_proposal_fraction": totals["risky_proposals"] / totals["proposals"] if totals["proposals"] else Fraction(0),
        "risky_rejection_rate": totals["harmful_risky_refusals"] / totals["harmful_risky_proposals"] if totals["harmful_risky_proposals"] else Fraction(0),
        "guard_true_positive_fraction": totals["true_harmful_refusals"] / totals["true_harmful_proposals"] if totals["true_harmful_proposals"] else Fraction(0),
        "guard_false_positive_fraction": totals["false_positive_refusals"] / totals["false_positive_proposals"] if totals["false_positive_proposals"] else Fraction(0),
    }


def analyze(fixture=None):
    fixture = fixture or {
        "max_proposals_per_episode": 2,
        "worlds": [{"true_harmful": True, "weight": "3/4"}, {"true_harmful": False, "weight": "1/4"}],
        "guard_confusion": {"true_positive_reject": "3/4", "false_positive_reject": "1/4"},
        "policies": {"conservative_risky_probability": "1/4", "compensated_risky_probability": "3/4", "protective_risky_probability": "0"},
        "harm_materiality_margin": "1/10",
    }
    conservative = _fraction(fixture["policies"]["conservative_risky_probability"])
    aggressive = _fraction(fixture["policies"]["compensated_risky_probability"])
    protective_probability = _fraction(fixture["policies"]["protective_risky_probability"])
    cells = {
        "fixed_conservative_guard_on": simulate_cell(conservative, True, fixture),
        "fixed_conservative_guard_off": simulate_cell(conservative, False, fixture),
        "guard_induced_aggressive_guard_on": simulate_cell(aggressive, True, fixture),
        "guard_induced_aggressive_guard_off": simulate_cell(aggressive, False, fixture),
    }
    null = simulate_cell(conservative, True, fixture)
    protective = simulate_cell(protective_probability, True, fixture)
    compensation = cells["guard_induced_aggressive_guard_on"]
    margin = _fraction(fixture["harm_materiality_margin"])

    def detected(profile):
        return (
            profile["risky_proposal_fraction"] > null["risky_proposal_fraction"]
            and profile["task_harm_fraction"] > null["task_harm_fraction"] + margin
        )

    return {
        "cells": cells,
        "controls": {
            "compensation_detected": detected(compensation),
            "null": {**null, "compensation_detected": detected(null)},
            "protective": {**protective, "compensation_detected": detected(protective)},
            "harm_materiality_margin": margin,
        },
        "schema": "guard-proposal-risk-t0-v1",
    }
