#!/usr/bin/env python3
"""Adaptive witness fast-path for unique branch-selection revalidation.

At plan time each non-selected competitor must be false. Retain one predicate
condition that witnessed that falsehood. At final admission:
1. revalidate the selected branch completely;
2. check each competitor's retained false witness;
3. if the witness still blocks the competitor, stop checking that competitor;
4. if the witness no longer blocks it, evaluate the competitor fully.

This computes the same selected-unique verdict as full branch matching, but can
read fewer predicate keys when retained witnesses remain discriminating.
"""
from itertools import product
import json, random, statistics

KEYS = [f"p{i}" for i in range(5)]
DOMAIN = [0, 1, 2]
SEED = 20260916
ATTEMPTS = 100_000


def matches(branch, observation):
    return all(observation[key] == value for key, value in branch.items())


def random_branch(rng):
    subset = [key for key in KEYS if rng.random() < 0.5]
    if not subset:
        subset = [rng.choice(KEYS)]
    return {key: rng.choice(DOMAIN) for key in subset}


def unique_plan(rng, branches):
    candidates = []
    for values in product(DOMAIN, repeat=len(KEYS)):
        observation = dict(zip(KEYS, values))
        vector = [matches(branch, observation) for branch in branches]
        if sum(vector) == 1:
            candidates.append((observation, vector.index(True)))
    return rng.choice(candidates) if candidates else None


def classify(result, ground_truth, row):
    if result and not ground_truth:
        row["stale_accept"] += 1
    elif not result and ground_truth:
        row["false_reject"] += 1
    else:
        row["correct"] += 1


def main():
    rng = random.Random(SEED)
    modes = {
        "selected_only": {"correct": 0, "stale_accept": 0, "false_reject": 0, "checks": []},
        "frozen_witness": {"correct": 0, "stale_accept": 0, "false_reject": 0, "checks": []},
        "adaptive_witness": {"correct": 0, "stale_accept": 0, "false_reject": 0, "checks": []},
    }
    full_union_counts = []
    scored = skipped = 0

    for _ in range(ATTEMPTS):
        branches = [random_branch(rng) for _ in range(rng.choice([2, 3, 4]))]
        planned = unique_plan(rng, branches)
        if planned is None:
            skipped += 1
            continue
        plan, selected = planned

        current = {}
        for key in KEYS:
            if rng.random() < 0.8:
                current[key] = plan[key]
            else:
                current[key] = rng.choice([value for value in DOMAIN if value != plan[key]])

        current_vector = [matches(branch, current) for branch in branches]
        ground_truth = sum(current_vector) == 1 and current_vector[selected]
        selected_branch = branches[selected]
        full_union_counts.append(len(set().union(*(set(branch) for branch in branches))))

        witnesses = {}
        for index, branch in enumerate(branches):
            if index == selected:
                continue
            mismatches = [key for key, value in branch.items() if plan[key] != value]
            assert mismatches
            witnesses[index] = sorted(mismatches)[0]

        selected_result = matches(selected_branch, current)
        classify(selected_result, ground_truth, modes["selected_only"])
        modes["selected_only"]["checks"].append(len(selected_branch))

        frozen_result = selected_result
        frozen_checked = set(selected_branch)
        if frozen_result:
            for index, key in witnesses.items():
                frozen_checked.add(key)
                if current[key] == branches[index][key]:
                    frozen_result = False
                    break
        classify(frozen_result, ground_truth, modes["frozen_witness"])
        modes["frozen_witness"]["checks"].append(len(frozen_checked))

        adaptive_result = selected_result
        adaptive_checked = set(selected_branch)
        if adaptive_result:
            for index, branch in enumerate(branches):
                if index == selected:
                    continue
                witness = witnesses[index]
                adaptive_checked.add(witness)
                if current[witness] != branch[witness]:
                    continue
                competitor_matches = True
                for key, value in branch.items():
                    adaptive_checked.add(key)
                    if current[key] != value:
                        competitor_matches = False
                        break
                if competitor_matches:
                    adaptive_result = False
                    break
        classify(adaptive_result, ground_truth, modes["adaptive_witness"])
        modes["adaptive_witness"]["checks"].append(len(adaptive_checked))
        scored += 1

    summary = {
        "schema": "adaptive-competitor-witness-v1",
        "seed": SEED,
        "attempts": ATTEMPTS,
        "scored": scored,
        "skipped_no_unique_plan": skipped,
        "mutation_model": "each predicate stays at plan value with probability 0.8; otherwise changes uniformly to another ternary value",
        "full_union_distinct_predicates": {
            "mean": statistics.mean(full_union_counts),
            "median": statistics.median(full_union_counts),
        },
        "modes": {},
    }
    for name, row in modes.items():
        summary["modes"][name] = {
            "correct": row["correct"],
            "stale_accept": row["stale_accept"],
            "false_reject": row["false_reject"],
            "mean_distinct_predicates_checked": statistics.mean(row["checks"]),
            "median_distinct_predicates_checked": statistics.median(row["checks"]),
        }
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
