#!/usr/bin/env python3
"""Candidate: exact conditional percentile bootstrap from public masks only."""
import argparse
import json
import math
from functools import lru_cache
from pathlib import Path

N = 200
TARGETS = (0.025000000001, 0.975000000001)


@lru_cache(maxsize=None)
def binomial_pmf(successes):
    p = successes / N
    if p == 0:
        return (1.0,) + (0.0,) * N
    if p == 1:
        return (0.0,) * N + (1.0,)
    mode = min(N, int((N + 1) * p))
    log_mode = (math.lgamma(N + 1) - math.lgamma(mode + 1) - math.lgamma(N - mode + 1)
                + mode * math.log(p) + (N - mode) * math.log1p(-p))
    pmf = [0.0] * (N + 1)
    pmf[mode] = math.exp(log_mode)
    for k in range(mode, 0, -1):
        pmf[k - 1] = pmf[k] * k / (N - k + 1) * (1.0 - p) / p
    for k in range(mode, N):
        pmf[k + 1] = pmf[k] * (N - k) / (k + 1) * p / (1.0 - p)
    total = math.fsum(pmf)
    return tuple(value / total for value in pmf)


@lru_cache(maxsize=None)
def interval_ticks(errors_a, errors_b):
    pa, pb = binomial_pmf(errors_a), binomial_pmf(errors_b)
    mass = [0.0] * 801
    for a, wa in enumerate(pa):
        if wa == 0.0:
            continue
        offset = 3 * a
        for b, wb in enumerate(pb):
            mass[offset + b] += wa * wb
    endpoints = []
    cumulative = 0.0
    target_index = 0
    for score, probability in enumerate(mass):
        cumulative += probability
        while target_index < len(TARGETS) and cumulative >= TARGETS[target_index]:
            endpoints.append(score)
            target_index += 1
        if target_index == len(TARGETS):
            break
    if len(endpoints) != 2:
        raise ArithmeticError("bootstrap distribution failed to reach both quantiles")
    return max(0, endpoints[0]), min(300, endpoints[1])


def estimate(public):
    if public.get("schema") != "unjuno.issue8049.public.a02.v1":
        raise ValueError("unexpected public schema")
    records = []
    for row in public["cohorts"]:
        counts = {}
        for name in ("A", "B"):
            data = row["strata"][name]
            resolved = int(data["resolved_mask"], 16)
            errors = int(data["resolved_error_mask"], 16)
            if resolved >> N or errors >> N or errors & ~resolved:
                raise ValueError("invalid public masks")
            counts[name] = (resolved.bit_count(), errors.bit_count())
        ka, kb = counts["A"][1], counts["B"][1]
        lo, hi = interval_ticks(ka, kb)
        records.append({
            "cohort": row["cohort"],
            "ht_numerator": 3 * ka + kb,
            "bootstrap_lo_numerator": lo,
            "bootstrap_hi_numerator": hi,
            "cc_errors": ka + kb,
            "cc_resolved": counts["A"][0] + counts["B"][0],
        })
    return {"schema": "unjuno.issue8049.candidate.a02.v1", "records": records}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("/work/public_input.json"))
    parser.add_argument("--output", type=Path, default=Path("/out/candidate_output.json"))
    args = parser.parse_args()
    result = estimate(json.loads(args.input.read_text()))
    args.output.write_text(json.dumps(result, separators=(",", ":")) + "\n")
    print(json.dumps({"candidate_cohorts": len(result["records"]),
                      "output_bytes": args.output.stat().st_size,
                      "bootstrap_state_pairs": interval_ticks.cache_info().currsize}))


if __name__ == "__main__":
    main()
