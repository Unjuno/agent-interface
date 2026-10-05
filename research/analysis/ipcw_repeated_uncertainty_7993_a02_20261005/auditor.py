#!/usr/bin/env python3
"""Independent raw-only reconstruction using binomial-coefficient CDFs."""
import argparse
import copy
import json
import math
import statistics
from functools import lru_cache
from pathlib import Path

N = 200
M = 20_000
N_TOTAL = 400
ALPHA_GUARD = 1e-12


@lru_cache(maxsize=None)
def exact_pmf(successes):
    p = successes / N
    if successes == 0:
        return (1.0,) + (0.0,) * N
    if successes == N:
        return (0.0,) * N + (1.0,)
    return tuple(math.comb(N, k) * p ** k * (1 - p) ** (N - k)
                 for k in range(N + 1))


@lru_cache(maxsize=None)
def verified_interval_ticks(errors_a, errors_b):
    a = exact_pmf(errors_a)
    b = exact_pmf(errors_b)
    prefix_b = []
    running = 0.0
    for value in b:
        running = math.fsum((running, value))
        prefix_b.append(running)

    def cdf(score):
        if score < 0:
            return 0.0
        if score >= 800:
            return 1.0
        terms = []
        for count_a, prob_a in enumerate(a):
            max_b = min(N, score - 3 * count_a)
            if max_b >= 0 and prob_a:
                terms.append(prob_a * prefix_b[max_b])
        return math.fsum(terms)

    result = []
    for target in (0.025 + ALPHA_GUARD, 0.975 + ALPHA_GUARD):
        low, high = -1, 800
        while high - low > 1:
            middle = (low + high) // 2
            if cdf(middle) >= target:
                high = middle
            else:
                low = middle
        result.append(high)
    return max(0, result[0]), min(300, result[1])


def reconstruct(public_row, truth_row):
    if public_row.get("cohort") != truth_row.get("cohort"):
        raise ValueError("cohort identity mismatch")
    errors = {}
    resolved_total = 0
    for name in ("A", "B"):
        public = public_row["strata"][name]
        truth = truth_row["strata"][name]
        resolved = int(public["resolved_mask"], 16)
        observed_errors = int(public["resolved_error_mask"], 16)
        outcomes = int(truth["outcome_mask"], 16)
        limit = (1 << N) - 1
        if any(mask & ~limit for mask in (resolved, observed_errors, outcomes)):
            raise ValueError("mask outside declared 200-unit stratum")
        if observed_errors & ~resolved or observed_errors != (outcomes & resolved):
            raise ValueError("resolved labels disagree with oracle truth")
        errors[name] = observed_errors.bit_count()
        resolved_total += resolved.bit_count()
    ka, kb = errors["A"], errors["B"]
    lo, hi = verified_interval_ticks(ka, kb)
    return {
        "cohort": public_row["cohort"],
        "ht_numerator": 3 * ka + kb,
        "bootstrap_lo_numerator": lo,
        "bootstrap_hi_numerator": hi,
        "cc_errors": ka + kb,
        "cc_resolved": resolved_total,
    }


def _audit_once(public, oracle, candidate):
    if public.get("schema") != "unjuno.issue8049.public.a02.v1":
        raise ValueError("public schema mismatch")
    if oracle.get("schema") != "unjuno.issue8049.oracle.a02.v1":
        raise ValueError("oracle schema mismatch")
    if candidate.get("schema") != "unjuno.issue8049.candidate.a02.v1":
        raise ValueError("candidate schema mismatch")
    pcs, ocs, rows = public["cohorts"], oracle["cohorts"], candidate.get("records", [])
    if len(pcs) != M or len(ocs) != M or len(rows) != M:
        raise ValueError("expected exactly 20,000 rows in every stream")
    expected_ids = list(range(M))
    if ([x.get("cohort") for x in pcs] != expected_ids or
            [x.get("cohort") for x in ocs] != expected_ids or
            [x.get("cohort") for x in rows] != expected_ids):
        raise ValueError("duplicate, missing, reordered, or aliased cohort ID")
    ht = []
    coverage = []
    cc = []
    for pub, tru, got in zip(pcs, ocs, rows):
        rebuilt = reconstruct(pub, tru)
        if got != rebuilt:
            raise ValueError(f"raw-only reconstruction mismatch at cohort {pub['cohort']}")
        ht.append(rebuilt["ht_numerator"] / 300.0)
        coverage.append(rebuilt["bootstrap_lo_numerator"] <= 75 <= rebuilt["bootstrap_hi_numerator"])
        if rebuilt["cc_resolved"]:
            cc.append(rebuilt["cc_errors"] / rebuilt["cc_resolved"])

    risk_a, risk_b = 0.40, 0.10
    q_a, q_b = 0.25, 0.75
    exact_variance = ((risk_a / q_a - risk_a**2) +
                      (risk_b / q_b - risk_b**2)) / (2 * N_TOTAL)
    exact_sd = math.sqrt(exact_variance)
    mean_ht = statistics.fmean(ht)
    empirical_sd = statistics.stdev(ht) if len(ht) > 1 else 0.0
    coverage_rate = sum(coverage) / M
    mean_tolerance = 4 * exact_sd / math.sqrt(M)
    gates = {
        "mean_within_four_mcse": abs(mean_ht - 0.25) <= mean_tolerance,
        "sd_within_2_5_percent": abs(empirical_sd / exact_sd - 1) <= 0.025,
        "bootstrap_coverage_within_0_006": abs(coverage_rate - 0.95) <= 0.006,
    }
    return {
        "schema": "unjuno.issue8049.audit.a02.v1",
        "disposition": "PASS_METHOD_SCOPED" if all(gates.values()) else "FAIL_METHOD",
        "cohort_count": M,
        "unit_identities_reconstructed": 2 * N * M,
        "unique_bootstrap_count_pairs": verified_interval_ticks.cache_info().currsize,
        "target_risk": 0.25,
        "ht_mean": mean_ht,
        "ht_mean_tolerance_four_mcse": mean_tolerance,
        "exact_ht_variance": exact_variance,
        "exact_ht_sd": exact_sd,
        "empirical_ht_sd": empirical_sd,
        "bootstrap_interval_coverage": coverage_rate,
        "complete_case_mean": statistics.fmean(cc),
        "complete_case_population_limit": 0.175,
        "complete_case_cohort_count": len(cc),
        "gates": gates,
    }


def audit(public, oracle, candidate):
    report = _audit_once(public, oracle, candidate)
    mutations = []
    probe = min(123, len(candidate["records"]) - 1)
    changes = (
        ("drop_cohort", lambda d: d["records"].pop()),
        ("alter_ht_numerator", lambda d: d["records"][probe].update(ht_numerator=999999)),
        ("invert_interval", lambda d: d["records"][probe].update(
            bootstrap_lo_numerator=300, bootstrap_hi_numerator=0)),
        ("relabel_cohort", lambda d: d["records"][probe].update(cohort=999999)),
    )
    for name, mutate in changes:
        altered = copy.deepcopy(candidate)
        mutate(altered)
        try:
            _audit_once(public, oracle, altered)
            mutations.append({"control": name, "rejected": False})
        except (ValueError, KeyError, TypeError):
            mutations.append({"control": name, "rejected": True})
    report["mutation_controls"] = mutations
    report["all_mutations_rejected"] = all(x["rejected"] for x in mutations)
    if not report["all_mutations_rejected"]:
        report["disposition"] = "FAIL_AUDIT"
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--public", type=Path, default=Path("/work/public_input.json"))
    parser.add_argument("--oracle", type=Path, default=Path("/work/oracle_input.json"))
    parser.add_argument("--candidate", type=Path, default=Path("/work/candidate_output.json"))
    parser.add_argument("--output", type=Path, default=Path("/out/audit.json"))
    args = parser.parse_args()
    report = audit(json.loads(args.public.read_text()), json.loads(args.oracle.read_text()),
                   json.loads(args.candidate.read_text()))
    args.output.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"disposition": report["disposition"], "cohorts": report["cohort_count"],
                      "coverage": report["bootstrap_interval_coverage"],
                      "mutations_rejected": report["all_mutations_rejected"]}))
    if report["disposition"] != "PASS_METHOD_SCOPED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
