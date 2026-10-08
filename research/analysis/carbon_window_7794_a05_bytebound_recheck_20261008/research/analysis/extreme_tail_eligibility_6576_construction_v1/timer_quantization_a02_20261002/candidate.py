"""Frozen candidate: current eligibility versus a 20-distinct-tail support rule."""
import hashlib
import json
import math
import sys
from collections import Counter
from pathlib import Path


def q7(x, p):
    values = sorted(x)
    h = (len(values) - 1) * p
    i = math.floor(h)
    return values[i] + (h - i) * (values[min(i + 1, len(values) - 1)] - values[i])


def assess(case):
    x = case["observed"]
    threshold = q7(x, 0.90)
    block = len(x) // 20
    medians = [q7(x[i:i + block], 0.5) for i in range(0, block * 20, block)]
    ratio = max(medians) / min(medians) if min(medians) > 0 else math.inf
    flags = [value > threshold for value in x]
    mean = sum(flags) / len(flags)
    denom = sum((int(value) - mean) ** 2 for value in flags)
    corr = sum((int(flags[i]) - mean) * (int(flags[i + 1]) - mean) for i in range(len(flags) - 1)) / denom if denom else 0.0
    tail = [value for value in x if value > threshold]
    distinct = len(set(tail))
    baseline = ratio <= 1.5 and abs(corr) <= 0.1 and len(tail) >= 40
    adjusted = baseline and distinct >= 20
    counts = Counter(tail)
    return {"arm": case["arm"], "quantum": case["quantum"], "seed": case["seed"],
            "threshold": threshold, "block_median_ratio": ratio, "lag1_correlation": corr,
            "tail_count": len(tail), "distinct_tail_values": distinct,
            "largest_tie_count": max(counts.values(), default=0),
            "baseline_eligible": baseline, "support_rule_eligible": adjusted,
            "support_rule_decision": "ELIGIBLE_REFERENCE" if adjusted else ("NOT_ESTIMABLE_TAIL_SUPPORT" if baseline else "NOT_ESTIMABLE_BASELINE_GATE")}


def main():
    raw = Path(sys.argv[1]).read_bytes()
    output = Path(sys.argv[2])
    data = json.loads(raw)
    results = [assess(case) for case in data["cases"]]
    rates = {}
    for arm in ("continuous", "quantum_025", "quantum_100"):
        group = [row for row in results if row["arm"] == arm]
        eligible = [row for row in group if row["baseline_eligible"]]
        rates[arm] = {"fixtures": len(group), "baseline_eligible": len(eligible),
                      "support_rule_rejected": sum(not row["support_rule_eligible"] for row in eligible),
                      "support_rule_reject_rate": (sum(not row["support_rule_eligible"] for row in eligible) / len(eligible)) if eligible else None}
    c, q = rates["continuous"], rates["quantum_100"]
    if not c["baseline_eligible"] or not q["baseline_eligible"]:
        disposition = "INCONCLUSIVE_NO_BASELINE_ELIGIBLE_CASES"
    elif q["support_rule_reject_rate"] >= 0.90 and c["support_rule_reject_rate"] <= 0.05:
        disposition = "PASS_SUPPORT_RULE_SCOPED"
    else:
        disposition = "FAIL_SUPPORT_RULE_CRITERION"
    payload = {"input_sha256": hashlib.sha256(raw).hexdigest(), "results": results, "rates": rates, "disposition": disposition}
    output.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    main()
