"""Calibrate the A19 three-seed, six-pair accuracy decision rule."""
import argparse
import bisect
import hashlib
import json
import math
import platform
import random
from pathlib import Path
import sys

ARMS = ("episodic_only", "per_episode", "batch_2", "terminal")
SEEDS = 3
PREFIXES = 6
ITEMS_PER_PREFIX = 10
ITEMS_PER_SEED_ARM = PREFIXES * ITEMS_PER_PREFIX
THRESHOLD_COUNT = math.ceil(0.10 * ITEMS_PER_SEED_ARM)
REPLICATES = 200_000
RNG_SEED = 84_062_026
DESIGN_SHA256 = "57600e5fa8107f2bb832275f9322469a80bdd6c6f7bceeec1e6b431ec9f12353"


def binomial_cdf(n, p):
    probabilities = [(1 - p) ** n]
    for k in range(1, n + 1):
        probabilities.append(probabilities[-1] * (n - k + 1) / k * p / (1 - p))
    total = sum(probabilities)
    cumulative = []
    running = 0.0
    for probability in probabilities:
        running += probability / total
        cumulative.append(running)
    cumulative[-1] = 1.0
    return cumulative


def draw(cdf, uniform):
    return bisect.bisect_left(cdf, uniform)


def qualifies(counts):
    for left in range(len(ARMS)):
        for right in range(left + 1, len(ARMS)):
            differences = [seed[left] - seed[right] for seed in counts]
            if all(value >= THRESHOLD_COUNT for value in differences):
                return True
            if all(value <= -THRESHOLD_COUNT for value in differences):
                return True
    return False


def has_no_material_difference(counts):
    return all(
        abs(seed[left] - seed[right]) < THRESHOLD_COUNT
        for seed in counts
        for left in range(len(ARMS))
        for right in range(left + 1, len(ARMS))
    )


def scenario(name, probabilities, rng):
    iid_cdfs = [binomial_cdf(ITEMS_PER_SEED_ARM, p) for p in probabilities]
    cluster_cdfs = [binomial_cdf(PREFIXES, p) for p in probabilities]
    iid_sensitive = cluster_sensitive = iid_no_material = cluster_no_material = 0
    for _ in range(REPLICATES):
        iid_counts, cluster_counts = [], []
        for _seed in range(SEEDS):
            iid_row, cluster_row = [], []
            for arm in range(len(ARMS)):
                u = rng.random()
                iid_row.append(draw(iid_cdfs[arm], u))
                cluster_row.append(ITEMS_PER_PREFIX * draw(cluster_cdfs[arm], u))
            iid_counts.append(iid_row)
            cluster_counts.append(cluster_row)
        iid_gate = qualifies(iid_counts)
        cluster_gate = qualifies(cluster_counts)
        iid_sensitive += iid_gate
        cluster_sensitive += cluster_gate
        iid_no_material += has_no_material_difference(iid_counts)
        cluster_no_material += has_no_material_difference(cluster_counts)
    def estimate(count):
        rate = count / REPLICATES
        return {"rate": rate, "monte_carlo_standard_error": math.sqrt(rate * (1 - rate) / REPLICATES)}

    return {
        "name": name,
        "arm_accuracy_probabilities": dict(zip(ARMS, probabilities)),
        "iid_answers": {
            "sensitivity_decision": estimate(iid_sensitive),
            "no_material_decision": estimate(iid_no_material),
        },
        "perfect_prefix_clusters": {
            "sensitivity_decision": estimate(cluster_sensitive),
            "no_material_decision": estimate(cluster_no_material),
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    source = Path(__file__).read_bytes()
    rng = random.Random(RNG_SEED)
    cases = (
        ("equal_accuracy_null", (0.50, 0.50, 0.50, 0.50)),
        ("episodic_plus_0_10", (0.60, 0.50, 0.50, 0.50)),
        ("episodic_plus_0_20", (0.70, 0.50, 0.50, 0.50)),
    )
    results = [scenario(name, probabilities, rng) for name, probabilities in cases]
    output = {
        "kind": "model_free_decision_gate_calibration",
        "formal_a19_allocation_invoked": False,
        "replicates_per_scenario": REPLICATES,
        "rng": {"implementation": "random.Random / MT19937", "seed": RNG_SEED},
        "python": platform.python_version(),
        "command": [sys.executable, *sys.argv],
        "design_sha256": DESIGN_SHA256,
        "arms": list(ARMS),
        "seeds_per_allocation": SEEDS,
        "prefixes_per_seed_arm": PREFIXES,
        "items_per_prefix": ITEMS_PER_PREFIX,
        "items_per_seed_arm": ITEMS_PER_SEED_ARM,
        "threshold_count": THRESHOLD_COUNT,
        "threshold_fraction": THRESHOLD_COUNT / ITEMS_PER_SEED_ARM,
        "same_pair_same_direction_all_seeds": True,
        "source_sha256": hashlib.sha256(source).hexdigest(),
        "scenarios": results,
        "scope": "idealized Bernoulli null/power calibration only; no Qwen3, cadence, GUI, or task-effect result",
    }
    Path(args.output).write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"scenarios": results, "source_sha256": output["source_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
