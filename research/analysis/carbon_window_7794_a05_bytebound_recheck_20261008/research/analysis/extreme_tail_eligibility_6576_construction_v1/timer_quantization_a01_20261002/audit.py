"""Independent raw-only audit; imports no candidate or project gate code."""
import hashlib
import json
import math
import sys
from pathlib import Path


def q7(values, p):
    x = sorted(values)
    h = (len(x) - 1) * p
    i = math.floor(h)
    return x[i] + (h - i) * (x[min(i + 1, len(x) - 1)] - x[i])


def main():
    source, output = map(Path, sys.argv[1:3])
    raw = source.read_bytes()
    data = json.loads(raw)
    result = json.loads(output.read_text())
    errors = []
    if result.get("input_sha256") != hashlib.sha256(raw).hexdigest():
        errors.append("input hash mismatch")
    if len(data["arms"]) != len(result.get("results", [])):
        errors.append("arm cardinality mismatch")
    expected_disposition = False
    summaries = []
    for arm, got in zip(data["arms"], result.get("results", [])):
        x = arm["train_observed"]
        threshold = q7(x, 0.90)
        n = len(x) // 20
        medians = [q7(x[i:i+n], 0.5) for i in range(0, 20*n, n)]
        ratio = max(medians) / min(medians) if min(medians) > 0 else math.inf
        flags = [v > threshold for v in x]
        avg = sum(flags) / len(flags)
        denom = sum((int(v)-avg)**2 for v in flags)
        corr = (sum((int(flags[i])-avg)*(int(flags[i+1])-avg) for i in range(len(flags)-1))/denom) if denom else 0.0
        tail = [v for v in x if v > threshold]
        distinct = len(set(tail))
        decision = "ELIGIBLE_REFERENCE" if ratio <= 1.5 and abs(corr) <= 0.1 and len(tail) >= 40 else "NOT_ESTIMABLE_DIAGNOSTIC_GATE"
        summary = {"arm": arm["arm"], "quantum": arm["quantum"], "threshold": threshold,
                   "block_median_ratio": ratio, "lag1_exceedance_correlation": corr,
                   "tail_exceedance_count": len(tail), "distinct_tail_values": distinct,
                   "decision": decision}
        for key, val in summary.items():
            actual = got.get(key)
            if isinstance(val, float):
                if not isinstance(actual, (int, float)) or not math.isclose(val, actual, rel_tol=0, abs_tol=1e-12):
                    errors.append(f"{arm['arm']}: {key} mismatch")
            elif actual != val:
                errors.append(f"{arm['arm']}: {key} mismatch")
        expected_disposition |= arm["quantum"] > 0 and decision == "ELIGIBLE_REFERENCE" and distinct <= 12
        summaries.append(summary)
    disposition = "COUNTEREXAMPLE_A01" if expected_disposition else "NO_COUNTEREXAMPLE_IN_FROZEN_FIXTURE"
    if result.get("disposition") != disposition:
        errors.append("disposition mismatch")
    if errors:
        print("AUDIT_INVALID")
        print("\n".join(errors))
        raise SystemExit(2)
    print("AUDIT_VALID")
    for summary in summaries:
        print(json.dumps(summary, sort_keys=True, separators=(",", ":")))
    print("DISPOSITION=" + disposition)


if __name__ == "__main__":
    main()
