#!/usr/bin/env python3
"""Independent raw-table claim auditor; does not import candidate.py."""
import json
import math
import sys
from pathlib import Path


def probability_at_most(k, n, p):
    if k < 0: return 0.0
    if k >= n: return 1.0
    term = (1-p)**n
    total = term
    for j in range(k):
        term *= (n-j)*p/((j+1)*(1-p))
        total += term
    return total


def binomial_boundaries(count, n, tail):
    if count == 0: low = 0.0
    else:
        left, right = 0.0, 1.0
        for _ in range(90):
            mid = (left+right)/2
            upper_tail = 1-probability_at_most(count-1, n, mid)
            if upper_tail < 1-tail: left = mid
            else: right = mid
        low = (left+right)/2
    if count == n: high = 1.0
    else:
        left, right = 0.0, 1.0
        for _ in range(90):
            mid = (left+right)/2
            if probability_at_most(count, n, mid) > tail: left = mid
            else: right = mid
        high = (left+right)/2
    return low, high


def exact_paired_test(a, b):
    discord = a+b
    if discord == 0: return 1.0
    tail = sum(math.comb(discord,j) for j in range(min(a,b)+1))/2**discord
    return min(1.0,2*tail)


def order_interval(sample, confidence):
    if not sample: return None
    x = sorted(sample)
    n = len(x)
    rank = 1
    for r in range(1,(n+1)//2+1):
        coverage = 1-2*sum(math.comb(n,j) for j in range(r))/2**n
        if coverage >= confidence: rank = r
        else: break
    achieved = 1-2*sum(math.comb(n,j) for j in range(rank))/2**n
    return [x[rank-1],x[n-rank]], achieved


def review(row, design):
    n, worse, better = row["attempted"], row["loss_discordances"], row["gain_discordances"]
    p = exact_paired_test(worse, better)
    no_difference = p > 1-design["confidence"]
    verdict = {"difference":"NO_DETECTED_DIFFERENCE" if no_difference else "DIFFERENCE_DETECTED","mcnemar_p":p}
    if row["forbidden_effects"]:
        verdict["binary_claim"] = "HARD_GATE_FAIL"
        return verdict
    if row["missing"]:
        verdict["binary_claim"] = "HOLD_MISSING_OUTCOMES"
        return verdict
    if row["task_mix_changed"]:
        verdict["binary_claim"] = "HOLD_TASK_MIXTURE"
        return verdict
    if not row["margin_preregistered"]:
        verdict["binary_claim"] = "HOLD_POSTHOC_MARGIN"
        return verdict
    # Bonferroni over the four one-sided bounds defining the paired risk range.
    tail = (1-design["confidence"])/4
    worse_ci = binomial_boundaries(worse,n,tail)
    better_ci = binomial_boundaries(better,n,tail)
    risk = [better_ci[0]-worse_ci[1],better_ci[1]-worse_ci[0]]
    verdict["correctness_risk_difference_ci"] = risk
    nm, em = design["noninferiority_margin_correctness"], design["equivalence_margin_correctness"]
    noninferior = risk[0] > -nm
    equivalent = risk[0] > -em and risk[1] < em
    latency = row["soft_latency_differences_ms"]
    if noninferior and not equivalent:
        verdict["binary_claim"] = "NONINFERIOR_NOT_EQUIVALENT"
    elif equivalent:
        verdict["binary_claim"] = "EQUIVALENT_ON_DECLARED_SOFT_ENDPOINT"
    elif no_difference:
        verdict["binary_claim"] = "UNRESOLVED_PRECISION"
    else:
        verdict["binary_claim"] = "BENEFIT_WITH_UNRESOLVED_CORRECTNESS"
    if no_difference:
        verdict["naive_difference_only_promotion"] = "FALSE_EQUIVALENCE"
    interval = order_interval(latency,design["confidence"])
    if interval:
        bounds, coverage = interval
        verdict["latency_median_ci_ms"] = bounds
        verdict["latency_interval_coverage"] = coverage
        if bounds[0] > -design["soft_latency_margin_ms"] and bounds[1] < design["soft_latency_margin_ms"]:
            verdict["latency_claim"] = "EQUIVALENT_ON_DECLARED_SOFT_ENDPOINT"
        elif sum(latency)/len(latency) < 0:
            verdict["latency_claim"] = "BENEFIT_NOT_EQUIVALENT"
        else:
            verdict["latency_claim"] = "UNRESOLVED_SOFT_ENDPOINT"
    if verdict["binary_claim"] == "UNRESOLVED_PRECISION" and verdict.get("latency_claim") == "BENEFIT_NOT_EQUIVALENT":
        verdict["overall_claim"] = "BENEFIT_WITH_UNRESOLVED_CORRECTNESS"
    return verdict


def main():
    design = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    result = {r["id"]:review(r,design) for r in design["cases"]}
    print(json.dumps({"schema":"6113.independent-audit.v1","cases":result},sort_keys=True))


if __name__ == "__main__": main()
