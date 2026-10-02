#!/usr/bin/env python3
"""Deterministic finite scheduler candidate for Issue #5370 T7."""

import argparse
import json
from pathlib import Path


POLICIES = ("DEADLINE_ONLY", "NAIVE_UNBOUNDED_PI", "COMPOSED_BOUNDED_PI")


def simulate(scenario, policy, max_ticks, fairness_bound):
    left = {"L": scenario["holder_ticks"], "M": scenario["middle_ticks"],
            "B": scenario["background_ticks"], "H": scenario["verifier_ticks"]}
    owner_r1 = "L"
    owner_r2 = "M" if scenario["topology"] == "nested" else None
    cancelled = False
    cycle_admitted = bool(scenario["attempt_cycle"] and policy == "NAIVE_UNBOUNDED_PI")
    events = []
    boost_used = {"L": 0, "M": 0}
    boost_total = {"L": 0, "M": 0}
    cap_tick = None
    first_medium_after_cap = None
    h_finish = None
    h_status = "UNKNOWN_STALE"
    t = 0

    if scenario["attempt_cycle"]:
        if cycle_admitted:
            events.append({"tick": 0, "kind": "CYCLE_EDGE_ADMITTED", "job": "L", "resource": "R2"})
        else:
            events.append({"tick": 0, "kind": "CYCLE_EDGE_REFUSED", "job": "L", "resource": "R2"})

    while t < max_ticks:
        if left["H"] == 0 and left["M"] == 0 and left["B"] == 0 and (left["L"] == 0 or cancelled):
            events.append({"tick": t, "kind": "ALL_WORK_COMPLETE"})
            break
        if scenario["holder_cancel_tick"] == t and not cancelled and owner_r1 == "L":
            cancelled = True
            owner_r1 = None
            events.append({"tick": t, "kind": "HOLDER_CANCEL_RELEASE", "job": "L", "resource": "R1"})
        if scenario["claim_expiry_tick"] == t:
            events.append({"tick": t, "kind": "CLAIM_EXPIRED", "job": "H"})

        if cycle_admitted:
            runnable = []
        else:
            if left["L"] > 0 and not cancelled:
                runnable = ["L"]
            else:
                runnable = []
            if left["M"] > 0 and (scenario["topology"] == "direct" or owner_r1 is None):
                runnable.append("M")
            if left["B"] > 0:
                runnable.append("B")
            h_ready = left["H"] > 0 and (
                (scenario["topology"] == "direct" and owner_r1 is None) or
                (scenario["topology"] == "nested" and owner_r2 is None)
            )
            if h_ready:
                runnable.append("H")

        if not runnable:
            events.append({"tick": t, "kind": "DEADLOCK" if cycle_admitted else "NO_RUNNABLE_JOB"})
            break

        effective = {"L": 1, "M": 2, "B": 2, "H": 3}
        h_waits = left["H"] > 0 and not h_ready
        valid_claim = (
            scenario["claim_authenticated"] and scenario["claim_live"] and
            scenario["graph_complete"] and
            (scenario["claim_expiry_tick"] is None or t < scenario["claim_expiry_tick"])
        )
        if policy == "COMPOSED_BOUNDED_PI" and h_waits and valid_claim:
            if scenario["topology"] == "direct" and owner_r1 == "L" and boost_used["L"] < scenario["cap_ticks"]:
                effective["L"] = 3
            elif scenario["topology"] == "nested" and owner_r2 == "M":
                if owner_r1 == "L" and boost_used["L"] < scenario["cap_ticks"]:
                    effective["L"] = 3
                if owner_r1 is None and boost_used["M"] < scenario["cap_ticks"]:
                    effective["M"] = 3
        elif policy == "NAIVE_UNBOUNDED_PI" and h_waits:
            if scenario["topology"] == "direct" and owner_r1 == "L":
                effective["L"] = scenario["claimed_priority"]
            elif scenario["topology"] == "nested" and owner_r2 == "M":
                if owner_r1 == "L":
                    effective["L"] = scenario["claimed_priority"]
                if owner_r1 is None:
                    effective["M"] = scenario["claimed_priority"]

        order = {"H": 4, "M": 3, "B": 2, "L": 1}
        job = max(runnable, key=lambda name: (effective[name], order[name]))
        inherited = effective[job] > {"L": 1, "M": 2, "B": 2, "H": 3}[job]
        events.append({"tick": t, "kind": "RUN", "job": job, "effective_priority": effective[job], "inherited": inherited})
        left[job] -= 1
        if inherited and job in boost_total:
            boost_total[job] += 1
            if policy == "COMPOSED_BOUNDED_PI":
                boost_used[job] += 1
            if policy == "COMPOSED_BOUNDED_PI" and boost_used[job] == scenario["cap_ticks"] and cap_tick is None:
                cap_tick = t + 1
                events.append({"tick": cap_tick, "kind": "INHERITANCE_CAP_EXHAUSTED", "job": job})
        if job in ("M", "B") and cap_tick is not None and first_medium_after_cap is None:
            first_medium_after_cap = t
        if job == "L" and left["L"] == 0 and owner_r1 == "L":
            owner_r1 = None
            events.append({"tick": t + 1, "kind": "RELEASE", "job": "L", "resource": "R1"})
        if job == "M" and left["M"] == 0 and owner_r2 == "M":
            owner_r2 = None
            events.append({"tick": t + 1, "kind": "RELEASE", "job": "M", "resource": "R2"})
        if job == "H" and left["H"] == 0:
            h_finish = t + 1
            h_status = "ADMITTED_FRESH" if h_finish <= scenario["deadline"] else "UNKNOWN_STALE"
            events.append({"tick": h_finish, "kind": h_status, "job": "H"})
        t += 1

    h_deadline_miss = h_finish is None or h_finish > scenario["deadline"]
    medium_service_delay = None
    if cap_tick is not None and first_medium_after_cap is not None:
        medium_service_delay = first_medium_after_cap - cap_tick
    return {
        "scenario_id": scenario["id"], "policy": policy, "events": events,
        "verifier_finish_tick": h_finish, "verifier_status": h_status,
        "verifier_deadline_miss": h_deadline_miss,
        "cycle_edge_admitted": cycle_admitted,
        "boost_ticks": boost_total,
        "inheritance_cap_tick": cap_tick,
        "medium_first_service_delay_after_cap": medium_service_delay,
        "medium_completed": left["M"] == 0 and left["B"] == 0,
        "background_completed": left["B"] == 0,
        "holder_cancelled_and_released": cancelled and owner_r1 is None,
        "resource_r1_held_at_end": owner_r1 is not None,
        "resource_r2_held_at_end": owner_r2 is not None,
    }


def run(scenarios):
    rows = []
    for scenario in scenarios["scenarios"]:
        for policy in POLICIES:
            rows.append(simulate(scenario, policy, scenarios["max_ticks"], scenarios["fairness_bound_ticks"]))
    return {"allocation_id": scenarios["allocation_id"], "rows": rows}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenarios", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    inputs = json.loads(args.scenarios.read_text())
    result = run(inputs)
    args.out.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    main()
