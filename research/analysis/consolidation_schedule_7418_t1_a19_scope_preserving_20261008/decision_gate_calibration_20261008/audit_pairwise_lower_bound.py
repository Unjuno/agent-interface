"""Exact single-pair lower bound, independent of the Monte Carlo sampler."""
import hashlib
import json
import math
from pathlib import Path


def binomial_pmf(n, p):
    return [math.comb(n, k) * p**k * (1 - p) ** (n - k) for k in range(n + 1)]


def one_direction_probability(n, threshold_count, p=0.5):
    probabilities = binomial_pmf(n, p)
    return sum(
        probabilities[left] * probabilities[right]
        for left in range(n + 1)
        for right in range(n + 1)
        if left - right >= threshold_count
    )


def main():
    result_path = Path("SIMULATION_RESULT.json")
    result_bytes = result_path.read_bytes()
    result = json.loads(result_bytes)
    null = result["scenarios"][0]
    cases = []
    for name, n, threshold, observed in (
        ("iid_answers", 60, 6, null["iid_answers"]["sensitivity_decision"]["rate"]),
        ("perfect_prefix_clusters", 6, 1, null["perfect_prefix_clusters"]["sensitivity_decision"]["rate"]),
    ):
        directional = one_direction_probability(n, threshold)
        lower_bound = 2 * directional**3
        cases.append({
            "null_structure": name,
            "one_seed_one_direction_probability": directional,
            "exact_single_pair_three_seed_probability": lower_bound,
            "monte_carlo_six_pair_familywise_rate": observed,
            "familywise_rate_exceeds_single_pair_lower_bound": observed >= lower_bound,
        })
    if not all(case["familywise_rate_exceeds_single_pair_lower_bound"] for case in cases):
        raise SystemExit("Monte Carlo familywise rate fell below exact single-pair lower bound")
    output = {
        "status": "PASS_SINGLE_PAIR_LOWER_BOUND_SANITY_CHECK",
        "method": "exact binomial PMF and three-seed same-direction probability; no RNG simulation",
        "simulation_result_sha256": hashlib.sha256(result_bytes).hexdigest(),
        "cases": cases,
        "limit": "checks only that the six-pair Monte Carlo familywise rates exceed an exact single-pair event; does not independently reproduce the full union probability",
    }
    Path("INDEPENDENT_AUDIT.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps(output, sort_keys=True))


if __name__ == "__main__":
    main()
