"""Frozen finite predicate-order drift experiment; standard library only."""
from fractions import Fraction
from itertools import product
import json
from pathlib import Path

ROOT = Path(__file__).parent
OUT = Path("/out")
NAMES = ("A", "B", "C", "D")
COST = {"A": 1, "B": 2, "C": 4, "D": 8}
Q = {"A": Fraction(1, 10), "B": Fraction(2, 5),
     "C": Fraction(9, 10), "D": Fraction(4, 5)}
NAIVE = ("A", "B", "C", "D")
STATES = [dict(zip(NAMES, bits)) for bits in product((False, True), repeat=4)]
SOURCE = {"A": True, "B": True, "C": False, "D": True}
DEST = {"A": False, "B": True, "C": True, "D": True}


def frac(value):
    return f"{value.numerator}/{value.denominator}"


def distribution(state):
    weight = Fraction(1)
    for name in NAMES:
        weight *= (1 - Q[name]) if not state[name] else Q[name]
    return weight


def row(state, order):
    spent = 0
    count = 0
    for name in order:
        spent += COST[name]
        count += 1
        if not state[name]:
            break
    return spent, count, all(state.values())


def weighted_quantile(values, percentile):
    ordered = sorted(values, key=lambda pair: pair[0])
    total = sum((weight for _, weight in ordered), Fraction())
    threshold = total * percentile
    seen = Fraction()
    for value, weight in ordered:
        seen += weight
        if seen >= threshold:
            return value
    raise AssertionError("non-empty normalized distribution required")


def summarize(weights, order):
    rows = []
    expected_cost = Fraction()
    expected_count = Fraction()
    for state in STATES:
        cost, count, decision = row(state, order)
        weight = weights[state_key(state)]
        expected_cost += weight * cost
        expected_count += weight * count
        rows.append({"state": state, "mass": frac(weight), "cost": cost,
                     "evaluations": count, "decision": decision})
    costs = [(item["cost"], Fraction(item["mass"])) for item in rows]
    return {"order": list(order), "expected_cost": frac(expected_cost),
            "expected_evaluations": frac(expected_count),
            "p50_cost": weighted_quantile(costs, Fraction(50, 100)),
            "p95_cost": weighted_quantile(costs, Fraction(95, 100)),
            "p99_cost": weighted_quantile(costs, Fraction(99, 100)),
            "rows": rows}


def state_key(state):
    return "".join("1" if state[name] else "0" for name in NAMES)


def main():
    weights = {state_key(s): distribution(s) for s in STATES}
    learned = tuple(sorted(NAMES, key=lambda n: (Fraction(COST[n], 1) / (1 - Q[n]), n)))
    source_key, dest_key = state_key(SOURCE), state_key(DEST)
    source_mass = weights[source_key]
    points = []
    for step in range(11):
        delta = source_mass * Fraction(step, 10)
        shifted = dict(weights)
        shifted[source_key] -= delta
        shifted[dest_key] += delta
        naive = summarize(shifted, NAIVE)
        learned_result = summarize(shifted, learned)
        points.append({"step": step, "delta_mass": frac(delta),
                       "naive": naive, "learned": learned_result,
                       "semantic_agreement": all(
                           a["decision"] == b["decision"] == all(s.values())
                           for s, a, b in zip(STATES, naive["rows"], learned_result["rows"]))})
    baseline = points[0]
    crossover = next((p["step"] for p in points
                      if Fraction(p["learned"]["expected_cost"]) >
                         Fraction(p["naive"]["expected_cost"])), None)
    result = {"allocation": "predicate-order-drift-4258-20260927-01",
              "learned_order": list(learned), "naive_order": list(NAIVE),
              "source_state": SOURCE, "destination_state": DEST,
              "source_mass": frac(source_mass), "grid_points": points,
              "first_learned_more_expensive_step": crossover,
              "crossover_scope": "none_on_frozen_grid" if crossover is None else "first_strictly_more_expensive_grid_point",
              "semantic_all_grid_points": all(p["semantic_agreement"] for p in points),
              "development_costs_at_step_0": {
                  "naive": baseline["naive"]["expected_cost"],
                  "learned": baseline["learned"]["expected_cost"]}}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "raw.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
