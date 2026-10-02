"""Independent raw-only T0 oracle; imports no candidate, gate, or TailID code."""

from __future__ import annotations

import hashlib
import json
import math
import random
import sys
from pathlib import Path


def _oracle_rows(case: dict, count: int, stream: str, config: dict) -> list[dict]:
    rng = random.Random(case["seed"] + (0 if stream == "train" else 100000))
    expected = []
    for index in range(count):
        mode, scale = "normal", 1.0
        if case["kind"] == "mixture" or (case["kind"] == "hidden_mode" and stream == "holdout"):
            if rng.random() < 0.05:
                mode, scale = "cleanup", 8.0
        elif case["kind"] == "drift":
            scale = 1.0 if index < count // 2 else 3.0
        elif case["kind"] == "cluster" and index % 500 < 20:
            scale = 12.0
        latent = rng.expovariate(1.0 / scale)
        observed, censored = latent, False
        if case["kind"] == "censored" and latent > config["censor_limit"]:
            censor_probability = min(0.95, 0.2 + 0.15 * (latent - config["censor_limit"]))
            censored = rng.random() < censor_probability
            if censored:
                observed = config["censor_limit"]
        expected.append({"index": index, "mode": mode, "latent": latent, "observed": observed, "censored": censored})
    return expected


def _q7(values: list[float], p: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * p
    lo = math.floor(position)
    hi = min(lo + 1, len(ordered) - 1)
    return ordered[lo] + (position - lo) * (ordered[hi] - ordered[lo])


def _oracle_binomial_cdf(k: int, n: int, p: float) -> float:
    if k < 0:
        return 0.0
    if k >= n:
        return 1.0
    if p <= 0:
        return 1.0
    if p >= 1:
        return 0.0
    term = math.exp(n * math.log1p(-p))
    mass = term
    x = 0
    while x < k:
        term *= (n - x) * p / ((x + 1) * (1 - p))
        mass += term
        x += 1
    return min(mass, 1.0)


def _oracle_cp95(k: int, n: int) -> tuple[float, float]:
    if k == 0:
        lower = 0.0
    else:
        lo, hi = 0.0, 1.0
        for _ in range(80):
            mid = (lo + hi) / 2
            if 1 - _oracle_binomial_cdf(k - 1, n, mid) < 0.025:
                lo = mid
            else:
                hi = mid
        lower = (lo + hi) / 2
    if k == n:
        upper = 1.0
    else:
        lo, hi = 0.0, 1.0
        for _ in range(80):
            mid = (lo + hi) / 2
            if _oracle_binomial_cdf(k, n, mid) > 0.025:
                lo = mid
            else:
                hi = mid
        upper = (lo + hi) / 2
    return lower, upper


def _expected_decision(rows: list[dict], case: dict, config: dict) -> str:
    observed_modes = {r["mode"] for r in rows}
    if observed_modes != set(case["declared_modes"]):
        return "NOT_ESTIMABLE_MODE_COVERAGE"
    if any(r["censored"] for r in rows):
        return "NOT_ESTIMABLE_CENSORED_ENDPOINT"
    complete = [r for r in rows if not r["censored"]]
    threshold = _q7([r["observed"] for r in complete], config["threshold_probability"])
    tail_counts = {mode: sum(r["mode"] == mode and r["observed"] > threshold for r in complete) for mode in case["declared_modes"]}
    if any(n < config["minimum_tail_events_per_mode"] for n in tail_counts.values()):
        return "NOT_ESTIMABLE_INSUFFICIENT_TAIL_EVENTS"
    chunk = len(rows) // 20
    medians = [_q7(sorted(r["observed"] for r in rows[i:i + chunk] if not r["censored"]), 0.5) for i in range(0, chunk * 20, chunk)]
    if min(medians) <= 0 or max(medians) / min(medians) > config["max_block_median_ratio"]:
        return "NOT_ESTIMABLE_NONSTATIONARY"
    indicator = [not r["censored"] and r["observed"] > threshold for r in rows]
    mean = sum(indicator) / len(indicator)
    denominator = sum((int(x) - mean) ** 2 for x in indicator)
    corr = 0.0 if denominator == 0 else sum((int(indicator[i]) - mean) * (int(indicator[i + 1]) - mean) for i in range(len(indicator) - 1)) / denominator
    if abs(corr) > config["max_lag1_tail_indicator_correlation"]:
        return "NOT_ESTIMABLE_DEPENDENCE"
    return "ELIGIBLE_REFERENCE"


def audit(config_path: Path, result_path: Path) -> tuple[bool, str]:
    config_raw = config_path.read_bytes()
    config = json.loads(config_raw)
    result = json.loads(result_path.read_text())
    if result.get("input_sha256") != hashlib.sha256(config_raw).hexdigest():
        return False, "FAIL_INPUT_HASH"
    expected_ids = [c["case_id"] for c in config["cases"]]
    rows = result.get("results")
    if not isinstance(rows, list) or [r.get("case_id") for r in rows] != expected_ids:
        return False, "FAIL_CASE_SET_OR_ORDER"
    method_failures = []
    for case, output in zip(config["cases"], rows, strict=True):
        for stream, n in (("train", config["n_train"]), ("holdout", config["n_holdout"])):
            actual = output.get("raw_train" if stream == "train" else "raw_holdout")
            if actual != _oracle_rows(case, n, stream, config):
                return False, f"FAIL_RAW_RECONSTRUCTION:{case['case_id']}:{stream}"
        expected = _expected_decision(output["raw_train"], case, config)
        if output.get("diagnostics", {}).get("decision") != expected:
            return False, f"FAIL_GATE_DECISION:{case['case_id']}:{expected}"
        train = [r["observed"] for r in output["raw_train"] if not r["censored"]]
        if not math.isclose(output.get("empirical_p95", math.nan), _q7(train, 0.95), rel_tol=0, abs_tol=1e-12):
            return False, f"FAIL_P95:{case['case_id']}"
        if output.get("empirical_max") != max(train):
            return False, f"FAIL_MAX:{case['case_id']}"
        gated = output.get("eligible_gated_evt", {})
        if expected != "ELIGIBLE_REFERENCE" and gated.get("status") != "NOT_ESTIMABLE":
            return False, f"FAIL_INVALID_GATE_PUBLISHED:{case['case_id']}"
        if expected == "ELIGIBLE_REFERENCE" and gated.get("status") not in ("ESTIMATED", "NOT_ESTIMABLE"):
            return False, f"FAIL_REFERENCE_NOT_ESTIMATED:{case['case_id']}"
        if expected == "ELIGIBLE_REFERENCE" and gated.get("status") == "NOT_ESTIMABLE" and gated.get("reason") != "NOT_ESTIMABLE_MODE_SPECIFIC_FIT":
            return False, f"FAIL_REFERENCE_FIT_REASON:{case['case_id']}"
        if case["case_id"] in {"time_drift", "clustered_extremes", "informative_right_censoring", "declared_unseen_cleanup_shift"} and expected == "ELIGIBLE_REFERENCE":
            method_failures.append(f"false_eligibility:{case['case_id']}")
        if case["case_id"] == "stationary_light_tail" and expected != "ELIGIBLE_REFERENCE":
            method_failures.append(f"reference_refused:{expected}")
        train_counts = {}
        for value in [r["observed"] for r in output["raw_train"] if not r["censored"]]:
            train_counts[value] = train_counts.get(value, 0) + 1
        tailid = output.get("tailid", {})
        expected_threshold = _q7(train, config["threshold_probability"])
        expected_candidates = round(config["tailid_candidate_fraction"] * (1 - config["threshold_probability"]) * len(train))
        if not math.isclose(tailid.get("threshold", math.nan), expected_threshold, rel_tol=0, abs_tol=1e-12) or tailid.get("candidate_count") != expected_candidates:
            return False, f"FAIL_TAILID_THRESHOLD_OR_COUNT:{case['case_id']}"
        sensitive = tailid.get("sensitive")
        if not isinstance(sensitive, list) or len(sensitive) > expected_candidates:
            return False, f"FAIL_TAILID_SENSITIVE_SET:{case['case_id']}"
        for value in sensitive:
            if train_counts.get(value, 0) < sensitive.count(value):
                return False, f"FAIL_TAILID_NONMEMBER:{case['case_id']}"
        for estimator, key in (("naive_evt", "naive_evt"), ("eligible_gated_evt", "eligible_gated_evt"), ("tailid_adjusted_evt", "tailid_adjusted_evt")):
            holdout = output["raw_holdout"]
            uncensored = [r for r in holdout if not r["censored"]]
            score = output.get("holdout_scores", {}).get(key, {})
            if len(uncensored) != len(holdout):
                if score.get("exceedances") is not None or score.get("n_uncensored") != len(uncensored) or score.get("cp95") is not None or score.get("nominal_in_cp95") is not None or score.get("reason") != "NOT_ESTIMABLE_CENSORED_HOLDOUT":
                    return False, f"FAIL_CENSORED_HOLDOUT_SCORED:{case['case_id']}:{key}"
                continue
            if estimator == "eligible_gated_evt" and gated.get("status") == "ESTIMATED":
                by_mode = gated.get("by_mode", {})
                if set(by_mode) != set(case["declared_modes"]) or any(f.get("status") != "ESTIMATED" for f in by_mode.values()):
                    return False, f"FAIL_GATED_MODE_FITS:{case['case_id']}"
                mode_counts = {mode: sum(not r["censored"] and r["mode"] == mode and r["latent"] > fit["p99"] for r in holdout) for mode, fit in by_mode.items()}
                mode_sizes = {mode: sum(not r["censored"] and r["mode"] == mode for r in holdout) for mode in by_mode}
                count, n_score = sum(mode_counts.values()), sum(mode_sizes.values())
                if score.get("exceedances") != count or score.get("n_uncensored") != n_score:
                    return False, f"FAIL_HELDOUT_COUNT:{case['case_id']}:{key}"
                mode_scores = score.get("by_mode", {})
                for mode in by_mode:
                    interval_mode = _oracle_cp95(mode_counts[mode], mode_sizes[mode])
                    report_mode = mode_scores.get(mode, {})
                    if report_mode.get("exceedances") != mode_counts[mode] or report_mode.get("n_uncensored") != mode_sizes[mode] or not isinstance(report_mode.get("cp95"), list) or any(not math.isclose(a, b, rel_tol=0, abs_tol=1e-10) for a, b in zip(report_mode["cp95"], interval_mode, strict=True)):
                        return False, f"FAIL_MODE_CP95:{case['case_id']}:{mode}"
                    nominal_covered_mode = interval_mode[0] <= config["nominal_exceedance_probability"] <= interval_mode[1]
                    if report_mode.get("nominal_in_cp95") is not nominal_covered_mode:
                        return False, f"FAIL_MODE_COVERAGE_FLAG:{case['case_id']}:{mode}"
                    if not nominal_covered_mode:
                        method_failures.append(f"gated_mode_coverage:{case['case_id']}:{mode}")
                interval = _oracle_cp95(count, n_score)
                predicted_exists = True
            else:
                fit = output.get("naive_evt", {}) if estimator == "naive_evt" else output.get("tailid", {}).get("adjusted_evt", {})
                predicted = fit.get("p99") if fit.get("status") == "ESTIMATED" else None
                count = sum(r["latent"] > predicted for r in uncensored) if predicted is not None else None
                n_score = len(uncensored)
                if score.get("exceedances") != count or score.get("n_uncensored") != n_score:
                    return False, f"FAIL_HELDOUT_COUNT:{case['case_id']}:{key}"
                predicted_exists = predicted is not None
                interval = _oracle_cp95(count, n_score) if predicted_exists else None
            if predicted_exists:
                reported = score.get("cp95")
                if not isinstance(reported, list) or len(reported) != 2 or any(not math.isclose(a, b, rel_tol=0, abs_tol=1e-10) for a, b in zip(reported, interval, strict=True)):
                    return False, f"FAIL_CP95:{case['case_id']}:{key}"
                nominal_covered = interval[0] <= config["nominal_exceedance_probability"] <= interval[1]
                if score.get("nominal_in_cp95") is not nominal_covered:
                    return False, f"FAIL_COVERAGE_FLAG:{case['case_id']}:{key}"
            elif score.get("cp95") is not None or score.get("nominal_in_cp95") is not None:
                return False, f"FAIL_UNESTIMATED_HAS_COVERAGE:{case['case_id']}:{key}"
    if method_failures:
        return False, f"FAIL_METHOD {','.join(method_failures)}"
    return True, f"PASS_METHOD_SCOPED PASS_RAW_ONLY cases={len(rows)} train={config['n_train']} holdout={config['n_holdout']}"


def main() -> int:
    ok, message = audit(Path(sys.argv[1]), Path(sys.argv[2]))
    print(message)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
