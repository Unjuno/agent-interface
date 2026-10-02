#!/usr/bin/env python3
"""Construct fresh, fixed #6613 EDF successor traces; no policies are run."""
import json
import random
from pathlib import Path

ALLOCATION = "SERVICE-FAIRNESS-6613-EDF-A01-20261003"
SEEDS = range(20000, 20040)
STRATA = ("asymmetric_deadlines", "burst_recovery", "revocation_mandatory")
OUT = Path(__file__).with_name("fixture.json")


def task(task_id, principal, arrival, service, deadline, eligible_until, mandatory=False):
    return {
        "id": task_id,
        "principal": principal,
        "arrival": arrival,
        "service": service,
        "deadline": deadline,
        "eligible_until": eligible_until,
        "mandatory": mandatory,
    }


def make_trace(seed, stratum):
    rng = random.Random(seed * 17 + STRATA.index(stratum) * 100003)
    jobs = []
    schedules = {
        "asymmetric_deadlines": ([0, 1, 2, 4, 5, 7], [0, 3, 5, 6, 8, 10]),
        "burst_recovery": ([0, 0, 1, 1, 3, 4], [0, 2, 2, 4, 5, 7]),
        "revocation_mandatory": ([0, 2, 3, 5, 6, 8], [0, 1, 4, 5, 7, 9]),
    }
    arrivals = schedules[stratum]
    for principal_index, principal in enumerate(("A", "B")):
        for i, base_arrival in enumerate(arrivals[principal_index]):
            arrival = base_arrival + rng.randrange(0, 2)
            service = rng.randint(1, 6)
            if stratum == "asymmetric_deadlines":
                slack = rng.choice((7, 9, 11, 13)) if principal == "A" else rng.choice((3, 4, 6, 8))
            elif stratum == "burst_recovery":
                slack = rng.choice((3, 5, 8, 12))
            else:
                slack = rng.choice((5, 7, 10, 14))
            hard_horizon = rng.choice((service + 5, service + 9, service + 15))
            eligible_until = arrival + hard_horizon
            if stratum == "revocation_mandatory" and principal_index == seed % 2 and i == 3:
                # One deliberately short but still initially feasible hard horizon.
                eligible_until = arrival + service + 1
            jobs.append(task(
                f"{principal}-{i}", principal, arrival, service,
                arrival + slack, eligible_until,
            ))
    if stratum == "revocation_mandatory":
        interrupt_at = 5 + (seed % 3)
        jobs.append(task("SYS-release", "SYSTEM", interrupt_at, 1,
                         interrupt_at + 1, None, mandatory=True))
    jobs.sort(key=lambda j: (j["arrival"], j["id"]))
    return {"seed": seed, "stratum": stratum, "tasks": jobs}


def main():
    fixture = {
        "allocation_id": ALLOCATION,
        "generator": "prepare.py / CPython random.Random / fixed seeds 20000..20039",
        "tick_unit": "integer synthetic tick",
        "policies": ["fifo", "shortest_service", "edf"],
        "strata": list(STRATA),
        "traces": [make_trace(seed, stratum) for seed in SEEDS for stratum in STRATA],
        "scope": "authored finite synthetic method-only traces",
    }
    data = (json.dumps(fixture, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()
    if OUT.exists():
        raise FileExistsError(f"refusing to replace frozen fixture: {OUT}")
    OUT.write_bytes(data)
    print(json.dumps({"path": OUT.name, "bytes": len(data), "traces": len(fixture["traces"]),
                      "allocation_id": ALLOCATION}, sort_keys=True))


if __name__ == "__main__":
    main()
