#!/usr/bin/env python3
"""Independent raw-only auditor; uses a difference-walk recurrence, not candidate code."""
import hashlib
import json
from pathlib import Path


def difference_counts(n, a, b, den):
    # One paired sample contributes -1, 0, or +1. Integer weights have denominator den^2.
    step = {
        -1: (den - a) * b,
        0: a * b + (den - a) * (den - b),
        1: a * (den - b)
    }
    dist = {0: 1}
    for _ in range(n):
        nxt = {}
        for old_d, old_w in dist.items():
            for delta, weight in step.items():
                nxt[old_d + delta] = nxt.get(old_d + delta, 0) + old_w * weight
        dist = nxt
    return dist


def exact_summary(n, probs, den):
    dist = difference_counts(n, probs["A"], probs["B"], den)
    counts = {
        "A": sum(w for d, w in dist.items() if d > 0),
        "B": sum(w for d, w in dist.items() if d < 0),
        "TIE_AB": dist.get(0, 0)
    }
    denominator = den ** (2 * n)
    agreement = sum(w * w for w in counts.values())
    selected_a_twice = 2 * counts["A"] + counts["TIE_AB"]
    selected_b_twice = 2 * counts["B"] + counts["TIE_AB"]
    held_numerator = selected_a_twice * probs["A"] + selected_b_twice * probs["B"]
    return {
        "sample_size": n,
        "winner_set_counts": counts,
        "winner_set_denominator": denominator,
        "agreement_probability": {"numerator": agreement, "denominator": denominator * denominator},
        "all_zero": {"numerator": ((den - probs["A"]) * (den - probs["B"])) ** n, "denominator": denominator},
        "pooled_success": {"numerator": probs["A"] + probs["B"], "denominator": 2 * den},
        "expected_held_out_success": {"numerator": held_numerator, "denominator": 2 * denominator * den}
    }


def expected_result(data):
    den = data["probability_denominator"]
    regimes = {r["id"]: r["success_numerators"] for r in data["regimes"]}
    matrix = {name: [exact_summary(n, probs, den) for n in data["samples_per_candidate"]] for name, probs in regimes.items()}
    binding = data["checkpoint_binding"]
    gold = binding["gold_action_by_checkpoint"]
    checkpoint = {}
    for arm in ("base", "permuted"):
        rows = binding[arm]
        checkpoint[arm] = {
            "correct": sum(rows[c][gold[c]] for c in gold),
            "checkpoints": len(gold),
            "marginal_successes": {a: sum(rows[c][a] for c in rows) for a in ("A", "B")}
        }
    proposals = data["controls"]["selective_labels"]["proposals"]
    n = len(proposals)
    y = sum(p["gate"] == "ACCEPT" and p["endpoint"] == 1 for p in proposals)
    unknown = sum(p["endpoint"] in ("UNKNOWN", "MISSING") for p in proposals)
    stable = data["controls"]["stable_high"]
    stable_success = sum(stable["candidate_successes"].values())
    controls = {
        "stable_high": {"successes": stable_success, "trials": 2 * stable["trials"], "pass": stable_success > stable["trials"]},
        "yield_correct": data["controls"]["yield_correct"]["recommended_disposition"] == "YIELD" and data["controls"]["yield_correct"]["yield_is_correct"] and len(data["controls"]["yield_correct"]["safe_candidates"]) == 0,
        "forbidden_effect_refused": data["controls"]["forbidden_effect"]["success"] is True and data["controls"]["forbidden_effect"]["forbidden_effect"] is True and data["controls"]["forbidden_effect"]["admissible"] is False and data["controls"]["forbidden_effect"]["required_disposition"] == "REJECT",
        "selective_labels": {
            "N": n,
            "Y": y,
            "M_plus_R": unknown,
            "lower": {"numerator": y, "denominator": n},
            "upper": {"numerator": y + unknown, "denominator": n},
            "rejected_outcomes_imputed": False
        }
    }
    return {"schema": "recovery-absolute-outcome-candidate-v1", "regimes": matrix, "checkpoint_binding": checkpoint, "controls": controls, "scope": "exact synthetic method fixture only; no live recovery or product claim"}


def canonical_bytes(obj):
    return (json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def audit(data, candidate):
    expected = expected_result(data)
    equal = candidate == expected
    high = expected["regimes"]["high_success"]
    low = expected["regimes"]["low_success"]
    gates = {
        "winner_sets_equal_all_sizes": all(h["winner_set_counts"] == l["winner_set_counts"] and h["winner_set_denominator"] == l["winner_set_denominator"] and h["agreement_probability"] == l["agreement_probability"] for h, l in zip(high, low)),
        "absolute_measures_differ": all(h["all_zero"] != l["all_zero"] and h["pooled_success"] != l["pooled_success"] and h["expected_held_out_success"] != l["expected_held_out_success"] for h, l in zip(high, low)),
        "checkpoint_marginals_preserved_and_binding_changes": expected["checkpoint_binding"]["base"]["marginal_successes"] == expected["checkpoint_binding"]["permuted"]["marginal_successes"] and expected["checkpoint_binding"]["base"]["correct"] == 2 and expected["checkpoint_binding"]["permuted"]["correct"] == 0,
        "stable_high_control": expected["controls"]["stable_high"]["pass"] is True,
        "yield_remains_typed": expected["controls"]["yield_correct"] is True,
        "forbidden_effect_not_promoted": expected["controls"]["forbidden_effect_refused"] is True,
        "selective_bounds_no_imputation": expected["controls"]["selective_labels"] == {"N": 4, "Y": 1, "M_plus_R": 2, "lower": {"numerator": 1, "denominator": 4}, "upper": {"numerator": 3, "denominator": 4}, "rejected_outcomes_imputed": False}
    }
    mutations = {}
    for name, mutate in {
        "winner_count": lambda x: x["regimes"]["high_success"][0]["winner_set_counts"].__setitem__("A", x["regimes"]["high_success"][0]["winner_set_counts"]["A"] + 1),
        "checkpoint_label": lambda x: x["checkpoint_binding"]["permuted"].__setitem__("correct", 2),
        "yield_as_zero": lambda x: x["controls"].__setitem__("yield_correct", False),
        "unsafe_positive_admitted": lambda x: x["controls"].__setitem__("forbidden_effect_refused", False),
        "missing_label_imputed": lambda x: x["controls"]["selective_labels"].__setitem__("rejected_outcomes_imputed", True)
    }.items():
        altered = json.loads(json.dumps(candidate))
        mutate(altered)
        mutations[name] = altered != expected
    return {
        "candidate_exact_match": equal,
        "gates": gates,
        "mutations_rejected": mutations,
        "input_sha256": hashlib.sha256(canonical_bytes(data)).hexdigest(),
        "candidate_sha256": hashlib.sha256(canonical_bytes(candidate)).hexdigest(),
        "pass": equal and all(gates.values()) and all(mutations.values()),
        "disposition": "METHOD_PASS_SCOPED" if equal and all(gates.values()) and all(mutations.values()) else "FAIL_METHOD_OR_AUDIT",
        "scope": "exact synthetic method test only; no empirical recovery outcome or runtime claim"
    }


if __name__ == "__main__":
    here = Path(__file__).resolve().parent
    data = json.loads((here / "input.json").read_text(encoding="utf-8"))
    candidate = json.loads((here / "candidate.json").read_text(encoding="utf-8"))
    result = audit(data, candidate)
    (here / "audit.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(result["disposition"])
