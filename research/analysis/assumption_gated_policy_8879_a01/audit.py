"""Independent raw-only reconstruction for #8879 A01; does not import candidate."""
from fractions import Fraction
from itertools import combinations, product
import copy
import json
import sys


UNIVERSE = tuple(product((0, 1), repeat=2))
SENSORS = ("left", "right")
FEE = Fraction(1, 100)


def worlds_for(history):
    return tuple(w for w in UNIVERSE if all(w[0 if s == "left" else 1] == bit
                                            for s, bit in history))


def score(history):
    population = worlds_for(history)
    labels = tuple(w[0] ^ w[1] for w in population)
    return Fraction(max(labels.count(0), labels.count(1)), len(population))


def gain(sensor, history):
    prior_rows = worlds_for(history)
    current = score(history)
    slot = 0 if sensor == "left" else 1
    result = Fraction(0)
    for bit in (0, 1):
        subset = tuple(w for w in prior_rows if w[slot] == bit)
        result += Fraction(len(subset), len(prior_rows)) * (
            score(history + ((sensor, bit),)) - current)
    return result


def histories():
    output = [()]
    for n in (1, 2):
        for names in combinations(SENSORS, n):
            for bits in product((0, 1), repeat=n):
                output.append(tuple(zip(names, bits)))
    return output


def reconstruction():
    rows = []
    for h in histories():
        rows.append({"history": [list(x) for x in h], "accuracy": str(score(h)),
                     "marginals": {s: str(gain(s, h)) for s in SENSORS if s not in dict(h)}})
    violations = []
    hs = histories()
    for small in hs:
        for large in hs:
            if len(small) >= len(large) or any(dict(small).get(k) != v for k, v in large):
                continue
            for s in SENSORS:
                if s not in dict(large) and gain(s, small) < gain(s, large):
                    violations.append({
                        "small": [list(x) for x in small],
                        "large": [list(x) for x in large],
                        "action": s,
                        "small_marginal": str(gain(s, small)),
                        "large_marginal": str(gain(s, large)),
                    })
    greedy_values = {s: gain(s, ()) - FEE for s in SENSORS}
    pair_value = score((("left", 0), ("right", 0))) - score(()) - 2 * FEE
    return rows, violations, greedy_values, pair_value


def check(record):
    expected_rows, violations, greedy, pair = reconstruction()
    assert record["allocation"] == "8879-assumption-gate-a01-wsl-native-20261012-01"
    assert record["model"] == "xor_two_bits_v1"
    assert record["target"] == "left XOR right"
    assert record["prior"] == "uniform"
    assert record["cost_per_observation"] == str(FEE)
    assert record["histories"] == expected_rows
    assert record["baseline_accuracy"] == "1/2"
    assert record["adaptive_dr_violations"] == violations
    assert len(violations) > 0
    assert record["greedy"]["immediate_net_marginals"] == {k: str(v) for k, v in greedy.items()}
    assert record["greedy"]["stops"] is True
    assert record["depth2"]["net_gain"] == str(pair)
    assert pair > 0
    assert record["selected_policy"] == "depth2"
    return True


def mutation_results(original):
    tests = []
    mutators = (
        lambda x: x.update(model="xor_two_bits_v999"),
        lambda x: x["histories"].pop(),
        lambda x: x.update(target="left OR right"),
        lambda x: x["greedy"].update(stops=False),
        lambda x: x["depth2"].update(net_gain="0"),
        lambda x: x.update(selected_policy="greedy"),
    )
    for mutate in mutators:
        changed = copy.deepcopy(original)
        mutate(changed)
        try:
            check(changed)
            tests.append(False)
        except (AssertionError, KeyError, ValueError):
            tests.append(True)
    return tests


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: audit.py RESULT.json AUDIT.json")
    with open(sys.argv[1], encoding="utf-8") as stream:
        result = json.load(stream)
    check(result)
    mutations = mutation_results(result)
    summary = {"status": "PASS_METHOD_SCOPED",
               "independent_histories_reconstructed": len(result["histories"]),
               "diminishing_returns_violations": len(result["adaptive_dr_violations"]),
               "mutation_controls_rejected": sum(mutations),
               "mutation_controls_total": len(mutations),
               "all_mutations_rejected": all(mutations)}
    if not all(mutations):
        raise SystemExit("mutation control survived")
    with open(sys.argv[2], "x", encoding="utf-8") as stream:
        json.dump(summary, stream, sort_keys=True, indent=2)
        stream.write("\n")
    print(json.dumps(summary, sort_keys=True))
