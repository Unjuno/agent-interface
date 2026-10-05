#!/usr/bin/env python3
"""Independent result audit using recursive enumeration, not run_t0 helpers."""
import hashlib
import itertools
import json
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).parent
spec = json.loads((HERE / "frozen_cases.json").read_text())
got = json.loads((HERE / "result.json").read_text())
assert got["input_sha256"] == hashlib.sha256((HERE / "frozen_cases.json").read_bytes()).hexdigest()
assert [x["case_id"] for x in got["results"]] == [x["id"] for x in spec["cases"]]


def reference(c):
    jobs = [j for j in c["jobs"] if not j["cancelled"]]
    all_schedules = []

    def visit(index, assignment, occupied):
        if index == len(jobs):
            all_schedules.append(dict(assignment))
            return
        j = jobs[index]
        last = min(j["deadline"], j["fresh_until"]) - j["duration"]
        for t in range(j["release"], last + 1):
            slots = set(range(t, t + j["duration"]))
            if slots & occupied:
                continue
            if any(assignment[p] + next(q["duration"] for q in jobs if q["id"] == p) > t
                   for p in j["predecessors"]):
                continue
            assignment[j["id"]] = t
            visit(index + 1, assignment, occupied | slots)
            del assignment[j["id"]]

    visit(0, {}, set())
    return jobs, all_schedules


def actual_cost(c, schedule, intensity):
    return sum(Fraction(j["energy_per_slot"]) * sum(intensity[t]
               for t in range(schedule[j["id"]], schedule[j["id"]] + j["duration"]))
               for j in c["jobs"] if not j["cancelled"])


def risk_cost(c, schedule):
    scs = c["scenarios"]
    vals = [actual_cost(c, schedule, x["intensity"]) for x in scs]
    mean = sum(Fraction(str(x["weight"])) * v for x, v in zip(scs, vals))
    return mean + Fraction(1, 2) * (max(vals) - mean)


for c, row in zip(spec["cases"], got["results"]):
    jobs, schedules = reference(c)
    if not schedules:
        assert row["case_id"] == "infeasible_window" and row["disposition"] == "FAIL_CONSTRAINT"
        assert row["feasible_schedule_count"] == 0
        continue
    assert row["disposition"] == "FEASIBLE"
    assert row["feasible_schedule_count"] == len(schedules)
    methods = row["methods"]
    for name, rec in methods.items():
        s = rec["starts"]
        assert s in schedules, (c["id"], name, "not independently feasible")
        assert rec["output_hashes"] == {j["id"]: j["output_sha256"] for j in jobs}
        assert rec["delayed_mandatory_jobs"] == []
        assert rec["forecast_cost"] == str(actual_cost(c, s, c["forecast"]))
        assert rec["scenario_costs"] == {sc["id"]: str(actual_cost(c, s, sc["intensity"])) for sc in c["scenarios"]}
        assert rec["risk_score"] == str(risk_cost(c, s))
    def vec(s): return tuple(s[j["id"]] for j in jobs)
    asap = min(schedules, key=vec)
    fixed = [s for s in schedules if all(s[j["id"]] == asap[j["id"]] for j in jobs if not j["optional"])]
    latest = min(fixed, key=lambda s: (-sum(vec(s)), tuple(-x for x in vec(s))))
    assert methods["asap"]["starts"] == asap
    assert methods["latest_feasible"]["starts"] == latest
    assert methods["carbon"]["forecast_cost"] == str(min(actual_cost(c, s, c["forecast"]) for s in fixed))
    assert methods["risk_aware"]["risk_score"] == str(min(risk_cost(c, s) for s in fixed))
    assert row["clairvoyant_cost_by_scenario"] == {
        sc["id"]: str(min(actual_cost(c, s, sc["intensity"]) for s in fixed)) for sc in c["scenarios"]
    }

assert got["pass_method_scoped"] is True
by_id = {r["case_id"]: r for r in got["results"]}
assert by_id["no_flex"]["feasible_schedule_count"] == 1
assert len({json.dumps(x["starts"], sort_keys=True) for x in by_id["no_flex"]["methods"].values()}) == 1
flat = by_id["flat_carbon"]["methods"]
assert len({x["forecast_cost"] for x in flat.values()}) == 1
assert by_id["inverted_carbon"]["methods"]["carbon"]["forecast_cost"] == by_id["inverted_carbon"]["methods"]["asap"]["forecast_cost"]
assert len(spec["cases"][0]["scenarios"]) == 3
assert by_id["cancellation"]["methods"]["carbon"]["output_hashes"].keys() == {"live"}
assert by_id["precedence"]["feasible_schedule_count"] > 0
assert by_id["long_job"]["feasible_schedule_count"] > 0
assert by_id["mandatory_guard"]["methods"]["carbon"]["starts"]["mandatory"] == by_id["mandatory_guard"]["methods"]["asap"]["starts"]["mandatory"]
print("independent recursive schedule/cost/hash/oracle audit: PASS (9 cases)")
