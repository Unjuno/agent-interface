import hashlib
import json
import math
from pathlib import Path

from power_model import calibrate_effect, simulate_rank_power


ROOT = Path(__file__).resolve().parent


def wilson_interval(successes, trials):
    z = 1.959963984540054
    p = successes / trials
    denominator = 1 + z * z / trials
    center = (p + z * z / (2 * trials)) / denominator
    margin = z * math.sqrt(p * (1 - p) / trials + z * z / (4 * trials * trials)) / denominator
    return [max(0.0, center - margin), min(1.0, center + margin)]


def main():
    protocol_bytes = (ROOT / "protocol.json").read_bytes()
    protocol = json.loads(protocol_bytes)
    result = {
        "allocation": protocol["allocation"],
        "protocol_sha256": hashlib.sha256(protocol_bytes).hexdigest(),
        "candidate_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "power_model_sha256": hashlib.sha256((ROOT / "power_model.py").read_bytes()).hexdigest(),
        "image": "python:3.12-slim local WSLc image sha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4",
        "cells": [],
        "null_control": None,
    }
    simulation = protocol["simulation"]
    for scenario_index, scenario in enumerate(protocol["ordinal_scenarios"]):
        baseline = scenario["baseline_pmf"]
        for effect_index, target_d in enumerate([0.35, 0.50]):
            odds_ratio, alternative, achieved_d = calibrate_effect(baseline, target_d)
            for n in simulation["sample_sizes_per_arm"]:
                seed = simulation["seed_base"] + scenario_index * 1000 + effect_index * 100 + n
                cell = simulate_rank_power(
                    baseline,
                    alternative,
                    n=n,
                    reps=simulation["replicates_per_power_cell"],
                    seed=seed,
                    alpha=protocol["decision"]["alpha_each_two_sided"],
                )
                cell.update({
                    "scenario": scenario["id"],
                    "target_d": target_d,
                    "achieved_d": achieved_d,
                    "odds_ratio": odds_ratio,
                    "baseline_pmf": baseline,
                    "alternative_pmf": alternative,
                    "seed": seed,
                    "wilson95": wilson_interval(cell["rejections"], cell["replicates"]),
                    "recruited_per_arm_15pct": math.ceil(n / 0.85),
                    "grid_gate_at_target": wilson_interval(cell["rejections"], cell["replicates"])[0] >= 0.80,
                })
                result["cells"].append(cell)
    null = simulation["null_control"]
    null_pmf = protocol["ordinal_scenarios"][0]["baseline_pmf"]
    null_result = simulate_rank_power(
        null_pmf, null_pmf, n=null["n_per_arm"], reps=null["replicates"],
        seed=null["seed"], alpha=protocol["decision"]["alpha_each_two_sided"],
    )
    null_result["seed"] = null["seed"]
    null_result["wilson95"] = wilson_interval(null_result["rejections"], null_result["replicates"])
    result["null_control"] = null_result
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
