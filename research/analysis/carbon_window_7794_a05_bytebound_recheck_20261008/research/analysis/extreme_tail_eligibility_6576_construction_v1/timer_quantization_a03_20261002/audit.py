"""Independent raw-only auditor for A03; imports no candidate/gate code."""
import hashlib
import json
import math
import sys
from pathlib import Path


def q7(values, p):
    x = sorted(values)
    h = (len(x) - 1) * p
    lo = math.floor(h)
    return x[lo] + (h-lo) * (x[min(lo+1, len(x)-1)]-x[lo])


def expected_row(case):
    x = case["observed"]
    threshold = q7(x, .90)
    n = len(x)//20
    med = [q7(x[i:i+n], .5) for i in range(0, 20*n, n)]
    ratio = max(med)/min(med) if min(med) > 0 else math.inf
    flag = [v > threshold for v in x]
    avg = sum(flag)/len(flag)
    den = sum((int(v)-avg)**2 for v in flag)
    corr = sum((int(flag[i])-avg)*(int(flag[i+1])-avg) for i in range(len(flag)-1))/den if den else 0.0
    tail = [v for v in x if v > threshold]
    unique = len(set(tail))
    baseline = ratio <= 1.5 and abs(corr) <= .1 and len(tail) >= 40
    return {"arm": case["arm"], "quantum": case["quantum"], "seed": case["seed"],
            "threshold": threshold, "block_median_ratio": ratio, "lag1_correlation": corr,
            "tail_count": len(tail), "distinct_tail_values": unique,
            "largest_tie_count": max((tail.count(v) for v in set(tail)), default=0),
            "baseline_eligible": baseline,
            "cutoff_eligible": {str(c): baseline and unique >= c for c in [8, 12, 16, 20, 24]}}


def summarize(rows):
    rates = {}
    for arm in ("continuous", "quantum_025", "quantum_050", "quantum_100"):
        group = [r for r in rows if r["arm"] == arm]
        eligible = [r for r in group if r["baseline_eligible"]]
        cutoffs = {}
        for c in [8, 12, 16, 20, 24]:
            reject = sum(not r["cutoff_eligible"][str(c)] for r in eligible)
            cutoffs[str(c)] = {"support_rule_rejected": reject, "reject_rate": reject/len(eligible) if eligible else None}
        rates[arm] = {"fixtures": len(group), "baseline_eligible": len(eligible), "cutoffs": cutoffs}
    qualifying = []
    for c in [8, 12, 16, 20, 24]:
        a = rates["continuous"]["cutoffs"][str(c)]["reject_rate"]
        b = rates["quantum_025"]["cutoffs"][str(c)]["reject_rate"]
        d = rates["quantum_100"]["cutoffs"][str(c)]["reject_rate"]
        if a is not None and b is not None and d is not None and d >= .90 and a <= .05 and b <= .10:
            qualifying.append(c)
    return rates, qualifying


def same(expected, actual, label, errors):
    for key, value in expected.items():
        got = actual.get(key)
        name = f"{label} {key}"
        if isinstance(value, dict):
            if not isinstance(got, dict):
                errors.append(name + " missing")
            else:
                same(value, got, name, errors)
        elif isinstance(value, float):
            if not isinstance(got, (int, float)) or not math.isclose(value, got, rel_tol=0, abs_tol=1e-12):
                errors.append(name + " mismatch")
        elif got != value:
            errors.append(name + " mismatch")


def main():
    input_path, output_path = map(Path, sys.argv[1:3])
    raw = input_path.read_bytes()
    data, result = json.loads(raw), json.loads(output_path.read_text())
    errors = []
    if result.get("input_sha256") != hashlib.sha256(raw).hexdigest():
        errors.append("input hash mismatch")
    if data.get("schema") != "unjuno.6576.timer-quantization-a03.v1" or len(data.get("cases", [])) != 200:
        errors.append("input schema/cardinality mismatch")
    if len(result.get("results", [])) != 200:
        errors.append("candidate cardinality mismatch")
    rows = []
    for case, actual in zip(data["cases"], result.get("results", [])):
        expected = expected_row(case)
        same(expected, actual, f"{case['arm']} seed {case['seed']}", errors)
        rows.append(expected)
    rates, qualifying = summarize(rows)
    same(rates, result.get("rates", {}), "aggregate rates", errors)
    if result.get("qualifying_cutoffs") != qualifying:
        errors.append("qualifying cutoff list mismatch")
    selected = min(qualifying) if qualifying else None
    if result.get("selected_smallest_cutoff") != selected:
        errors.append("selected cutoff mismatch")
    disposition = "PASS_CUTOFF_SWEEP_SCOPED" if qualifying else "NO_QUALIFYING_CUTOFF"
    if result.get("disposition") != disposition:
        errors.append("disposition mismatch")
    if errors:
        print("AUDIT_INVALID")
        print("\n".join(errors))
        raise SystemExit(2)
    print("AUDIT_VALID")
    print(json.dumps(rates, sort_keys=True, separators=(",", ":")))
    print("QUALIFYING_CUTOFFS=" + json.dumps(qualifying))
    print("DISPOSITION=" + disposition)


if __name__ == "__main__":
    main()
