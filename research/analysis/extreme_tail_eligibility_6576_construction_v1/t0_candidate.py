"""One-shot synthetic T0 candidate for Issue #6576; never a safety bound."""

from __future__ import annotations

import hashlib
import json
import math
import random
import sys
from collections import Counter
from pathlib import Path

from research.analysis.extreme_tail_eligibility_6576_construction_v1.gate import decide
from research.analysis.extreme_tail_eligibility_6576_construction_v1.tailid_equivalent import (
    fit_gpd_parameters,
    quantile_type7,
    tailid_sensitive_upper,
)


def _one(rng: random.Random, scale: float) -> float:
    return rng.expovariate(1.0 / scale)


def generate(case: dict, n: int, stream: str, config: dict) -> list[dict]:
    rng = random.Random(case["seed"] + (0 if stream == "train" else 100000))
    rows = []
    for i in range(n):
        mode = "normal"
        scale = 1.0
        if case["kind"] == "mixture" or (case["kind"] == "hidden_mode" and stream == "holdout"):
            if rng.random() < 0.05:
                mode, scale = "cleanup", 8.0
        elif case["kind"] == "drift":
            scale = 1.0 if i < n // 2 else 3.0
        elif case["kind"] == "cluster" and (i % 500) < 20:
            scale = 12.0
        latent = _one(rng, scale)
        censored = False
        observed = latent
        if case["kind"] == "censored" and latent > config["censor_limit"]:
            p = min(0.95, 0.2 + 0.15 * (latent - config["censor_limit"]))
            censored = rng.random() < p
            if censored:
                observed = config["censor_limit"]
        rows.append({"index": i, "mode": mode, "latent": latent, "observed": observed, "censored": censored})
    return rows


def _correlation_binary(values: list[bool]) -> float:
    if len(values) < 3:
        return 0.0
    mean = sum(values) / len(values)
    denominator = sum((int(v) - mean) ** 2 for v in values)
    if denominator == 0:
        return 0.0
    return sum((int(values[i]) - mean) * (int(values[i + 1]) - mean) for i in range(len(values) - 1)) / denominator


def diagnostics(rows: list[dict], case: dict, config: dict) -> dict:
    values = [r["observed"] for r in rows if not r["censored"]]
    threshold = quantile_type7(values, config["threshold_probability"])
    block_size = len(rows) // 20
    medians = []
    for start in range(0, block_size * 20, block_size):
        block = sorted(r["observed"] for r in rows[start:start + block_size] if not r["censored"])
        medians.append(quantile_type7(block, 0.5))
    ratio = max(medians) / min(medians) if min(medians) > 0 else math.inf
    indicators = [not r["censored"] and r["observed"] > threshold for r in rows]
    corr = _correlation_binary(indicators)
    counts = {mode: sum(r["mode"] == mode and not r["censored"] and r["observed"] > threshold for r in rows) for mode in case["declared_modes"]}
    observed_modes = sorted({r["mode"] for r in rows})
    evidence = {
        "endpoint_identity": "synthetic_admission_to_neutral_v1",
        "mode_manifest": case["declared_modes"],
        "observed_modes": observed_modes,
        "tail_events_by_mode": counts,
        "min_tail_events_per_mode": config["minimum_tail_events_per_mode"],
        "temporal_stability": ratio <= config["max_block_median_ratio"],
        "dependence_checked": abs(corr) <= config["max_lag1_tail_indicator_correlation"],
        "censor_count": sum(r["censored"] for r in rows),
        "missing_endpoint_count": 0,
    }
    return {"threshold": threshold, "block_median_ratio": ratio, "lag1_tail_indicator_correlation": corr, "evidence": evidence, "decision": decide(evidence)}


def _gpd_quantile(values: list[float], threshold_probability: float, target: float) -> dict:
    threshold = quantile_type7(values, threshold_probability)
    excesses = [v - threshold for v in values if v > threshold]
    if len(excesses) < 3:
        return {"status": "NOT_ESTIMABLE", "threshold": threshold, "exceedances": len(excesses)}
    scale, shape = fit_gpd_parameters(excesses)
    tail_fraction = len(excesses) / len(values)
    conditional_tail_probability = (1 - target) / tail_fraction
    if conditional_tail_probability <= 0 or conditional_tail_probability >= 1:
        return {"status": "NOT_ESTIMABLE", "threshold": threshold, "exceedances": len(excesses)}
    if abs(shape) < 1e-7:
        estimate = threshold - scale * math.log(conditional_tail_probability)
    else:
        estimate = threshold + scale / shape * (conditional_tail_probability ** (-shape) - 1)
    if not math.isfinite(estimate) or estimate < threshold:
        return {"status": "NOT_ESTIMABLE", "threshold": threshold, "exceedances": len(excesses), "scale": scale, "shape": shape}
    return {"status": "ESTIMATED", "threshold": threshold, "exceedances": len(excesses), "scale": scale, "shape": shape, "p99": estimate}


def _binomial_cdf(k: int, n: int, p: float) -> float:
    if k < 0:
        return 0.0
    if k >= n:
        return 1.0
    if p <= 0:
        return 1.0
    if p >= 1:
        return 0.0
    probability = math.exp(n * math.log1p(-p))
    total = probability
    for x in range(k):
        probability *= (n - x) * p / ((x + 1) * (1 - p))
        total += probability
    return min(1.0, total)


def _clopper_pearson(k: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    lower = 0.0 if k == 0 else _bisect_probability(lambda p: 1 - _binomial_cdf(k - 1, n, p), alpha / 2, increasing=True)
    upper = 1.0 if k == n else _bisect_probability(lambda p: _binomial_cdf(k, n, p), alpha / 2, increasing=False)
    return lower, upper


def _bisect_probability(function, target: float, *, increasing: bool) -> float:
    lo, hi = 0.0, 1.0
    for _ in range(80):
        mid = (lo + hi) / 2
        value = function(mid)
        if (value < target) == increasing:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def _score_prediction(rows: list[dict], fit: dict, nominal: float) -> dict:
    uncensored_count = sum(not r["censored"] for r in rows)
    if any(r["censored"] for r in rows):
        return {"exceedances": None, "n_uncensored": uncensored_count, "cp95": None, "nominal_in_cp95": None, "reason": "NOT_ESTIMABLE_CENSORED_HOLDOUT"}
    if fit.get("status") != "ESTIMATED":
        return {"exceedances": None, "n_uncensored": uncensored_count, "cp95": None, "nominal_in_cp95": None, "reason": fit.get("reason", "NOT_ESTIMABLE_PREDICTION")}
    predicted = fit["p99"]
    eligible_rows = [r for r in rows if not r["censored"]]
    count = sum(r["latent"] > predicted for r in eligible_rows)
    interval = _clopper_pearson(count, len(eligible_rows))
    return {"exceedances": count, "n_uncensored": len(eligible_rows), "cp95": list(interval), "nominal_in_cp95": interval[0] <= nominal <= interval[1]}


def run(source: Path) -> dict:
    raw = source.read_bytes()
    config = json.loads(raw)
    result = {"input_sha256": hashlib.sha256(raw).hexdigest(), "schema": config["schema"], "results": []}
    target = 1 - config["nominal_exceedance_probability"]
    for case in config["cases"]:
        train = generate(case, config["n_train"], "train", config)
        holdout = generate(case, config["n_holdout"], "holdout", config)
        diag = diagnostics(train, case, config)
        values = [row["observed"] for row in train if not row["censored"]]
        naive = _gpd_quantile(values, config["threshold_probability"], target)
        eligible = diag["decision"] == "ELIGIBLE_REFERENCE"
        gated = {
            "status": "ESTIMATED" if eligible else "NOT_ESTIMABLE",
            "reason": None if eligible else diag["decision"],
            "by_mode": {
                mode: _gpd_quantile([r["observed"] for r in train if r["mode"] == mode and not r["censored"]], config["threshold_probability"], target)
                for mode in case["declared_modes"]
            } if eligible else {},
        }
        if eligible and any(fit.get("status") != "ESTIMATED" for fit in gated["by_mode"].values()):
            gated["status"] = "NOT_ESTIMABLE"
            gated["reason"] = "NOT_ESTIMABLE_MODE_SPECIFIC_FIT"
        tailid = tailid_sensitive_upper(values, threshold_probability=config["threshold_probability"], confidence=config["tailid_confidence"], candidate_fraction_of_tail=config["tailid_candidate_fraction"])
        sensitive = tailid["sensitive"]
        sensitive_counts = Counter(sensitive)
        nonsensitive = []
        for value in values:
            if sensitive_counts[value]:
                sensitive_counts[value] -= 1
            else:
                nonsensitive.append(value)
        tailid_fit = _gpd_quantile(nonsensitive, config["threshold_probability"], target) if len(nonsensitive) >= 100 else {"status": "NOT_ESTIMABLE"}
        empirical_p95 = quantile_type7(values, 0.95)
        empirical_max = max(values)
        gated_fit = {
            "status": "ESTIMATED",
            "p99_by_mode": {mode: fit["p99"] for mode, fit in gated["by_mode"].items() if fit.get("status") == "ESTIMATED"},
        } if gated["status"] == "ESTIMATED" and all(fit.get("status") == "ESTIMATED" for fit in gated["by_mode"].values()) else {"status": "NOT_ESTIMABLE"}
        if any(r["censored"] for r in holdout):
            gated_score = {"exceedances": None, "n_uncensored": sum(not r["censored"] for r in holdout), "by_mode": None, "cp95": None, "nominal_in_cp95": None, "reason": "NOT_ESTIMABLE_CENSORED_HOLDOUT"}
        elif gated_fit["status"] == "ESTIMATED":
            gate_counts = {mode: sum(not r["censored"] and r["latent"] > gated_fit["p99_by_mode"][mode] for r in holdout if r["mode"] == mode) for mode in gated_fit["p99_by_mode"]}
            gate_sample_counts = {mode: sum(not r["censored"] and r["mode"] == mode for r in holdout) for mode in gated_fit["p99_by_mode"]}
            total_count = sum(gate_counts.values())
            total_n = sum(gate_sample_counts.values())
            gate_interval = _clopper_pearson(total_count, total_n)
            gated_score = {"exceedances": total_count, "n_uncensored": total_n, "by_mode": {mode: {"exceedances": gate_counts[mode], "n_uncensored": gate_sample_counts[mode], "cp95": list(_clopper_pearson(gate_counts[mode], gate_sample_counts[mode])), "nominal_in_cp95": _clopper_pearson(gate_counts[mode], gate_sample_counts[mode])[0] <= config["nominal_exceedance_probability"] <= _clopper_pearson(gate_counts[mode], gate_sample_counts[mode])[1]} for mode in gate_counts}, "cp95": list(gate_interval), "nominal_in_cp95": gate_interval[0] <= config["nominal_exceedance_probability"] <= gate_interval[1]}
        else:
            gated_score = {"exceedances": None, "n_uncensored": sum(not r["censored"] for r in holdout), "by_mode": None, "cp95": None, "nominal_in_cp95": None, "reason": gated.get("reason", "NOT_ESTIMABLE_PREDICTION")}
        scores = {
            "naive_evt": _score_prediction(holdout, naive, config["nominal_exceedance_probability"]),
            "eligible_gated_evt": gated_score,
            "tailid_adjusted_evt": _score_prediction(holdout, tailid_fit, config["nominal_exceedance_probability"]),
        }
        result["results"].append({
            "case_id": case["case_id"], "seed": case["seed"], "kind": case["kind"],
            "diagnostics": diag, "empirical_p95": empirical_p95, "empirical_max": empirical_max,
            "naive_evt": naive, "eligible_gated_evt": gated,
            "tailid": {"threshold": tailid["threshold"], "candidate_count": tailid["candidate_count"], "sensitive": sensitive, "adjusted_evt": tailid_fit},
            "holdout_scores": scores,
            "raw_train": train, "raw_holdout": holdout,
        })
    return result


def main() -> int:
    source, output = Path(sys.argv[1]), Path(sys.argv[2])
    output.write_text(json.dumps(run(source), sort_keys=True, separators=(",", ":")) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
