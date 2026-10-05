#!/usr/bin/env python3
"""Construction-only interval selection pilots; never part of formal seed."""
import json
import math
import random
import statistics
from pathlib import Path

from candidate import interval_ticks

N = 200
M = 30_000
Z95 = 1.959963984540054
SEEDS = (8_049_002, 8_049_010, 8_049_011, 8_049_012)


def t_critical(df):
    z = Z95
    return (z + (z**3 + z) / (4 * df)
            + (5*z**5 + 16*z**3 + 3*z) / (96 * df**2)
            + (3*z**7 + 19*z**5 + 17*z**3 - 15*z) / (384 * df**3))


def run_seed(seed):
    rng = random.Random(seed)
    cover_boot = cover_t = 0
    estimates = []
    for _ in range(M):
        counts = []
        variance_parts = []
        ht_numerator = 0
        for p, q in ((0.40, 0.25), (0.10, 0.75)):
            error_count = 0
            for _unit in range(N):
                outcome = rng.random() < p
                resolved = rng.random() < q
                error_count += int(outcome and resolved)
            counts.append(error_count)
            weighted_sum = error_count / q
            weighted_square_sum = error_count / (q*q)
            sample_variance = (weighted_square_sum - weighted_sum**2 / N) / (N - 1)
            variance_parts.append(N * sample_variance / (400**2))
            ht_numerator += error_count * (3 if q == 0.25 else 1)
        point = ht_numerator / 300.0
        estimates.append(point)
        lo, hi = interval_ticks(*counts)
        cover_boot += lo <= 75 <= hi
        variance = sum(variance_parts)
        se = math.sqrt(max(0.0, variance))
        df_denominator = sum(v*v/(N-1) for v in variance_parts)
        if df_denominator:
            df = variance*variance/df_denominator
            crit = t_critical(df)
            t_lo, t_hi = max(0.0, point-crit*se), min(1.0, point+crit*se)
        else:
            t_lo, t_hi = 0.0, 1.0
        cover_t += t_lo <= 0.25 <= t_hi
    exact_variance = ((0.40/0.25 - 0.40**2) + (0.10/0.75 - 0.10**2)) / 800
    return {
        "seed": seed, "cohorts": M,
        "percentile_bootstrap_coverage": cover_boot/M,
        "welch_satterthwaite_t_coverage": cover_t/M,
        "ht_mean": statistics.fmean(estimates),
        "ht_empirical_sd": statistics.stdev(estimates),
        "exact_ht_sd": math.sqrt(exact_variance),
    }


if __name__ == "__main__":
    result = {"status": "CONSTRUCTION_ONLY_NOT_FORMAL", "results": [run_seed(s) for s in SEEDS]}
    destination = Path(__file__).with_name("PILOT_RESULTS.json")
    destination.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True, indent=2))
