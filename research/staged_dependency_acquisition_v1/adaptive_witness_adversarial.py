#!/usr/bin/env python3
"""Adversarially invalidate every retained competitor witness.

Only score cases where the originally selected branch still matches after the
witness flips. This isolates competitor-uniqueness handling from selected-side
failure. Adaptive fallback must remain equivalent to full unique selection.
"""
from itertools import product
import json, random, statistics

KEYS = [f"p{i}" for i in range(5)]
DOMAIN = [0, 1, 2]
SEED = 20260917
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


def main():
    rng = random.Random(SEED)
    scored = skipped_no_plan = skipped_selected_broken = skipped_witness_conflict = 0
    errors = {
        "selected_only": {"stale_accept": 0, "false_reject": 0},
        "frozen_witness": {"stale_accept": 0, "false_reject": 0},
        "adaptive_witness": {"stale_accept": 0, "false_reject": 0},
    }
    adaptive_checks = []
    full_union_counts = []
    fallback_competitors = []

    for _ in range(ATTEMPTS):
        branches = [random_branch(rng) for _ in range(rng.choice([2, 3, 4]))]
        planned = unique_plan(rng, branches)
        if planned is None:
            skipped_no_plan += 1
            continue
        plan, selected = planned
        witnesses = {}
        for index, branch in enumerate(branches):
            if index == selected:
                continue
            mismatches = sorted(key for key, value in branch.items() if plan[key] != value)
            assert mismatches
            witnesses[index] = mismatches[0]

        desired = {}
        conflict = False
        for index in sorted(witnesses):
            key = witnesses[index]
            value = branches[index][key]
            if key in desired and desired[key] != value:
                conflict = True
                break
            desired[key] = value
        if conflict:
            skipped_witness_conflict += 1
            continue

        current = dict(plan)
        current.update(desired)
        if not matches(branches[selected], current):
            skipped_selected_broken += 1
            continue
        assert all(current[key] == branches[index][key]
                   for index, key in witnesses.items())

        vector = [matches(branch, current) for branch in branches]
        ground_truth = sum(vector) == 1 and vector[selected]
        full_union_counts.append(len(set().union(*(set(branch) for branch in branches))))

        selected_result = True
        if selected_result and not ground_truth:
            errors["selected_only"]["stale_accept"] += 1
        elif not selected_result and ground_truth:
            errors["selected_only"]["false_reject"] += 1

        frozen_result = not witnesses
        if frozen_result and not ground_truth:
            errors["frozen_witness"]["stale_accept"] += 1
        elif not frozen_result and ground_truth:
            errors["frozen_witness"]["false_reject"] += 1

        adaptive_result = True
        checked = set(branches[selected])
        fallbacks = 0
        for index, branch in enumerate(branches):
            if index == selected:
                continue
            witness = witnesses[index]
            checked.add(witness)
            if current[witness] != branch[witness]:
                continue
            fallbacks += 1
            competitor_matches = True
            for key, value in branch.items():
                checked.add(key)
                if current[key] != value:
                    competitor_matches = False
                    break
            if competitor_matches:
                adaptive_result = False
                break
        if adaptive_result and not ground_truth:
            errors["adaptive_witness"]["stale_accept"] += 1
        elif not adaptive_result and ground_truth:
            errors["adaptive_witness"]["false_reject"] += 1

        adaptive_checks.append(len(checked))
        fallback_competitors.append(fallbacks)
        scored += 1

    summary = {
        "schema": "adaptive-witness-adversarial-v1",
        "seed": SEED,
        "attempts": ATTEMPTS,
        "scored": scored,
        "skipped_no_unique_plan": skipped_no_plan,
        "skipped_selected_branch_broken": skipped_selected_broken,
        "skipped_conflicting_witness_targets": skipped_witness_conflict,
        "errors": errors,
        "adaptive_distinct_predicates_checked": {
            "mean": statistics.mean(adaptive_checks),
            "median": statistics.median(adaptive_checks),
        },
        "full_union_distinct_predicates": {
            "mean": statistics.mean(full_union_counts),
            "median": statistics.median(full_union_counts),
        },
        "competitors_fully_reevaluated": {
            "mean": statistics.mean(fallback_competitors),
            "median": statistics.median(fallback_competitors),
        },
    }
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
