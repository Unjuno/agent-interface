"""Candidate sweep of frozen distinct-tail-value support cutoffs."""
import hashlib
import json
import math
import sys
from collections import Counter
from pathlib import Path


def q7(values, p):
    x = sorted(values)
    h = (len(x) - 1) * p
    i = math.floor(h)
    return x[i] + (h - i) * (x[min(i + 1, len(x) - 1)] - x[i])


def diagnose(case):
    x = case["observed"]
    threshold = q7(x, 0.90)
    size = len(x) // 20
    medians = [q7(x[i:i+size], 0.5) for i in range(0, 20*size, size)]
    ratio = max(medians) / min(medians) if min(medians) > 0 else math.inf
    flags = [v > threshold for v in x]
    avg = sum(flags) / len(flags)
    denom = sum((int(v)-avg)**2 for v in flags)
    corr = sum((int(flags[i])-avg)*(int(flags[i+1])-avg) for i in range(len(flags)-1))/denom if denom else 0.0
    tail = [v for v in x if v > threshold]
    baseline = ratio <= 1.5 and abs(corr) <= 0.1 and len(tail) >= 40
    result = {"arm": case["arm"], "quantum": case["quantum"], "seed": case["seed"],
              "threshold": threshold, "block_median_ratio": ratio, "lag1_correlation": corr,
              "tail_count": len(tail), "distinct_tail_values": len(set(tail)),
              "largest_tie_count": max(Counter(tail).values(), default=0), "baseline_eligible": baseline}
    result["cutoff_eligible"] = {str(cutoff): baseline and result["distinct_tail_values"] >= cutoff for cutoff in [8, 12, 16, 20, 24]}
    return result


def summarize(rows):
    rates = {}
    for arm in ("continuous", "quantum_025", "quantum_050", "quantum_100"):
        group = [r for r in rows if r["arm"] == arm]
        eligible = [r for r in group if r["baseline_eligible"]]
        rates[arm] = {"fixtures": len(group), "baseline_eligible": len(eligible), "cutoffs": {}}
        for cutoff in [8, 12, 16, 20, 24]:
            rejected = sum(not r["cutoff_eligible"][str(cutoff)] for r in eligible)
            rates[arm]["cutoffs"][str(cutoff)] = {"support_rule_rejected": rejected,
                                                   "reject_rate": rejected / len(eligible) if eligible else None}
    qualifying = []
    for cutoff in [8, 12, 16, 20, 24]:
        c = rates["continuous"]["cutoffs"][str(cutoff)]["reject_rate"]
        q25 = rates["quantum_025"]["cutoffs"][str(cutoff)]["reject_rate"]
        q100 = rates["quantum_100"]["cutoffs"][str(cutoff)]["reject_rate"]
        if c is not None and q25 is not None and q100 is not None and q100 >= .90 and c <= .05 and q25 <= .10:
            qualifying.append(cutoff)
    return rates, qualifying


def main():
    raw = Path(sys.argv[1]).read_bytes()
    data = json.loads(raw)
    rows = [diagnose(case) for case in data["cases"]]
    rates, qualifying = summarize(rows)
    disposition = "PASS_CUTOFF_SWEEP_SCOPED" if qualifying else "NO_QUALIFYING_CUTOFF"
    payload = {"input_sha256": hashlib.sha256(raw).hexdigest(), "results": rows, "rates": rates,
               "qualifying_cutoffs": qualifying, "selected_smallest_cutoff": min(qualifying) if qualifying else None,
               "disposition": disposition}
    Path(sys.argv[2]).write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    main()
