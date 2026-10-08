#!/usr/bin/env python3
"""Exact finite claim-ladder candidate; stdlib only, no external I/O."""
import json
import math
import sys
from pathlib import Path


def cdf(k, n, p):
    if k < 0:
        return 0.0
    if k >= n:
        return 1.0
    return sum(math.comb(n, j) * p**j * (1-p)**(n-j) for j in range(k+1))


def cp_interval(k, n, alpha):
    if n <= 0:
        raise ValueError("empty denominator")
    if k == 0:
        lo = 0.0
    else:
        a, b = 0.0, 1.0
        for _ in range(80):
            p = (a+b)/2
            if 1-cdf(k-1, n, p) < 1-alpha:
                a = p
            else:
                b = p
        lo = (a+b)/2
    if k == n:
        hi = 1.0
    else:
        a, b = 0.0, 1.0
        for _ in range(80):
            p = (a+b)/2
            if cdf(k, n, p) > alpha:
                a = p
            else:
                b = p
        hi = (a+b)/2
    return lo, hi


def mcnemar_p(loss, gain):
    d = loss + gain
    if d == 0:
        return 1.0
    tail = cdf(min(loss, gain), d, 0.5)
    return min(1.0, 2*tail)


def median_interval(values, confidence):
    if not values:
        return None
    ordered = sorted(values)
    n = len(ordered)
    r = 1
    while r <= n//2:
        covered = 1 - 2*sum(math.comb(n,j) for j in range(r))/2**n
        if covered < confidence:
            break
        r += 1
    r -= 1
    achieved = 1 - 2*sum(math.comb(n,j) for j in range(r))/2**n
    return [ordered[r-1], ordered[n-r]], achieved


def evaluate(case, public):
    n = case["attempted"]
    loss, gain = case["loss_discordances"], case["gain_discordances"]
    p = mcnemar_p(loss, gain)
    difference = "DIFFERENCE_DETECTED" if p <= 1-public["confidence"] else "NO_DETECTED_DIFFERENCE"
    out = {"difference": difference, "mcnemar_p": p}
    if case["forbidden_effects"]:
        out["binary_claim"] = "HARD_GATE_FAIL"
        return out
    if case["missing"]:
        out["binary_claim"] = "HOLD_MISSING_OUTCOMES"
        return out
    if case["task_mix_changed"]:
        out["binary_claim"] = "HOLD_TASK_MIXTURE"
        return out
    if not case["margin_preregistered"]:
        out["binary_claim"] = "HOLD_POSTHOC_MARGIN"
        return out
    # Four one-sided bounds (lower/upper for each discordance rate); union
    # bound keeps their joint coverage at least the requested confidence.
    alpha = (1-public["confidence"])/4
    loss_ci = cp_interval(loss, n, alpha)
    gain_ci = cp_interval(gain, n, alpha)
    risk_ci = [gain_ci[0]-loss_ci[1], gain_ci[1]-loss_ci[0]]
    out["correctness_risk_difference_ci"] = risk_ci
    ni = risk_ci[0] > -public["noninferiority_margin_correctness"]
    equiv_margin = public["equivalence_margin_correctness"]
    eq = risk_ci[0] > -equiv_margin and risk_ci[1] < equiv_margin
    latencies = case.get("soft_latency_differences_ms", [])
    if ni and not eq:
        out["binary_claim"] = "NONINFERIOR_NOT_EQUIVALENT"
    elif eq:
        out["binary_claim"] = "EQUIVALENT_ON_DECLARED_SOFT_ENDPOINT"
    elif difference == "NO_DETECTED_DIFFERENCE":
        out["binary_claim"] = "UNRESOLVED_PRECISION"
    else:
        out["binary_claim"] = "BENEFIT_WITH_UNRESOLVED_CORRECTNESS"
    if difference == "NO_DETECTED_DIFFERENCE":
        out["naive_difference_only_promotion"] = "FALSE_EQUIVALENCE"
    values = latencies
    interval = median_interval(values, public["confidence"])
    if interval:
        bounds, achieved = interval
        out["latency_median_ci_ms"] = bounds
        out["latency_interval_coverage"] = achieved
        if bounds[0] > -public["soft_latency_margin_ms"] and bounds[1] < public["soft_latency_margin_ms"]:
            out["latency_claim"] = "EQUIVALENT_ON_DECLARED_SOFT_ENDPOINT"
        elif sum(values)/len(values) < 0:
            out["latency_claim"] = "BENEFIT_NOT_EQUIVALENT"
        else:
            out["latency_claim"] = "UNRESOLVED_SOFT_ENDPOINT"
    if out["binary_claim"] == "UNRESOLVED_PRECISION" and out.get("latency_claim") == "BENEFIT_NOT_EQUIVALENT":
        out["overall_claim"] = "BENEFIT_WITH_UNRESOLVED_CORRECTNESS"
    return out


def main():
    public = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    cases = {c["id"]: evaluate(c, public) for c in public["cases"]}
    print(json.dumps({"schema":"6113.candidate.v1","cases":cases}, sort_keys=True))


if __name__ == "__main__":
    main()
