#!/usr/bin/env python3
"""Exact tiny-horizon synthetic restless-stream scheduling fixture."""
from __future__ import annotations

from fractions import Fraction
import hashlib
import itertools
import json
import sys
from pathlib import Path

HORIZON = 4
STARVATION_CAP = 3
FALSE_CONFIDENCE_CAP = Fraction(3, 2)
MANDATORY_SENTINEL = "mandatory-focus-lease-cancel-v1"

CASES = {
    "independent_train": {
        "p01": [Fraction(9, 10), Fraction(1, 20), Fraction(3, 10)],
        "p10": [Fraction(2, 5), Fraction(1, 20), Fraction(3, 10)],
        "initial": [0, 1, 0], "weights": [3, 2, 1], "independent": True, "stationary_mode": True, "known_transition": True,
    },
    "independent_heldout": {
        "p01": [Fraction(9, 10), Fraction(1, 10), Fraction(1, 5)],
        "p10": [Fraction(2, 5), Fraction(1, 10), Fraction(1, 4)],
        "initial": [0, 1, 1], "weights": [3, 2, 1], "independent": True, "stationary_mode": True, "known_transition": True,
    },
    "coupled_common_cause": {
        "p01": [Fraction(1, 3)] * 3, "p10": [Fraction(1, 3)] * 3,
        "initial": [0, 0, 0], "weights": [3, 2, 1], "independent": False, "stationary_mode": True, "known_transition": True,
    },
    "mode_switch": {
        "p01": [Fraction(1, 4)] * 3, "p10": [Fraction(1, 4)] * 3,
        "initial": [0, 1, 0], "weights": [3, 2, 1], "independent": True, "stationary_mode": False, "known_transition": True,
    },
    "unknown_transition": {
        "p01": [Fraction(1, 3)] * 3, "p10": [Fraction(1, 3)] * 3,
        "initial": [0, 1, 0], "weights": [3, 2, 1], "independent": True, "stationary_mode": True, "known_transition": False,
    },
}

POLICIES = ("cyclic", "aoi", "entropy", "belief_value")


def transition(p: Fraction, p01: Fraction, p10: Fraction) -> Fraction:
    return p * (1 - p10) + (1 - p) * p01


def paths(case_id: str, spec: dict):
    initial, p01, p10 = spec["initial"], spec["p01"], spec["p10"]
    if case_id == "coupled_common_cause":
        for seq in itertools.product((0, 1), repeat=HORIZON):
            prior = initial[0]
            probability = Fraction(1)
            for state in seq:
                prob1 = p01[0] if prior == 0 else 1 - p10[0]
                probability *= prob1 if state else 1 - prob1
                prior = state
            if probability:
                yield tuple(seq for _ in initial), probability
        return
    per_stream = []
    for index, start in enumerate(initial):
        seqs = []
        for seq in itertools.product((0, 1), repeat=HORIZON):
            prior = start
            probability = Fraction(1)
            for tick, state in enumerate(seq):
                if case_id == "mode_switch" and tick >= 2:
                    up, down = Fraction(3, 4), Fraction(1, 4)
                else:
                    up, down = p01[index], p10[index]
                prob1 = up if prior == 0 else 1 - down
                probability *= prob1 if state else 1 - prob1
                prior = state
            if probability:
                seqs.append((seq, probability))
        per_stream.append(seqs)
    for joint in itertools.product(*per_stream):
        state_paths = tuple(item[0] for item in joint)
        probability = Fraction(1)
        for item in joint:
            probability *= item[1]
        yield state_paths, probability


def entropy_rank(p: Fraction) -> Fraction:
    # Binary entropy is strictly increasing in p(1-p); use exact rational ranking.
    return p * (1 - p)


def choose(policy: str, beliefs: list[Fraction], ages: list[int], tick: int, weights: list[int]) -> int:
    if policy == "cyclic":
        return tick % len(beliefs)
    if policy == "aoi":
        return max(range(len(ages)), key=lambda i: (ages[i], -i))
    if policy == "entropy":
        return max(range(len(beliefs)), key=lambda i: (entropy_rank(beliefs[i]), -i))
    overdue = [i for i, age in enumerate(ages) if age >= STARVATION_CAP - 1]
    if overdue:
        return max(overdue, key=lambda i: (ages[i], -i))
    return max(range(len(beliefs)), key=lambda i: (weights[i] * beliefs[i], -i))


def simulate_case(case_id: str, spec: dict, policy: str) -> dict:
    supported = spec["independent"] and spec["stationary_mode"] and spec["known_transition"]
    effective = policy if policy != "belief_value" or supported else "cyclic"
    total_miss = Fraction(0)
    total_false = Fraction(0)
    action_mass = [Fraction(0) for _ in spec["initial"]]
    max_starve = 0
    path_count = 0
    mass = Fraction(0)
    path_digest = hashlib.sha256()
    for state_paths, prob in paths(spec.get("case_id", ""), spec):
        path_count += 1
        mass += prob
        beliefs = [transition(Fraction(x), a, b) for x, a, b in zip(spec["initial"], spec["p01"], spec["p10"])]
        ages = [0] * len(beliefs)
        miss = Fraction(0)
        false = Fraction(0)
        path_starve = 0
        action_sequence = []
        for tick in range(HORIZON):
            chosen = choose(effective, beliefs, ages, tick, spec["weights"])
            action_sequence.append(chosen)
            action_mass[chosen] += prob
            for i, weight in enumerate(spec["weights"]):
                state = state_paths[i][tick]
                if i != chosen:
                    if state == 1:
                        miss += weight
                    if (beliefs[i] >= Fraction(9, 10) and state == 0) or (beliefs[i] <= Fraction(1, 10) and state == 1):
                        false += 1
            ages = [0 if i == chosen else age + 1 for i, age in enumerate(ages)]
            max_starve = max(max_starve, *ages)
            path_starve = max(path_starve, *ages)
            beliefs = [transition(Fraction(state_paths[i][tick]) if i == chosen else beliefs[i], *( (Fraction(3, 4), Fraction(1, 4)) if case_id == "mode_switch" and tick >= 2 else (spec["p01"][i], spec["p10"][i]) )) for i in range(len(beliefs))]
        total_miss += prob * miss
        total_false += prob * false
        path_payload = {"states": state_paths, "probability": frac(prob), "actions": action_sequence, "weighted_miss": frac(miss), "false_confidence": frac(false), "max_starvation": path_starve}
        path_digest.update(json.dumps(path_payload, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n")
        total_ticks = HORIZON
    return {
        "declared_policy": policy,
        "effective_policy": effective,
        "index_claim": False,
        "expected_weighted_misses": frac(total_miss),
        "expected_false_confidence": frac(total_false) if supported else None,
        "max_starvation": max_starve,
        "captures": total_ticks,
        "action_mass": [frac(v) for v in action_mass],
        "enumerated_worlds": path_count,
        "probability_mass": frac(mass),
        "world_result_sha256": path_digest.hexdigest(),
        "mandatory_sentinel": MANDATORY_SENTINEL,
    }


def frac(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def analytic_entropy_check() -> dict:
    p01, p10 = Fraction(9, 10), Fraction(2, 5)
    p = Fraction(0)
    beliefs = []
    for _ in range(3):
        p = transition(p, p01, p10)
        beliefs.append(p)
    ranks = [entropy_rank(value) for value in beliefs]
    return {"beliefs": [frac(v) for v in beliefs], "entropy_rank_exact": [frac(v) for v in ranks], "age2_gt_age3": ranks[1] > ranks[2]}


def main(output: str) -> None:
    records = []
    for case_id, spec in CASES.items():
        spec = {**spec, "case_id": case_id}
        unsupported = not (spec["independent"] and spec["stationary_mode"] and spec["known_transition"])
        policies = POLICIES if not unsupported else ("cyclic", "belief_value")
        records.append({
            "case_id": case_id,
            "stream_count": len(spec["initial"]),
            "horizon": HORIZON,
            "weights": spec["weights"],
            "support_flags": {"independent": spec["independent"], "stationary_mode": spec["stationary_mode"], "known_transition": spec["known_transition"]},
            "fallback_required": unsupported,
            "opportunity_definition": "synthetic_evaluator_truth_state_equals_one",
            "observation_boundary": "policy_receives_selected_stream_state_only",
            "oracle_truth_scope": "auditor_only",
            "policies": [simulate_case(case_id, spec, policy) for policy in policies],
            "analytic_entropy_control": analytic_entropy_check(),
        })
    with Path(output).open("w", encoding="utf-8", newline="\n") as stream:
        for record in records:
            stream.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps({"cases": len(records), "policy_case_rows": len(records) * len(POLICIES), "output": output}, sort_keys=True))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python simulate.py OUTPUT.jsonl")
    main(sys.argv[1])
