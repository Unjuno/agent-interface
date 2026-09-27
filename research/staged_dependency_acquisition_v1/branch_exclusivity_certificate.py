#!/usr/bin/env python3
"""Exact mutual-exclusion certificate for compiled-gui-interface-v1 branches.

A v1 branch condition is a conjunction of scalar equalities represented as a
partial map predicate -> expected value. Two such branches are simultaneously
satisfiable iff their partial maps have no conflicting assignment on a shared
predicate.
"""
from itertools import product, combinations
import json, random


def mutually_exclusive(a, b):
    return any(key in b and b[key] != value for key, value in a.items())


def exhaustive_overlap(a, b, domains):
    keys = sorted(set(a) | set(b))
    for values in product(*(domains[key] for key in keys)):
        env = dict(zip(keys, values))
        if (all(env[k] == v for k, v in a.items()) and
                all(env[k] == v for k, v in b.items())):
            return True
    return False


def generated_check(n=100_000):
    rng = random.Random(20260916)
    keys = [f"p{i}" for i in range(4)]
    domains = {key: [0, 1, 2] for key in keys}
    mismatches = 0
    exclusive = overlap = 0
    for _ in range(n):
        branches = []
        for _ in range(2):
            subset = [key for key in keys if rng.random() < 0.6]
            if not subset:
                subset = [rng.choice(keys)]
            branches.append({key: rng.randrange(3) for key in subset})
        cert = mutually_exclusive(*branches)
        actual_overlap = exhaustive_overlap(*branches, domains)
        mismatches += cert != (not actual_overlap)
        exclusive += cert
        overlap += actual_overlap
    return {"pairs": n, "mismatches": mismatches,
            "certified_exclusive": exclusive, "overlapping": overlap}


def retained_shapes():
    return {
        "chromium_v5": {
            "empty": [{"field_pixels_changed": False, "field_target_present": True}],
            "filled": [{"field_pixels_changed": True, "submit_target_present": True}],
            "submitted": [{"submission_pixels_changed": True}],
        },
        "xterm_v4": {
            "token": [{"surface_present": False}, {"surface_present": True, "stage": "RED"}],
            "confirm": [{"surface_present": False}, {"surface_present": True, "stage": "BLUE"}, {"surface_present": True, "stage": "YELLOW"}],
            "done": [{"surface_present": True, "stage": "GREEN"}, {"surface_present": False}],
        },
        "map01_composition": {
            "retreat_state": [{"surface_present": False}, {"surface_present": True, "phase": "RETREAT"}],
            "strafe_state": [{"surface_present": False}, {"surface_present": True, "phase": "STRAFE"}],
            "done": [{"surface_present": True, "phase": "DONE"}, {"surface_present": False}],
        },
        "continuous_control": {
            "steer": [{"surface_present": False}, {"surface_present": True, "zone": "RIGHT"}, {"surface_present": True, "zone": "LEFT"}, {"surface_present": True, "zone": "GOAL"}],
        },
        "desktop_two_step": {
            "token": [{"surface_present": False}, {"surface_present": True, "stage": "RED"}],
            "confirm_state": [{"surface_present": False}, {"surface_present": True, "stage": "BLUE"}, {"surface_present": True, "stage": "YELLOW"}],
            "done": [{"surface_present": True, "stage": "GREEN"}, {"surface_present": False}],
        },
    }


def retained_check():
    out = {}
    for name, states in retained_shapes().items():
        total = certified = 0
        failures = []
        for state, branches in states.items():
            for i, j in combinations(range(len(branches)), 2):
                total += 1
                ok = mutually_exclusive(branches[i], branches[j])
                certified += ok
                if not ok:
                    failures.append([state, i, j])
        out[name] = {"branch_pairs": total, "certified_exclusive": certified,
                     "uncertified": failures}
    return out


def main():
    print(json.dumps({"generated": generated_check(),
                      "retained_shapes": retained_check()}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
