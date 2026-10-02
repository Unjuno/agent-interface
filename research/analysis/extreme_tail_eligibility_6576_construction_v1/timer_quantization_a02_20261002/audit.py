"""Independent raw-only recomputation of the A02 support-rule experiment."""
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


def main():
    input_path, output_path = map(Path, sys.argv[1:3])
    raw = input_path.read_bytes()
    source = json.loads(raw)
    result = json.loads(output_path.read_text())
    errors = []
    if result.get("input_sha256") != hashlib.sha256(raw).hexdigest():
        errors.append("input hash mismatch")
    if source.get("schema") != "unjuno.6576.timer-quantization-a02.v1" or len(source.get("cases", [])) != 90:
        errors.append("frozen input schema/cardinality mismatch")
    if len(result.get("results", [])) != 90:
        errors.append("candidate row cardinality mismatch")
    rows = []
    for case, got in zip(source["cases"], result.get("results", [])):
        x = case["observed"]
        threshold = q7(x, 0.90)
        size = len(x) // 20
        medians = [q7(x[i:i+size], 0.5) for i in range(0, 20*size, size)]
        ratio = max(medians) / min(medians) if min(medians) > 0 else math.inf
        indicator = [v > threshold for v in x]
        avg = sum(indicator) / len(indicator)
        denominator = sum((int(v)-avg)**2 for v in indicator)
        corr = sum((int(indicator[i])-avg)*(int(indicator[i+1])-avg) for i in range(len(indicator)-1)) / denominator if denominator else 0.0
        tail = [v for v in x if v > threshold]
        distinct = len(set(tail))
        baseline = ratio <= 1.5 and abs(corr) <= 0.1 and len(tail) >= 40
        adjusted = baseline and distinct >= 20
        expected = {"arm": case["arm"], "quantum": case["quantum"], "seed": case["seed"],
                    "threshold": threshold, "block_median_ratio": ratio, "lag1_correlation": corr,
                    "tail_count": len(tail), "distinct_tail_values": distinct,
                    "baseline_eligible": baseline, "support_rule_eligible": adjusted,
                    "support_rule_decision": "ELIGIBLE_REFERENCE" if adjusted else ("NOT_ESTIMABLE_TAIL_SUPPORT" if baseline else "NOT_ESTIMABLE_BASELINE_GATE")}
        for key, value in expected.items():
            actual = got.get(key)
            if isinstance(value, float):
                if not isinstance(actual, (int, float)) or not math.isclose(value, actual, rel_tol=0, abs_tol=1e-12):
                    errors.append(f"{case['arm']} seed {case['seed']} {key} mismatch")
            elif actual != value:
                errors.append(f"{case['arm']} seed {case['seed']} {key} mismatch")
        rows.append(expected)
    rates = {}
    for arm in ("continuous", "quantum_025", "quantum_100"):
        group = [row for row in rows if row["arm"] == arm]
        eligible = [row for row in group if row["baseline_eligible"]]
        rejected = sum(not row["support_rule_eligible"] for row in eligible)
        rates[arm] = {"fixtures": len(group), "baseline_eligible": len(eligible),
                      "support_rule_rejected": rejected,
                      "support_rule_reject_rate": rejected / len(eligible) if eligible else None}
    if result.get("rates") != rates:
        errors.append("aggregate rates mismatch")
    c, q = rates["continuous"], rates["quantum_100"]
    if not c["baseline_eligible"] or not q["baseline_eligible"]:
        disposition = "INCONCLUSIVE_NO_BASELINE_ELIGIBLE_CASES"
    elif q["support_rule_reject_rate"] >= 0.90 and c["support_rule_reject_rate"] <= 0.05:
        disposition = "PASS_SUPPORT_RULE_SCOPED"
    else:
        disposition = "FAIL_SUPPORT_RULE_CRITERION"
    if result.get("disposition") != disposition:
        errors.append("disposition mismatch")
    if errors:
        print("AUDIT_INVALID")
        print("\n".join(errors))
        raise SystemExit(2)
    print("AUDIT_VALID")
    print(json.dumps(rates, sort_keys=True, separators=(",", ":")))
    print("DISPOSITION=" + disposition)


if __name__ == "__main__":
    main()
