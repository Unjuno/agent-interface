"""Small exact candidate for Issue #8879; standard library only."""
from fractions import Fraction
from itertools import combinations
import json
import sys


WORLDS = ((0, 0), (0, 1), (1, 0), (1, 1))
TARGET = lambda w: w[0] ^ w[1]
OBSERVATIONS = ("left", "right")
COST = Fraction(1, 100)


def compatible(world, history):
    return all(world[0 if key == "left" else 1] == value
               for key, value in history)


def accuracy(history):
    rows = [w for w in WORLDS if compatible(w, history)]
    if not rows:
        raise ValueError("inconsistent history")
    counts = [sum(TARGET(w) == label for w in rows) for label in (0, 1)]
    return Fraction(max(counts), len(rows))


def marginal(observation, history):
    if observation in dict(history):
        raise ValueError("observation already acquired")
    rows = [w for w in WORLDS if compatible(w, history)]
    before = accuracy(history)
    total = Fraction(0)
    index = 0 if observation == "left" else 1
    for value in (0, 1):
        branch = tuple(w for w in rows if w[index] == value)
        probability = Fraction(len(branch), len(rows))
        after = accuracy(history + ((observation, value),))
        total += probability * (after - before)
    return total


def all_histories():
    seen = {()}
    for size in range(1, len(OBSERVATIONS) + 1):
        for names in combinations(OBSERVATIONS, size):
            for values in __import__("itertools").product((0, 1), repeat=size):
                seen.add(tuple(zip(names, values)))
    return sorted(seen, key=lambda h: (len(h), h))


def adaptive_dr_violations():
    histories = all_histories()
    violations = []
    for small in histories:
        for large in histories:
            if len(small) >= len(large) or any(dict(small).get(k) != v for k, v in large):
                continue
            for action in OBSERVATIONS:
                if action not in dict(large):
                    a, b = marginal(action, small), marginal(action, large)
                    if a < b:
                        violations.append({"small": small, "large": large,
                                           "action": action, "small_marginal": a,
                                           "large_marginal": b})
    return violations


def run():
    violations = adaptive_dr_violations()
    base = accuracy(())
    immediate = {name: marginal(name, ()) - COST for name in OBSERVATIONS}
    greedy_stops = max(immediate.values()) <= 0
    pair_accuracy = accuracy((("left", 0), ("right", 0)))
    pair_gain = pair_accuracy - base - 2 * COST
    selector = "depth2" if violations else "greedy"
    return {
        "allocation": "8879-assumption-gate-a01-wsl-native-20261012-01",
        "model": "xor_two_bits_v1",
        "worlds": [list(w) for w in WORLDS],
        "target": "left XOR right",
        "prior": "uniform",
        "cost_per_observation": str(COST),
        "baseline_accuracy": str(base),
        "histories": [
            {"history": list(h), "accuracy": str(accuracy(h)),
             "marginals": {a: str(marginal(a, h)) for a in OBSERVATIONS if a not in dict(h)}}
            for h in all_histories()
        ],
        "adaptive_dr_violations": [
            {**{k: [list(x) for x in v] if isinstance(v, tuple) else v
                for k, v in row.items()},
             "small_marginal": str(row["small_marginal"]),
             "large_marginal": str(row["large_marginal"])}
            for row in violations
        ],
        "greedy": {"immediate_net_marginals": {k: str(v) for k, v in immediate.items()},
                   "stops": greedy_stops, "net_gain": "0" if greedy_stops else "UNMODELED"},
        "depth2": {"accuracy": str(pair_accuracy), "net_gain": str(pair_gain)},
        "selected_policy": selector,
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: candidate.py OUTPUT.json")
    with open(sys.argv[1], "x", encoding="utf-8") as stream:
        json.dump(run(), stream, sort_keys=True, indent=2)
        stream.write("\n")
    print("candidate_written")
