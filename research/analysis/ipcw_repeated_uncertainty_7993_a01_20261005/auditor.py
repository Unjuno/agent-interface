#!/usr/bin/env python3
"""Raw-only independent reconstruction; imports no candidate implementation."""
from __future__ import annotations

import argparse
import copy
import json
import math
import statistics
from pathlib import Path

N = 200
NALL = 400
Q = {"A": 0.25, "B": 0.75}
Z = 1.959963984540054
P = {"A": 0.40, "B": 0.10}
M = 20_000


def reconstruct_one(cohort: dict, truth: dict) -> dict:
    if cohort["cohort"] != truth["cohort"]:
        raise ValueError("cohort identity mismatch")
    ht_sum = v_sum = err_total = resolved_total = 0.0
    for h in ("A", "B"):
        pub, oracle = cohort["strata"][h], truth["strata"][h]
        rmask, emask = (int(pub[k], 16) for k in ("resolved_mask", "resolved_error_mask"))
        ytrue = int(oracle["outcome_mask"], 16)
        limit = (1 << N) - 1
        if any(mask & ~limit for mask in (rmask, emask, ytrue)):
            raise ValueError("bitmask exceeds declared stratum size")
        if emask & ~rmask or ((ymask := (ytrue & rmask)) != emask):
            raise ValueError("public resolved labels disagree with oracle or status")
        q = Q[h]
        nr, ne = rmask.bit_count(), emask.bit_count()
        zsum, z2sum = ne / q, ne / (q * q)
        ht_sum += zsum
        v_sum += N * (z2sum - zsum * zsum / N) / (N - 1)
        err_total += ne
        resolved_total += nr
    ht = ht_sum / NALL
    se = math.sqrt(max(0.0, v_sum / (NALL * NALL)))
    lo, hi = max(0.0, ht - Z * se), min(1.0, ht + Z * se)
    cc = err_total / resolved_total if resolved_total else None
    cc_se = math.sqrt(cc * (1 - cc) / resolved_total) if resolved_total else None
    return {"cohort": cohort["cohort"], "ht": ht, "ht_se": se, "ht_lo": lo, "ht_hi": hi,
            "cc": cc, "cc_lo": None if cc is None else max(0, cc-Z*cc_se),
            "cc_hi": None if cc is None else min(1, cc+Z*cc_se)}


def summarize(public: dict, oracle: dict, candidate: dict) -> dict:
    if public.get("schema") != "unjuno.issue8049.public.v1" or oracle.get("schema") != "unjuno.issue8049.oracle.v1":
        raise ValueError("input schema mismatch")
    if candidate.get("schema") != "unjuno.issue8049.candidate.v1":
        raise ValueError("candidate output schema mismatch")
    pcs, ocs, recs = public["cohorts"], oracle["cohorts"], candidate.get("records", [])
    if len(pcs) != M or len(ocs) != M or len(recs) != M:
        raise ValueError("expected exactly 20,000 public/oracle/output cohorts")
    if [x["cohort"] for x in pcs] != list(range(M)) or [x["cohort"] for x in ocs] != list(range(M)):
        raise ValueError("duplicate, missing, reordered, or aliased cohort IDs")
    rebuilt = []
    for pub, tru, got in zip(pcs, ocs, recs):
        expected = reconstruct_one(pub, tru)
        if got != expected:
            # JSON float decimal roundtrip should preserve exact binary64 values.
            raise ValueError(f"candidate/raw reconstruction mismatch at cohort {pub['cohort']}")
        rebuilt.append(expected)

    hts = [r["ht"] for r in rebuilt]
    ses = [r["ht_se"] for r in rebuilt]
    ccs = [r["cc"] for r in rebuilt if r["cc"] is not None]
    hcover = [r["ht_lo"] <= 0.25 <= r["ht_hi"] for r in rebuilt]
    ccover = [r["cc_lo"] <= 0.25 <= r["cc_hi"] for r in rebuilt if r["cc"] is not None]
    # Each stratum contributes N=200 independent draws; divide the sum of
    # stratum variances by 400^2 after multiplying each by its allocation.
    exact_var = sum(P[h] / Q[h] - P[h] ** 2 for h in ("A", "B")) / (2 * NALL)
    exact_sd = math.sqrt(exact_var)
    mean_ht, sd_ht = statistics.fmean(hts), statistics.stdev(hts)
    mean_se = statistics.fmean(ses)
    cov_ht, cov_cc = sum(hcover) / M, sum(ccover) / len(ccover)
    mean_tol = 4 * exact_sd / math.sqrt(M)
    gates = {
        "mean_within_4_mcse": abs(mean_ht - 0.25) <= mean_tol,
        "sd_within_2_5_percent": abs(sd_ht / exact_sd - 1) <= 0.025,
        "ht_coverage_within_0_006": abs(cov_ht - 0.95) <= 0.006,
        "candidate_oracle_full_reconstruction": True,
    }
    return {
        "schema": "unjuno.issue8049.audit.v1", "disposition": "PASS_METHOD_SCOPED" if all(gates.values()) else "FAIL_METHOD",
        "cohort_count": M, "units_reconstructed": 2 * N * M, "truth_risk": 0.25,
        "exact_ht_variance": exact_var, "exact_ht_sd": exact_sd,
        "ht_mean": mean_ht, "ht_mean_tolerance": mean_tol,
        "ht_empirical_sd": sd_ht, "mean_candidate_se": mean_se,
        "ht_coverage_95_wald": cov_ht, "complete_case_mean": statistics.fmean(ccs),
        "complete_case_population_limit": 0.175, "complete_case_coverage_of_0_25": cov_cc,
        "gates": gates,
    }


def mutation_suite(public: dict, oracle: dict, candidate: dict) -> list[dict]:
    cases = []
    for name, change in (
        ("drop_cohort", lambda c: c["records"].pop()),
        ("alter_ht", lambda c: c["records"][123].update(ht=99.0)),
        ("alter_interval", lambda c: c["records"][123].update(ht_hi=2.0)),
    ):
        altered = copy.deepcopy(candidate)
        change(altered)
        rejected = False
        try:
            summarize(public, oracle, altered)
        except (ValueError, KeyError, TypeError):
            rejected = True
        cases.append({"mutation": name, "rejected": rejected})
    return cases


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--public", type=Path, default=Path("/src/public_input.json"))
    p.add_argument("--oracle", type=Path, default=Path("/src/oracle_input.json"))
    p.add_argument("--candidate", type=Path, default=Path("/out/candidate_output.json"))
    p.add_argument("--output", type=Path, default=Path("/out/audit.json"))
    a = p.parse_args()
    public, oracle, candidate = (json.loads(x.read_text()) for x in (a.public, a.oracle, a.candidate))
    report = summarize(public, oracle, candidate)
    report["mutation_controls"] = mutation_suite(public, oracle, candidate)
    if not all(x["rejected"] for x in report["mutation_controls"]):
        report["disposition"] = "FAIL_AUDIT_MUTATION_ESCAPED"
    a.output.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print(json.dumps(report, sort_keys=True))
    if not all(report["gates"].values()) or not all(x["rejected"] for x in report["mutation_controls"]):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
