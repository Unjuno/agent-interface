"""Independent raw-only recomputation for predicate-order drift results."""
from fractions import Fraction
from itertools import product
import copy
import json
from pathlib import Path

RAW = Path("/out/raw.json")
OUT = Path("/out/audit.json")
N = ("A", "B", "C", "D")
C = {"A": 1, "B": 2, "C": 4, "D": 8}
Q = {"A": Fraction(1, 10), "B": Fraction(2, 5),
     "C": Fraction(9, 10), "D": Fraction(4, 5)}
O = ("A", "B", "C", "D")
S = [dict(zip(N, b)) for b in product((False, True), repeat=4)]
SRC = {"A": True, "B": True, "C": False, "D": True}
DST = {"A": False, "B": True, "C": True, "D": True}


def key(x):
    return "".join("1" if x[n] else "0" for n in N)


def show(x):
    return f"{x.numerator}/{x.denominator}"


def base_mass(s):
    value = Fraction(1)
    for n in N:
        value *= (1 - Q[n]) if s[n] is False else Q[n]
    return value


def charge(s, sequence):
    total = 0
    steps = 0
    for n in sequence:
        total += C[n]
        steps += 1
        if s[n] is False:
            return total, steps, False
    return total, steps, True


def quantile(bins, p):
    total = sum((w for _, w in bins), Fraction(0))
    limit = total * p
    sofar = Fraction(0)
    for value, weight in sorted(bins):
        sofar += weight
        if sofar >= limit:
            return value
    return None


def expected(rows, sequence):
    weighted = Fraction(0)
    tests = Fraction(0)
    bins = []
    for s in S:
        k = key(s)
        item = rows[k]
        mass = Fraction(item["mass"])
        amount, ntests, answer = charge(s, sequence)
        if item["decision"] is not answer:
            raise ValueError("truth-table result differs from reference AND")
        if type(item["cost"]) is not int or item["cost"] != amount:
            raise ValueError("per-row weighted cost mismatch")
        if type(item["evaluations"]) is not int or item["evaluations"] != ntests:
            raise ValueError("per-row predicate count mismatch")
        weighted += mass * amount
        tests += mass * ntests
        bins.append((amount, mass))
    return {"expected_cost": show(weighted), "expected_evaluations": show(tests),
            "p50_cost": quantile(bins, Fraction(50, 100)),
            "p95_cost": quantile(bins, Fraction(95, 100)),
            "p99_cost": quantile(bins, Fraction(99, 100))}


def check(document):
    if document["allocation"] != "predicate-order-drift-4258-20260927-01":
        raise ValueError("allocation mismatch")
    learned = tuple(sorted(N, key=lambda n: (Fraction(C[n], 1) / (1 - Q[n]), n)))
    if tuple(document["learned_order"]) != learned or tuple(document["naive_order"]) != O:
        raise ValueError("order does not follow freeze")
    masses = {key(s): base_mass(s) for s in S}
    if document["source_state"] != SRC or document["destination_state"] != DST:
        raise ValueError("drift endpoints differ from freeze")
    source_weight = masses[key(SRC)]
    if document["source_mass"] != show(source_weight) or len(document["grid_points"]) != 11:
        raise ValueError("source mass or grid coverage mismatch")
    crossed = None
    for idx, point in enumerate(document["grid_points"]):
        delta = source_weight * Fraction(idx, 10)
        if point["step"] != idx or point["delta_mass"] != show(delta):
            raise ValueError("grid step/delta mismatch")
        changed = dict(masses)
        changed[key(SRC)] -= delta
        changed[key(DST)] += delta
        if sum(changed.values(), Fraction()) != 1 or min(changed.values()) < 0:
            raise ValueError("distribution is not normalized/nonnegative")
        for label, sequence in (("naive", O), ("learned", learned)):
            result = point[label]
            raw_rows = {key(r["state"]): r for r in result["rows"]}
            if set(raw_rows) != {key(s) for s in S} or len(result["rows"]) != 16:
                raise ValueError("truth-state coverage mismatch")
            for state_key, expected_mass in changed.items():
                if raw_rows[state_key]["mass"] != show(expected_mass):
                    raise ValueError("raw state probability mismatch")
            metrics = expected(raw_rows, sequence)
            if any(result[k] != v for k, v in metrics.items()):
                raise ValueError("aggregate metric mismatch")
        if not point["semantic_agreement"]:
            raise ValueError("semantic equivalence flag false")
        naive_cost = Fraction(point["naive"]["expected_cost"])
        learned_cost = Fraction(point["learned"]["expected_cost"])
        if crossed is None and learned_cost > naive_cost:
            crossed = idx
    if document["first_learned_more_expensive_step"] != crossed:
        raise ValueError("crossover classification mismatch")
    expected_scope = "none_on_frozen_grid" if crossed is None else "first_strictly_more_expensive_grid_point"
    if document["crossover_scope"] != expected_scope or document["semantic_all_grid_points"] is not True:
        raise ValueError("final scope flags mismatch")
    return True


def main():
    original = json.loads(RAW.read_text(encoding="utf-8"))
    errors = []
    try:
        check(original)
    except (ValueError, KeyError, TypeError, ZeroDivisionError) as exc:
        errors.append(str(exc))
    corrupt_cost = copy.deepcopy(original)
    corrupt_cost["grid_points"][0]["learned"]["rows"][0]["cost"] += 1
    corrupt_decision = copy.deepcopy(original)
    corrupt_decision["grid_points"][0]["naive"]["rows"][0]["decision"] = not corrupt_decision["grid_points"][0]["naive"]["rows"][0]["decision"]
    controls = {}
    for name, sample in (("cost_mutation", corrupt_cost), ("decision_mutation", corrupt_decision)):
        try:
            check(sample)
            controls[name] = False
        except (ValueError, KeyError, TypeError, ZeroDivisionError):
            controls[name] = True
    result = {"audit": "PASS" if not errors and all(controls.values()) else "FAIL",
              "errors": errors, "independent_reconciliation": not errors,
              "corruption_controls_rejected": controls,
              "scope": "independent exact finite recomputation; not a runtime or latency audit"}
    OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
