"""Single-run candidate summarizing frozen timer-quantization fixtures."""
import hashlib
import json
import math
import sys
from pathlib import Path


def q7(values, p):
    ordered = sorted(values)
    h = (len(ordered) - 1) * p
    lo = math.floor(h)
    return ordered[lo] + (h - lo) * (ordered[min(lo + 1, len(ordered) - 1)] - ordered[lo])


def summarize(arm):
    values = arm["train_observed"]
    threshold = q7(values, 0.90)
    block_size = len(values) // 20
    medians = [q7(values[i:i + block_size], 0.5) for i in range(0, block_size * 20, block_size)]
    ratio = max(medians) / min(medians) if min(medians) > 0 else math.inf
    indicators = [v > threshold for v in values]
    mean = sum(indicators) / len(indicators)
    denom = sum((int(x) - mean) ** 2 for x in indicators)
    corr = (sum((int(indicators[i]) - mean) * (int(indicators[i + 1]) - mean) for i in range(len(indicators) - 1)) / denom) if denom else 0.0
    exceedances = [v for v in values if v > threshold]
    distinct = len(set(exceedances))
    count = len(exceedances)
    decision = "ELIGIBLE_REFERENCE" if ratio <= 1.5 and abs(corr) <= 0.1 and count >= 40 else "NOT_ESTIMABLE_DIAGNOSTIC_GATE"
    latent_misses = sum(x > threshold for x in arm["holdout_latent"])
    observed_misses = sum(x > threshold for x in arm["holdout_observed"])
    return {"arm": arm["arm"], "quantum": arm["quantum"], "threshold": threshold,
            "block_median_ratio": ratio, "lag1_exceedance_correlation": corr,
            "tail_exceedance_count": count, "distinct_tail_values": distinct,
            "largest_tie_count": max((exceedances.count(v) for v in set(exceedances)), default=0),
            "decision": decision, "holdout_latent_above_observed_threshold": latent_misses,
            "holdout_observed_above_observed_threshold": observed_misses}


def main():
    source = Path(sys.argv[1])
    output = Path(sys.argv[2])
    raw = source.read_bytes()
    data = json.loads(raw)
    results = [summarize(arm) for arm in data["arms"]]
    counterexample = any(r["quantum"] > 0 and r["decision"] == "ELIGIBLE_REFERENCE" and r["distinct_tail_values"] <= 12 for r in results)
    payload = {"input_sha256": hashlib.sha256(raw).hexdigest(), "results": results,
               "disposition": "COUNTEREXAMPLE_A01" if counterexample else "NO_COUNTEREXAMPLE_IN_FROZEN_FIXTURE"}
    output.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    main()
