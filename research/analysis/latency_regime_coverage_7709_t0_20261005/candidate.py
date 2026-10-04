#!/usr/bin/env python3
"""Frozen synthetic T0 for Issue #7709; emits every paired attempt."""
import hashlib
import json
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
F = json.loads((ROOT / "FREEZE.json").read_text())
RAW = ROOT / "raw_trials.jsonl"
OUT = ROOT / "RESULT.json"
SCENARIOS = {"stationary": 50.0, "abrupt": 50.0, "gradual": 40.0}


def mean(xs):
    return sum(xs) / len(xs)


def variance(xs):
    m = mean(xs)
    return sum((x - m) ** 2 for x in xs) / (len(xs) - 1)


def interval(xs, critical):
    m = mean(xs)
    half = critical * math.sqrt(variance(xs) / len(xs))
    return [m - half, m + half]


def regime_mean(name, t):
    if name == "stationary":
        return SCENARIOS[name]
    if name == "abrupt":
        return 50.0 if t < 20 else 75.0
    return 40.0 + 20.0 * t / 39.0


def main():
    if RAW.exists() or OUT.exists():
        raise SystemExit("STOP_OUTPUT_EXISTS")
    if F["candidate_sha256"] != hashlib.sha256(Path(__file__).read_bytes()).hexdigest():
        raise SystemExit("STOP_CANDIDATE_HASH")
    rng = random.Random(F["seed"])
    summaries = {name: [] for name in SCENARIOS}
    with RAW.open("x", encoding="utf-8", newline="\n") as stream:
        for scenario in SCENARIOS:
            for replicate in range(F["replicates"]):
                all_deltas, session_means = [], []
                for session in range(F["sessions"]):
                    shared_run = rng.gauss(0.0, 8.0)
                    treatment_run = rng.gauss(0.0, 6.0)
                    common_ar = diff_ar = 0.0
                    deltas = []
                    for attempt in range(F["attempts"]):
                        common_ar = 0.45 * common_ar + rng.gauss(0.0, 5.0)
                        diff_ar = 0.75 * diff_ar + rng.gauss(0.0, 5.0)
                        base = regime_mean(scenario, attempt) + shared_run + common_ar
                        raw_a = base
                        raw_b = base + treatment_run + diff_ar
                        censored = rng.random() < 0.05
                        a = F["deadline_penalty_ns"] if censored else max(0.0, raw_a)
                        b = F["deadline_penalty_ns"] if censored else max(0.0, raw_b)
                        a, b = round(a, 6), round(b, 6)
                        delta = round(b - a, 6)
                        row = {"scenario": scenario, "replicate": replicate, "session": session,
                               "attempt": attempt, "block": attempt // F["block_width"],
                               "route_a_ns": a, "route_b_ns": b,
                               "paired_delta_ns": delta, "censored": censored,
                               "penalty_ns": F["deadline_penalty_ns"], "truth_delta_ns": 0.0}
                        stream.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
                        all_deltas.append(delta)
                        deltas.append(delta)
                    session_means.append(mean(deltas))
                pooled = interval(all_deltas, 1.96)
                clustered = interval(session_means, 2.364624251)  # two-sided 95%, df=7
                summaries[scenario].append({"pooled": pooled, "clustered": clustered,
                                            "pooled_covers": pooled[0] <= 0 <= pooled[1],
                                            "clustered_covers": clustered[0] <= 0 <= clustered[1],
                                            "pooled_promotes": not (pooled[0] <= 0 <= pooled[1]),
                                            "clustered_promotes": not (clustered[0] <= 0 <= clustered[1])})
    raw_sha = hashlib.sha256(RAW.read_bytes()).hexdigest()
    workloads = {}
    for scenario, rows in summaries.items():
        pooled_cov = mean([r["pooled_covers"] for r in rows])
        cluster_cov = mean([r["clustered_covers"] for r in rows])
        pooled_fp = mean([r["pooled_promotes"] for r in rows])
        cluster_fp = mean([r["clustered_promotes"] for r in rows])
        workloads[scenario] = {"datasets": len(rows), "pooled_coverage": pooled_cov,
                               "session_cluster_coverage": cluster_cov,
                               "pooled_false_promotion": pooled_fp,
                               "session_cluster_false_promotion": cluster_fp,
                               "coverage_gain": cluster_cov - pooled_cov}
    gates = {
        "cluster_coverage_each_regime_ge_0_90": all(x["session_cluster_coverage"] >= 0.90 for x in workloads.values()),
        "cluster_false_promotion_each_regime_le_0_10": all(x["session_cluster_false_promotion"] <= 0.10 for x in workloads.values()),
        "nonstationary_coverage_gain_ge_0_10": all(workloads[x]["coverage_gain"] >= 0.10 for x in ("abrupt", "gradual")),
    }
    result = {"format": "issue7709-t0-result-v1", "classification": "finite synthetic method only",
              "seed": F["seed"], "raw_rows": F["replicates"] * F["sessions"] * F["attempts"] * len(SCENARIOS),
              "raw_sha256": raw_sha, "all_attempts_retained": True, "workloads": workloads,
              "gates": gates, "disposition": "METHOD_PASS_SCOPED" if all(gates.values()) else "FAIL_METHOD"}
    OUT.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({"rows": result["raw_rows"], "workloads": workloads,
                      "gates": gates, "disposition": result["disposition"]}, sort_keys=True))


if __name__ == "__main__":
    main()
