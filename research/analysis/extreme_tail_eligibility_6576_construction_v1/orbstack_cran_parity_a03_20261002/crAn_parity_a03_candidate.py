"""Run the predeclared Python TailID-port arm for the CRAN/R parity audit."""

import hashlib
import json
import sys
from pathlib import Path

from research.analysis.extreme_tail_eligibility_6576_construction_v1.tailid_equivalent import (
    fit_gpd_parameters,
    quantile_type7,
    shape_interval,
    tailid_sensitive_upper,
)


def main() -> int:
    prereg = Path(sys.argv[1]).read_bytes()
    config = json.loads(prereg)
    sample_dir = Path(sys.argv[2])
    rows = []
    for seed in config["seed_list"]:
        sample_path = sample_dir / f"{seed}.txt"
        sample_bytes = sample_path.read_bytes()
        sample = [float(value) for value in sample_bytes.decode().splitlines()]
        result = tailid_sensitive_upper(
            sample,
            config["threshold_probability"],
            config["confidence"],
            config["candidate_fraction_of_tail"],
        )
        threshold = quantile_type7(sample, config["threshold_probability"])
        candidate_count = result["candidate_count"]
        ranked = sorted(range(len(sample)), key=lambda i: sample[i], reverse=True)[:candidate_count]
        base = [value for i, value in enumerate(sample) if i not in set(ranked)]
        scale, shape = fit_gpd_parameters([v - threshold for v in base if v > threshold])
        interval = shape_interval(shape, sum(v > threshold for v in base), config["confidence"])
        states = [{"fit": [scale, shape], "ci": list(interval)}]
        ordered_candidates = list(reversed(ranked))
        sensitive_indices = []
        current_shape = shape
        current_interval = interval
        for position, index in enumerate(ordered_candidates):
            restored = base + [sample[index]]
            excesses = [v - threshold for v in restored if v > threshold]
            refit_scale, refit_shape = fit_gpd_parameters(excesses)
            refit_interval = shape_interval(refit_shape, len(excesses), config["confidence"])
            states.append({"restored_index": index + 1,
                           "fit": [refit_scale, refit_shape],
                           "ci": list(refit_interval)})
            if not sensitive_indices and refit_shape > current_interval[1]:
                sensitive_indices = [i + 1 for i in ordered_candidates[position:]]
                break
            current_shape = refit_shape
            current_interval = refit_interval
        rows.append({
            "case_id": f"seed-{seed}", "seed": seed, "n": len(sample),
            "sample_sha256": hashlib.sha256(sample_bytes).hexdigest(),
            "threshold": threshold,
            "candidate_indices": sorted(i + 1 for i in ranked),
            "candidate_count_formula": config["candidate_fraction_of_tail"]
                * (1 - config["threshold_probability"]) * len(sample),
            "base_fit": [scale, shape],
            "base_ci": list(shape_interval(shape, sum(v > threshold for v in base), config["confidence"])),
            "states": states,
            "sensitive_indices": sorted(sensitive_indices),
        })
    output = {"preregistration_sha256": hashlib.sha256(prereg).hexdigest(), "rows": rows}
    Path(sys.argv[3]).write_text(json.dumps(output, sort_keys=True, separators=(",", ":")) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
