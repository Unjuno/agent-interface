#!/usr/bin/env python3
"""Exhaustive finite-trace scheduler replay for Issue #7794 T0 (synthetic only)."""
from __future__ import annotations

import hashlib
import itertools
import json
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).parent
INPUT = ROOT / "frozen_cases.json"


def active(case):
    return [j for j in case["jobs"] if not j["cancelled"]]


def all_feasible(case):
    jobs = active(case)
    domains = [range(j["release"], min(j["deadline"], j["fresh_until"]) - j["duration"] + 1) for j in jobs]
    out = []
    for starts in itertools.product(*domains):
        s = dict(zip((j["id"] for j in jobs), starts))
        occupied = []
        valid = True
        for j in jobs:
            slots = set(range(s[j["id"]], s[j["id"]] + j["duration"]))
            if any(slots & x for x in occupied):
                valid = False
                break
            occupied.append(slots)
            if any(s[p] + next(x["duration"] for x in jobs if x["id"] == p) > s[j["id"]]
                   for p in j["predecessors"]):
                valid = False
                break
        if valid:
            out.append(s)
    return out


def scenario_cost(case, schedule, scenario):
    jobs = active(case)
    return sum((Fraction(j["energy_per_slot"]) * sum(scenario["intensity"][t]
                for t in range(schedule[j["id"]], schedule[j["id"]] + j["duration"]))
                for j in jobs), Fraction(0))


def carbon(schedule, case, scenario):
    return scenario_cost(case, schedule, scenario)


def risk(schedule, case):
    scenarios = case["scenarios"]
    weights = [Fraction(str(x["weight"])) for x in scenarios]
    if sum(weights) != 1:
        raise ValueError("scenario weights must sum to 1")
    values = [scenario_cost(case, schedule, sc) for sc in scenarios]
    mean = sum((w * v for w, v in zip(weights, values)), Fraction(0))
    return mean + Fraction(1, 2) * (max(values) - mean)


def ordered(schedule, jobs, latest=False):
    vals = tuple(schedule[j["id"]] for j in jobs)
    # ASAP is canonical-order serial placement; latest maximizes total starts.
    return (-sum(vals), tuple(-x for x in vals)) if latest else vals


def solve_case(case):
    jobs = active(case)
    feas = all_feasible(case)
    if not feas:
        return {"case_id": case["id"], "disposition": "FAIL_CONSTRAINT", "feasible_schedule_count": 0,
                "methods": {m: None for m in ("asap", "latest_feasible", "carbon", "risk_aware")}}
    asap = min(feas, key=lambda s: ordered(s, jobs))
    mandatory = [j for j in jobs if not j["optional"]]
    eligible = [s for s in feas if all(s[j["id"]] == asap[j["id"]] for j in mandatory)]
    forecast_case = {"intensity": case["forecast"]}
    results = {
        "asap": asap,
        "latest_feasible": min(eligible, key=lambda s: ordered(s, jobs, latest=True)),
        "carbon": min(eligible, key=lambda s: (carbon(s, case, forecast_case), ordered(s, jobs))),
        "risk_aware": min(eligible, key=lambda s: (risk(s, case), ordered(s, jobs))),
    }
    methods = {}
    for method, schedule in results.items():
        methods[method] = {
            "starts": schedule,
            "forecast_cost": str(carbon(schedule, case, forecast_case)),
            "scenario_costs": {sc["id"]: str(scenario_cost(case, schedule, sc)) for sc in case["scenarios"]},
            "risk_score": str(risk(schedule, case)),
            "output_hashes": {j["id"]: j["output_sha256"] for j in jobs},
            "delayed_mandatory_jobs": [j["id"] for j in jobs if not j["optional"] and schedule[j["id"]] > j["release"]],
        }
    clairvoyant = {sc["id"]: str(min(scenario_cost(case, s, sc) for s in eligible)) for sc in case["scenarios"]}
    return {"case_id": case["id"], "disposition": "FEASIBLE", "feasible_schedule_count": len(feas),
            "carbon_policy_schedule_count_after_mandatory_freeze": len(eligible),
            "clairvoyant_cost_by_scenario": clairvoyant, "methods": methods}


def main():
    frozen = json.loads(INPUT.read_text())
    records = [solve_case(c) for c in frozen["cases"]]
    result = {
        "protocol": frozen["schema"],
        "scope": "finite synthetic scheduling logic only; no realistic trace, metered energy, or emissions claim",
        "input_sha256": hashlib.sha256(INPUT.read_bytes()).hexdigest(),
        "risk_rule": frozen["risk_rule"],
        "results": records,
        "pass_method_scoped": all(r["disposition"] == "FAIL_CONSTRAINT" if r["case_id"] == "infeasible_window" else r["disposition"] == "FEASIBLE" for r in records),
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    if not result["pass_method_scoped"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
