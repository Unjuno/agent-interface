#!/usr/bin/env python3
"""Single deterministic candidate for Issue #6133 T1c; standard library only."""
import hashlib
import json
import pathlib
import sys

SCENARIOS = ("no_aging", "monotone_leak", "cache_plateau", "thermal_only", "hidden_state")
POLICIES = ("NEVER", "FIXED_AGE_10", "RESOURCE_THRESHOLD_112")
JOBS = 40


def measurement(scenario, age, job_index):
    rss = 100
    latency = 20.0
    if scenario == "monotone_leak":
        rss += 2 * age
        latency += age
    elif scenario == "cache_plateau":
        rss += 3 * min(age, 8)
    elif scenario == "thermal_only":
        latency += 0.5 * max(0, job_index - 10)
    return rss, latency


def run_cell(scenario, policy):
    generation = 1
    age = 0
    rows = []
    for job_index in range(JOBS):
        age_before = age
        generation_before = generation
        rss, latency = measurement(scenario, age_before, job_index)
        pending = ["effect-10"] if job_index in (10, 11, 12) else []
        due = ((policy == "FIXED_AGE_10" and age_before >= 10) or
               (policy == "RESOURCE_THRESHOLD_112" and rss >= 112))
        decision = "not_due"
        if due:
            decision = "deferred_pending_obligation" if pending else "committed_restart"
        restart = decision == "committed_restart"
        generation_after = generation_before + int(restart)
        age_after = 0 if restart else age_before + 1
        late_receipt = None
        if restart:
            late_receipt = {
                "receipt_generation": generation_before,
                "current_generation": generation_after,
                "accepted": False,
                "reason": "stale_generation",
            }
        expected_output = f"answer-{job_index}"
        contaminated = scenario == "hidden_state" and job_index == 7
        observed_output = "stale-prior-request-marker" if contaminated else expected_output
        rows.append({
            "job_index": job_index,
            "generation_before": generation_before,
            "age_before": age_before,
            "rss_mb": rss,
            "latency_ms": latency,
            "host_temp_c": 30.0 + (max(0, job_index - 10) if scenario == "thermal_only" else 0),
            "pending_obligation_ids": pending,
            "restart_due": due,
            "restart_decision": decision,
            "generation_after": generation_after,
            "age_after": age_after,
            "late_receipt": late_receipt,
            "expected_output": expected_output,
            "observed_output": observed_output,
            "output_mismatch": observed_output != expected_output,
        })
        generation, age = generation_after, age_after
    segments = {}
    for row in rows:
        segments.setdefault(row["generation_before"], []).append(row)
    detected = False
    for segment in segments.values():
        by_age = sorted(segment, key=lambda r: r["age_before"])
        if len(by_age) < 2:
            continue
        first, last = by_age[0], by_age[-1]
        if (last["age_before"] - first["age_before"] >= 4 and
                last["rss_mb"] - first["rss_mb"] >= 8 and
                last["latency_ms"] - first["latency_ms"] >= 4):
            detected = True
    return {
        "scenario": scenario,
        "policy": policy,
        "rows": rows,
        "aging_detected": detected,
        "restart_count": sum(r["restart_decision"] == "committed_restart" for r in rows),
        "deferred_count": sum(r["restart_decision"] == "deferred_pending_obligation" for r in rows),
        "output_mismatch_count": sum(r["output_mismatch"] for r in rows),
    }


def main(output_path):
    cells = [run_cell(scenario, policy) for scenario in SCENARIOS for policy in POLICIES]
    raw = {
        "schema": "worker-aging-t1c-raw-v1",
        "scenario_sha256": hashlib.sha256(pathlib.Path(__file__).with_name("scenario.json").read_bytes()).hexdigest(),
        "cells": cells,
    }
    out = pathlib.Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(raw, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "CANDIDATE_COMPLETE", "cells": len(cells), "rows": sum(len(c["rows"]) for c in cells), "output": str(out)}))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: candidate.py OUTPUT_JSON")
    main(sys.argv[1])
