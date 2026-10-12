"""Conditional ordered-logit anchor calibration for the frozen fixture."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path


def logistic(x: float) -> float:
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


def probabilities(cutpoints: list[float], location: float) -> list[float]:
    cumulative = [logistic(c - location) for c in cutpoints]
    return [cumulative[0], *(cumulative[i] - cumulative[i - 1] for i in range(1, len(cumulative))), 1.0 - cumulative[-1]]


def cross_entropy(observed: list[float], predicted: list[float]) -> float:
    return -sum(p * math.log(max(q, 1e-300)) for p, q in zip(observed, predicted))


def fit_shift(rows: list[dict], cutpoints: list[float], anchor_levels: list[float], grid: list[float]) -> float:
    best = (float("inf"), float("inf"))
    for shift in grid:
        score = sum(cross_entropy(row["probabilities"], probabilities(cutpoints, level - shift))
                    for row, level in zip(rows, anchor_levels))
        best = min(best, (score, shift))
    return best[1]


def fit_location(row: dict, cutpoints: list[float], shift: float, grid: list[float]) -> float:
    best = (float("inf"), float("inf"))
    for location in grid:
        score = cross_entropy(row["probabilities"], probabilities(cutpoints, location - shift))
        best = min(best, (score, location))
    return best[1]


def max_residual(rows: list[dict], cutpoints: list[float], levels: list[float], shift: float) -> float:
    return max(abs(a - b)
               for row, level in zip(rows, levels)
               for a, b in zip(row["probabilities"], probabilities(cutpoints, level - shift)))


def analyze(case: dict, spec: dict) -> dict:
    cuts = spec["cutpoints"]
    levels = spec["anchor_levels"]
    grid_b = spec["threshold_shift_grid"]
    grid_mu = spec["self_location_grid"]
    fit = {}
    residuals = {}
    estimates = {}
    for group, rows in case["anchors"].items():
        shift = fit_shift(rows, cuts, levels, grid_b)
        fit[group] = shift
        residuals[group] = max_residual(rows, cuts, levels, shift)
        estimates[group] = fit_location(case["self"][group], cuts, shift, grid_mu)
    identified_by_fit = max(residuals.values()) <= spec["max_anchor_residual"]
    return {
        "case_id": case["case_id"],
        "threshold_shift_estimates": fit,
        "self_location_estimates_conditional": estimates,
        "contrast_conditional": estimates["comparison"] - estimates["reference"],
        "max_anchor_residuals": residuals,
        "model_fit_gate": "CONDITIONAL_FIT" if identified_by_fit else "REJECT_MISFIT",
        "assumption_identification": "NOT_TESTED_BY_OBSERVED_RATINGS",
        "calibrated_claim_permitted": False,
    }


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: candidate.py observations.json output.json")
    source, output = Path(sys.argv[1]), Path(sys.argv[2])
    payload = json.loads(source.read_text())
    result = {
        "schema": "8522-vignette-candidate-v1",
        "cases": [analyze(case, payload["spec"]) for case in payload["cases"]],
    }
    output.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps({"case_count": len(result["cases"]), "output": str(output)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
