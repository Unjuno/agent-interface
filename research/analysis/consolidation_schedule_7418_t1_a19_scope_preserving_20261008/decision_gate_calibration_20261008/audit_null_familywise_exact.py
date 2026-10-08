"""Exact equal-accuracy null union probability by independent PMF enumeration."""
from collections import defaultdict
import hashlib
import itertools
import json
import math
from pathlib import Path

ARMS = 4
SEEDS = 3


def pmf(n, p):
    values = [math.comb(n, k) * p**k * (1 - p) ** (n - k) for k in range(n + 1)]
    total = math.fsum(values)
    return [value / total for value in values]


def one_seed_masks(n, threshold):
    probabilities = pmf(n, 0.5)
    distribution = defaultdict(float)
    for counts in itertools.product(range(n + 1), repeat=ARMS):
        weight = math.prod(probabilities[count] for count in counts)
        mask = 0
        pair_index = 0
        for left in range(ARMS):
            for right in range(left + 1, ARMS):
                difference = counts[left] - counts[right]
                if difference >= threshold:
                    mask |= 1 << pair_index
                elif difference <= -threshold:
                    mask |= 1 << (pair_index + 6)
                pair_index += 1
        distribution[mask] += weight
    return dict(distribution)


def exact_three_seed_union(mask_distribution):
    all_directions = (1 << 12) - 1
    accumulated = {all_directions: 1.0}
    for _ in range(SEEDS):
        next_distribution = defaultdict(float)
        for accumulated_mask, accumulated_probability in accumulated.items():
            for seed_mask, seed_probability in mask_distribution.items():
                next_distribution[accumulated_mask & seed_mask] += accumulated_probability * seed_probability
        accumulated = dict(next_distribution)
    return 1.0 - accumulated.get(0, 0.0)


def main():
    mc_bytes = Path("SIMULATION_RESULT.json").read_bytes()
    mc = json.loads(mc_bytes)
    null = mc["scenarios"][0]
    cases = []
    for name, n, threshold, observed, mc_se in (
        ("iid_answers", 60, 6,
         null["iid_answers"]["sensitivity_decision"]["rate"],
         null["iid_answers"]["sensitivity_decision"]["monte_carlo_standard_error"]),
        ("perfect_prefix_clusters", 6, 1,
         null["perfect_prefix_clusters"]["sensitivity_decision"]["rate"],
         null["perfect_prefix_clusters"]["sensitivity_decision"]["monte_carlo_standard_error"]),
    ):
        masks = one_seed_masks(n, threshold)
        exact_rate = exact_three_seed_union(masks)
        difference_in_mc_se = (observed - exact_rate) / mc_se if mc_se else 0.0
        cases.append({
            "null_structure": name,
            "one_seed_directed_mask_count": len(masks),
            "one_seed_probability_sum": math.fsum(masks.values()),
            "exact_three_seed_six_pair_rate": exact_rate,
            "monte_carlo_six_pair_rate": observed,
            "monte_carlo_standard_error": mc_se,
            "difference_in_monte_carlo_standard_errors": difference_in_mc_se,
            "within_five_monte_carlo_standard_errors": abs(difference_in_mc_se) <= 5,
        })
    if not all(case["within_five_monte_carlo_standard_errors"] for case in cases):
        raise SystemExit("exact null union does not agree with Monte Carlo within 5 SE")
    output = {
        "status": "PASS_EXACT_NULL_UNION_CROSSCHECK",
        "method": "enumerate four independent Binomial arm counts into directed pair masks, then intersect masks across three seeds",
        "simulation_result_sha256": hashlib.sha256(mc_bytes).hexdigest(),
        "cases": cases,
        "scope": "exact equal-accuracy null crosscheck only; does not verify non-null power scenarios or actual model dependence",
    }
    Path("NULL_UNION_EXACT_AUDIT.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps(output, sort_keys=True))


if __name__ == "__main__":
    main()
