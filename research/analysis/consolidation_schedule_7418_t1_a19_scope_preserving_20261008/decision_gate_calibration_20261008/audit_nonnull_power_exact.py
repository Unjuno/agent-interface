"""Exact non-null power calculation for A19's three-seed six-pair gate."""
from collections import defaultdict
import hashlib
import itertools
import json
import math
from pathlib import Path

ARMS = 4
SEEDS = 3
DESIGN_SHA256 = "6fc07363ce71a4ab8e80f6009cd73aeff7a225451305c5581b6803d2d937b3ca"


def pmf(n, p):
    values = [math.comb(n, k) * p**k * (1 - p) ** (n - k) for k in range(n + 1)]
    total = math.fsum(values)
    return [value / total for value in values]


def one_seed_masks(n, threshold, arm_probabilities):
    arm_pmfs = [pmf(n, probability) for probability in arm_probabilities]
    distribution = defaultdict(float)
    for counts in itertools.product(range(n + 1), repeat=ARMS):
        weight = math.prod(arm_pmfs[arm][count] for arm, count in enumerate(counts))
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


def exact_three_seed_rate(mask_distribution):
    all_directions = (1 << 12) - 1
    accumulated = {all_directions: 1.0}
    for _ in range(SEEDS):
        next_distribution = defaultdict(float)
        for prior_mask, prior_probability in accumulated.items():
            for seed_mask, seed_probability in mask_distribution.items():
                next_distribution[prior_mask & seed_mask] += prior_probability * seed_probability
        accumulated = dict(next_distribution)
    return 1.0 - accumulated.get(0, 0.0)


def main():
    mc_bytes = Path("SIMULATION_RESULT.json").read_bytes()
    mc = json.loads(mc_bytes)
    cases = []
    for scenario_name, elevated in (("episodic_plus_0_10", 0.60), ("episodic_plus_0_20", 0.70)):
        mc_case = next(item for item in mc["scenarios"] if item["name"] == scenario_name)
        probabilities = (elevated, 0.50, 0.50, 0.50)
        structures = []
        for structure, n, threshold, mc_key in (
            ("iid_answers", 60, 6, "iid_answers"),
            ("perfect_prefix_clusters", 6, 1, "perfect_prefix_clusters"),
        ):
            masks = one_seed_masks(n, threshold, probabilities)
            exact_rate = exact_three_seed_rate(masks)
            mc_entry = mc_case[mc_key]["sensitivity_decision"]
            difference_se = (exact_rate - mc_entry["rate"]) / mc_entry["monte_carlo_standard_error"]
            structures.append({
                "dependence_model": structure,
                "exact_sensitivity_decision_rate": exact_rate,
                "monte_carlo_rate": mc_entry["rate"],
                "monte_carlo_standard_error": mc_entry["monte_carlo_standard_error"],
                "difference_in_monte_carlo_standard_errors": difference_se,
                "within_five_mc_se": abs(difference_se) <= 5,
                "one_seed_mask_count": len(masks),
                "one_seed_probability_sum": math.fsum(masks.values()),
            })
        cases.append({"scenario": scenario_name, "arm_probabilities": dict(zip(("episodic_only", "per_episode", "batch_2", "terminal"), probabilities)), "structures": structures})
    passed = all(structure["within_five_mc_se"] for case in cases for structure in case["structures"])
    output = {
        "status": "PASS_EXACT_POWER_CROSSCHECK" if passed else "FAIL_CROSSCHECK",
        "method": "exact Binomial PMFs and directed-contrast-mask intersections across three seeds",
        "design_sha256": DESIGN_SHA256,
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "monte_carlo_input_sha256": hashlib.sha256(mc_bytes).hexdigest(),
        "cases": cases,
        "scope": "exact non-null gate probabilities conditional on independent arm/seed Binomial draws; no model or GUI result",
    }
    Path("NONNULL_POWER_EXACT_AUDIT.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps(output, sort_keys=True))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
