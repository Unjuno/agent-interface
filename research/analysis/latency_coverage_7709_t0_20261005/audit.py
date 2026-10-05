#!/usr/bin/env python3
"""Independent raw-only reconstruction; does not import candidate.py."""
import json
import math
import statistics
import sys
from collections import defaultdict

Z = 1.959963984540054
TOL = 1e-7


def tcrit(df):
    if df == 7:
        return 2.364624251
    if df == 15:
        return 2.131449546
    z = Z
    return z + (z**3 + z) / (4.0 * df) + (5*z**5 + 16*z**3 + 3*z) / (96.0 * df**2)


def ci(xs):
    n = len(xs)
    mu = sum(xs) / n
    variance = sum((x - mu) * (x - mu) for x in xs) / (n - 1)
    radius = tcrit(n - 1) * math.sqrt(variance / n)
    return [mu, mu - radius, mu + radius]


def find_edges(sessions, cfg):
    count = len(sessions[0])
    signal = [sum((s[j][0] + s[j][1]) / 2.0 for s in sessions) / len(sessions) for j in range(count)]
    prefix = [0.0]
    for value in signal:
        prefix.append(prefix[-1] + value)
    edges = []

    def avg(lo, hi):
        return (prefix[hi] - prefix[lo]) / (hi - lo)

    def search(lo, hi):
        if len(edges) + 1 >= cfg["segment_max_count"] or hi - lo < 2 * cfg["segment_min_windows"]:
            return
        choice, score = -1, cfg["segment_split_threshold_ms"]
        for k in range(lo + cfg["segment_min_windows"], hi - cfg["segment_min_windows"] + 1):
            diff = abs(avg(k, hi) - avg(lo, k))
            if diff > score:
                choice, score = k, diff
        if choice >= 0:
            edges.append(choice)
            search(lo, choice)
            search(choice, hi)

    search(0, count)
    return sorted(edges)


def session_integrals(sessions, boundaries):
    points = [0] + boundaries + [len(sessions[0])]
    totals = []
    for s in sessions:
        total = 0.0
        for start, end in zip(points, points[1:]):
            segment = sum(s[t][1] - s[t][0] for t in range(start, end)) / (end - start)
            total += segment * (end - start)
        totals.append(total / len(s[0:]))
    return totals


def expected_record(raw, cfg):
    sessions = raw["sessions"]
    flat = [point[1] - point[0] for session in sessions for point in session]
    boundaries = find_edges(sessions, cfg)
    aware_values = session_integrals(sessions, boundaries)
    no_boundary_values = session_integrals(sessions, [])
    nwin = len(sessions[0])
    extras = [k for k in range(cfg["segment_min_windows"], nwin, cfg["segment_min_windows"])
              if min(k, nwin - k) >= cfg["segment_min_windows"]]
    extra_values = session_integrals(sessions, extras)
    censored = sum(point[2] for session in sessions for point in session)
    bounds = [0] + boundaries + [len(sessions[0])]
    strata = []
    for start, end in zip(bounds, bounds[1:]):
        values = [session[t][1] - session[t][0] for session in sessions for t in range(start, end)]
        strata.append({
            "start": start, "end": end, "paired_windows": len(values),
            "censored_windows": sum(session[t][2] for session in sessions for t in range(start, end)),
            "mean_delta_ms": sum(values) / len(values),
        })
    return {
        "case": raw["case"], "n": raw["n"], "rep": raw["rep"], "truth_ms": raw["truth_ms"],
        "window_rows": len(flat), "censored_rows": censored, "edges": boundaries, "segments": strata,
        "base": ci(flat), "aware": ci(aware_values),
        "no_boundary_max_error": max(abs(a-b) for a, b in zip(ci(aware_values), ci(no_boundary_values))),
        "extra_boundary_max_error": max(abs(a-b) for a, b in zip(ci(aware_values), ci(extra_values))),
    }


def same(a, b):
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(a - b) <= TOL
    return a == b


def read_map(path, key_fn):
    out = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            item = json.loads(line)
            key = key_fn(item)
            if key in out:
                raise ValueError("duplicate key " + repr(key))
            out[key] = item
    return out


def audit(input_path, results_path, config):
    expected_cases = {(case["name"], n) for case in config["scenarios"] for n in config["session_counts"]}
    results = read_map(results_path, lambda r: (r["case"], r["n"], r["rep"]))
    cells = defaultdict(list)
    input_count = 0
    paired_windows = 0
    censored_windows = 0
    mutation_examples = {}
    for raw_line in open(input_path, encoding="utf-8"):
        raw = json.loads(raw_line)
        input_count += 1
        key = (raw["case"], raw["n"], raw["rep"])
        if key not in results:
            raise ValueError("candidate result missing " + repr(key))
        scenario = next(x for x in config["scenarios"] if x["name"] == raw["case"])
        if raw["truth_ms"] != round(scenario["beta_ms"] * (1-config["censor_probability"]), 9):
            raise ValueError("wrong truth " + repr(key))
        if len(raw["sessions"]) != raw["n"]:
            raise ValueError("session count mismatch " + repr(key))
        for session in raw["sessions"]:
            if len(session) != config["windows_per_session"]:
                raise ValueError("window count mismatch " + repr(key))
            for a, b, censored in session:
                if a <= 0 or b <= 0 or censored not in (0, 1):
                    raise ValueError("invalid raw row " + repr(key))
                if censored and (a != config["censor_cap_ms"] or b != config["censor_cap_ms"]):
                    raise ValueError("censor cap not retained " + repr(key))
                paired_windows += 1
                censored_windows += censored
        exp = expected_record(raw, config)
        got = results[key]
        if not same(got, exp):
            raise ValueError("raw-only reconstruction mismatch " + repr(key))
        cells[(raw["case"], raw["n"])].append(exp)
        if exp["censored_rows"] and not mutation_examples:
            mutation_examples["base"] = exp

    if len(results) != input_count:
        raise ValueError("candidate has extra result rows")
    expected_reps = config["replicates"] * len(expected_cases)
    expected_windows = expected_reps * sum(config["session_counts"]) // len(config["session_counts"]) * config["windows_per_session"]
    # The two n-grid cells have distinct sample sizes; sum exact rows from the grid.
    expected_windows = config["replicates"] * len(config["scenarios"]) * sum(config["session_counts"]) * config["windows_per_session"]
    if input_count != expected_reps or paired_windows != expected_windows:
        raise ValueError("frozen input denominator mismatch")

    # Mutation controls exercise the auditor's full-record comparison, not a rerun.
    control = mutation_examples["base"]
    bad_count = dict(control)
    bad_count["window_rows"] -= 1
    bad_censor = dict(control)
    bad_censor["censored_rows"] = 0
    bad_promotion = dict(control)
    bad_promotion["aware"] = [-1.0, -2.0, -0.5]
    controls = {
        "drop_window": not same(bad_count, control),
        "drop_censored_rows": not same(bad_censor, control),
        "planted_false_promotion": not same(bad_promotion, control),
    }

    summary = []
    aware_coverage_ok = True
    false_promotion_ok = True
    boundary_ok = True
    stress_improvements = 0
    for case_name, n in sorted(expected_cases):
        records = cells[(case_name, n)]
        truth = records[0]["truth_ms"]
        base_cov = sum(r["base"][1] <= truth <= r["base"][2] for r in records) / len(records)
        aware_cov = sum(r["aware"][1] <= truth <= r["aware"][2] for r in records) / len(records)
        base_fp = sum(r["base"][2] < 0 for r in records) / len(records) if truth == 0 else None
        aware_fp = sum(r["aware"][2] < 0 for r in records) / len(records) if truth == 0 else None
        base_width = statistics.fmean(r["base"][2] - r["base"][1] for r in records)
        aware_width = statistics.fmean(r["aware"][2] - r["aware"][1] for r in records)
        max_boundary_error = max(max(r["no_boundary_max_error"], r["extra_boundary_max_error"]) for r in records)
        aware_coverage_ok &= config["coverage_min"] <= aware_cov <= config["coverage_max"]
        if truth == 0:
            false_promotion_ok &= aware_fp <= config["null_false_promotion_max"]
        boundary_ok &= max_boundary_error <= config["boundary_invariance_tolerance"]
        if case_name != "stationary_null" and aware_cov - base_cov >= config["required_coverage_advantage"]:
            stress_improvements += 1
        summary.append({
            "case": case_name, "sessions": n, "replicates": len(records), "truth_ms": truth,
            "pooled_coverage": round(base_cov, 6), "segment_session_coverage": round(aware_cov, 6),
            "coverage_gain": round(aware_cov - base_cov, 6), "pooled_mean_width": round(base_width, 6),
            "segment_session_mean_width": round(aware_width, 6), "pooled_false_promotion": base_fp,
            "segment_session_false_promotion": aware_fp,
            "max_boundary_perturbation_error": max_boundary_error,
            "mean_detected_boundaries": round(statistics.fmean(len(r["edges"]) for r in records), 6),
        })

    h_supported = stress_improvements >= config["required_nonstationary_cells"]
    method_pass = aware_coverage_ok and false_promotion_ok and boundary_ok and all(controls.values())
    report = {
        "status": "PASS_METHOD_SCOPED" if method_pass else "FAIL_METHOD",
        "hypothesis": "SUPPORTED_SCOPED" if h_supported else "NOT_SUPPORTED_SCOPED",
        "input_replicates": input_count, "paired_windows_reconstructed": paired_windows,
        "censored_windows_retained": censored_windows,
        "row_accounting": "exact", "independent_raw_only_reconstruction": "PASS",
        "mutation_controls_rejected": controls,
        "gates": {"aware_coverage_in_range": aware_coverage_ok, "null_false_promotion_in_range": false_promotion_ok,
                  "boundary_invariant": boundary_ok, "required_stress_coverage_gains": stress_improvements},
        "cells": summary,
        "scope": "Synthetic finite CPU-only method qualification. No real route, model, GUI, runtime, task, or product effect."
    }
    return report


if __name__ == "__main__":
    with open(sys.argv[3], encoding="utf-8") as f:
        cfg = json.load(f)
    report = audit(sys.argv[1], sys.argv[2], cfg)
    with open(sys.argv[4], "w", encoding="utf-8", newline="\n") as f:
        json.dump(report, f, indent=2, sort_keys=True)
        f.write("\n")
    print(json.dumps({"status": report["status"], "hypothesis": report["hypothesis"],
                      "rows": report["paired_windows_reconstructed"], "controls": report["mutation_controls_rejected"]}, sort_keys=True))
