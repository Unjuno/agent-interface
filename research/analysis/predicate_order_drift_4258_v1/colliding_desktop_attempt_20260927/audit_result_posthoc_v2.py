"""Forensic audit against FREEZE.json; never used to alter/re-run allocation."""
from fractions import Fraction
from itertools import product
from collections import Counter, defaultdict
import json
import os
from pathlib import Path

ROOT = Path(__file__).parent
FREEZE = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
RESULTS = Path(os.environ.get("AI_PREDICATE_DRIFT_RESULTS", "/out"))
RAW = json.loads((RESULTS / "raw.json").read_text(encoding="utf-8"))
NAMES = tuple(FREEZE["predicates"])
COST = FREEZE["positive_costs"]
FALSE_P = {k: Fraction(v) for k, v in FREEZE["development_false_probability"].items()}
NAIVE = tuple(FREEZE["naive_order"])
STATES = [dict(zip(NAMES, bits)) for bits in product((False, True), repeat=len(NAMES))]


def skey(state):
    return "".join("1" if state[n] else "0" for n in NAMES)


def fmt(number):
    return f"{number.numerator}/{number.denominator}"


def mass_of(state):
    result = Fraction(1)
    for name in NAMES:
        result *= (FALSE_P[name] if not state[name] else 1 - FALSE_P[name])
    return result


def row_cost(state, order):
    total = 0
    tests = 0
    for name in order:
        total += COST[name]
        tests += 1
        if not state[name]:
            return total, tests, False
    return total, tests, True


def inspect():
    issues = []
    expected_order = tuple(sorted(NAMES, key=lambda n: (Fraction(COST[n], 1) / FALSE_P[n], n)))
    if tuple(RAW.get("learned_order", ())) != expected_order:
        issues.append({"check": "learned_order_matches_frozen_false_probability_rule",
                       "expected": list(expected_order), "observed": RAW.get("learned_order")})
    source, destination = FREEZE["drift_source_state"], FREEZE["drift_destination_state"]
    base = {skey(s): mass_of(s) for s in STATES}
    source_mass = base[skey(source)]
    if RAW.get("source_mass") != fmt(source_mass):
        issues.append({"check": "source_mass_matches_frozen_distribution",
                       "expected": fmt(source_mass), "observed": RAW.get("source_mass")})
    if len(RAW.get("grid_points", [])) != 11:
        issues.append({"check": "frozen_grid_has_11_points", "observed": len(RAW.get("grid_points", []))})
    for index, point in enumerate(RAW.get("grid_points", [])):
        delta = source_mass * Fraction(index, 10)
        expected_weights = dict(base)
        expected_weights[skey(source)] -= delta
        expected_weights[skey(destination)] += delta
        if point.get("step") != index or point.get("delta_mass") != fmt(delta):
            issues.append({"check": "grid_step_and_delta", "step": index})
        for label, order in (("naive", NAIVE), ("learned", expected_order)):
            section = point.get(label, {})
            observed = {skey(x["state"]): x for x in section.get("rows", [])}
            if len(observed) != 16 or set(observed) != set(expected_weights):
                issues.append({"check": "all_16_unique_states", "step": index, "order": label})
                continue
            total_cost = Fraction()
            total_tests = Fraction()
            bins = []
            for state in STATES:
                k = skey(state)
                item = observed[k]
                weight = expected_weights[k]
                cost, tests, decision = row_cost(state, order)
                if item.get("mass") != fmt(weight):
                    issues.append({"check": "row_mass_matches_frozen_distribution", "step": index,
                                   "order": label, "state": k, "expected": fmt(weight),
                                   "observed": item.get("mass")})
                if item.get("cost") != cost or item.get("evaluations") != tests:
                    issues.append({"check": "row_cost_and_test_count_match_frozen_order",
                                   "step": index, "order": label, "state": k,
                                   "expected": [cost, tests],
                                   "observed": [item.get("cost"), item.get("evaluations")]})
                if item.get("decision") is not decision or decision is not all(state.values()):
                    issues.append({"check": "exact_AND_semantics", "step": index,
                                   "order": label, "state": k})
                total_cost += weight * cost
                total_tests += weight * tests
                bins.append((cost, weight))
            for pct in (50, 95, 99):
                threshold = sum((w for _, w in bins), Fraction()) * Fraction(pct, 100)
                running = Fraction()
                quantile = None
                for value, weight in sorted(bins):
                    running += weight
                    if running >= threshold:
                        quantile = value
                        break
                if section.get(f"p{pct}_cost") != quantile:
                    issues.append({"check": f"p{pct}_weighted_nearest_rank", "step": index,
                                   "order": label, "expected": quantile,
                                   "observed": section.get(f"p{pct}_cost")})
            if section.get("expected_cost") != fmt(total_cost):
                issues.append({"check": "exact_expected_weighted_cost", "step": index,
                               "order": label, "expected": fmt(total_cost),
                               "observed": section.get("expected_cost")})
            if section.get("expected_evaluations") != fmt(total_tests):
                issues.append({"check": "exact_expected_evaluations", "step": index,
                               "order": label, "expected": fmt(total_tests),
                               "observed": section.get("expected_evaluations")})
    counts = Counter(item["check"] for item in issues)
    examples = defaultdict(list)
    for item in issues:
        if len(examples[item["check"]]) < 2:
            examples[item["check"]].append(item)
    summary = [{"check": name, "count": count, "examples": examples[name]}
               for name, count in sorted(counts.items())]
    return {"allocation_status": "STOP_SOURCE_IMAGE_OR_AUDIT",
            "error_count": len(issues), "error_classes": summary,
            "first_attempt_preserved": True,
            "rerun_performed": False,
            "independent_specification": "FREEZE.json, interpreting development_false_probability as P(predicate=false)",
            "scope": "Forensic posthoc classification only; no new experimental invocation."}


if __name__ == "__main__":
    target = RESULTS / "audit_posthoc_v2.json"
    target.write_text(json.dumps(inspect(), indent=2) + "\n", encoding="utf-8")
