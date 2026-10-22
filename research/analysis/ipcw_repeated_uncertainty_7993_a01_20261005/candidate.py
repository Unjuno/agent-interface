#!/usr/bin/env python3
"""Candidate risk estimator. It reads public masks only, never oracle outcomes."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

N = 200
Q = {"A": 0.25, "B": 0.75}
Z95 = 1.959963984540054
N_TOTAL = 400


def estimate(public: dict) -> dict:
    rows = []
    for cohort in public["cohorts"]:
        htsum = variance_total = errors = observed = 0.0
        for stratum in ("A", "B"):
            row = cohort["strata"][stratum]
            rmask, emask = int(row["resolved_mask"], 16), int(row["resolved_error_mask"], 16)
            if emask & ~rmask:
                raise ValueError("resolved errors must be a subset of resolved rows")
            count_r, count_y = rmask.bit_count(), emask.bit_count()
            q = Q[stratum]
            zsum, z2sum = count_y / q, count_y / (q * q)
            sample_var = (z2sum - zsum * zsum / N) / (N - 1)
            htsum += zsum
            variance_total += N * sample_var
            errors += count_y
            observed += count_r
        ht = htsum / N_TOTAL
        se = math.sqrt(max(0.0, variance_total / (N_TOTAL * N_TOTAL)))
        ht_lo, ht_hi = max(0.0, ht - Z95 * se), min(1.0, ht + Z95 * se)
        cc = errors / observed if observed else None
        cc_se = math.sqrt(cc * (1.0 - cc) / observed) if observed else None
        rows.append({
            "cohort": cohort["cohort"],
            "ht": ht, "ht_se": se, "ht_lo": ht_lo, "ht_hi": ht_hi,
            "cc": cc,
            "cc_lo": None if cc is None else max(0.0, cc - Z95 * cc_se),
            "cc_hi": None if cc is None else min(1.0, cc + Z95 * cc_se),
        })
    return {"schema": "unjuno.issue8049.candidate.v1", "records": rows}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, default=Path("/src/public_input.json"))
    p.add_argument("--output", type=Path, default=Path("/out/candidate_output.json"))
    a = p.parse_args()
    result = estimate(json.loads(a.input.read_text()))
    a.output.write_text(json.dumps(result, separators=(",", ":")) + "\n")
    print(json.dumps({"candidate_cohorts": len(result["records"]), "output_bytes": a.output.stat().st_size}))


if __name__ == "__main__":
    main()
