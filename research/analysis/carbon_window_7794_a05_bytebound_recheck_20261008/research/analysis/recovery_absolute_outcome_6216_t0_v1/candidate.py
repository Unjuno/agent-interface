#!/usr/bin/env python3
"""Candidate exact calculations for Issue #6216's finite T0 method fixture."""
import json
import math
from pathlib import Path


def binomial_mass(n, p_num, den):
    return [math.comb(n, k) * p_num**k * (den - p_num) ** (n - k) for k in range(n + 1)]


def regime_result(n, probs, den):
    a = binomial_mass(n, probs["A"], den)
    b = binomial_mass(n, probs["B"], den)
    win_a = sum(a[i] * b[j] for i in range(n + 1) for j in range(n + 1) if i > j)
    win_b = sum(a[i] * b[j] for i in range(n + 1) for j in range(n + 1) if i < j)
    tie = sum(a[i] * b[i] for i in range(n + 1))
    denom = den ** (2 * n)
    # A tie is broken uniformly only for the separate expected-held-out metric.
    selected_a_num = 2 * win_a + tie
    selected_b_num = 2 * win_b + tie
    held_out_num = selected_a_num * probs["A"] + selected_b_num * probs["B"]
    held_out_den = 2 * denom * den
    zero_num = (den - probs["A"]) ** n * (den - probs["B"]) ** n
    agreement_num = win_a * win_a + win_b * win_b + tie * tie
    return {
        "sample_size": n,
        "winner_set_counts": {"A": win_a, "B": win_b, "TIE_AB": tie},
        "winner_set_denominator": denom,
        "agreement_probability": {"numerator": agreement_num, "denominator": denom * denom},
        "all_zero": {"numerator": zero_num, "denominator": denom},
        "pooled_success": {"numerator": probs["A"] + probs["B"], "denominator": 2 * den},
        "expected_held_out_success": {"numerator": held_out_num, "denominator": held_out_den}
    }


def checkpoint_result(data):
    binding = data["checkpoint_binding"]
    gold = binding["gold_action_by_checkpoint"]
    result = {}
    for arm in ("base", "permuted"):
        rows = binding[arm]
        correct = sum(rows[c][gold[c]] for c in gold)
        marginals = {a: sum(rows[c][a] for c in rows) for a in ("A", "B")}
        result[arm] = {"correct": correct, "checkpoints": len(gold), "marginal_successes": marginals}
    return result


def control_result(data):
    c = data["controls"]
    selective = c["selective_labels"]["proposals"]
    n = len(selective)
    known_positive = sum(x["endpoint"] == 1 and x["gate"] == "ACCEPT" for x in selective)
    unresolved_or_missing = sum(x["endpoint"] in ("UNKNOWN", "MISSING") for x in selective)
    stable = c["stable_high"]
    stable_rate = sum(stable["candidate_successes"].values())
    return {
        "stable_high": {"successes": stable_rate, "trials": 2 * stable["trials"], "pass": stable_rate > stable["trials"]},
        "yield_correct": c["yield_correct"]["recommended_disposition"] == "YIELD" and c["yield_correct"]["yield_is_correct"] and not c["yield_correct"]["safe_candidates"],
        "forbidden_effect_refused": c["forbidden_effect"]["success"] and c["forbidden_effect"]["forbidden_effect"] and not c["forbidden_effect"]["admissible"] and c["forbidden_effect"]["required_disposition"] == "REJECT",
        "selective_labels": {
            "N": n,
            "Y": known_positive,
            "M_plus_R": unresolved_or_missing,
            "lower": {"numerator": known_positive, "denominator": n},
            "upper": {"numerator": known_positive + unresolved_or_missing, "denominator": n},
            "rejected_outcomes_imputed": False
        }
    }


def run(data):
    den = data["probability_denominator"]
    regimes = {r["id"]: r["success_numerators"] for r in data["regimes"]}
    matrix = {name: [regime_result(n, probs, den) for n in data["samples_per_candidate"]] for name, probs in regimes.items()}
    return {
        "schema": "recovery-absolute-outcome-candidate-v1",
        "regimes": matrix,
        "checkpoint_binding": checkpoint_result(data),
        "controls": control_result(data),
        "scope": "exact synthetic method fixture only; no live recovery or product claim"
    }


if __name__ == "__main__":
    here = Path(__file__).resolve().parent
    frozen = json.loads((here / "input.json").read_text(encoding="utf-8"))
    (here / "candidate.json").write_text(json.dumps(run(frozen), sort_keys=True, indent=2) + "\n", encoding="utf-8")
