"""One-shot candidate for Issue #5557 T15 finite scheduling traces."""

from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path


HORIZON = 4
OBSERVER_UNITS_PER_TICK = 1
HI_UNITS_PER_ARRIVAL = 2
LO_MINIMUM = 1
CAPACITIES = (2, 3)


def build_row(capacity: int, bits: tuple[int, ...]) -> dict:
    hi = [HI_UNITS_PER_ARRIVAL * bit for bit in bits]
    aggregate_demand = sum(hi) + HORIZON * OBSERVER_UNITS_PER_TICK + LO_MINIMUM
    aggregate_feasible = aggregate_demand <= capacity * HORIZON

    priority_dispatch = []
    for tick, hi_demand in enumerate(hi):
        hi_service = min(hi_demand, capacity)
        remaining = capacity - hi_service
        observer_service = min(OBSERVER_UNITS_PER_TICK, remaining)
        remaining -= observer_service
        planner_service = remaining
        priority_dispatch.append(
            {
                "tick": tick,
                "hi": hi_service,
                "observer": observer_service,
                "planner": planner_service,
                "background": 0,
            }
        )

    priority_observer_misses = sum(
        row["observer"] != OBSERVER_UNITS_PER_TICK for row in priority_dispatch
    )
    priority_hi_misses = sum(row["hi"] != hi[tick] for tick, row in enumerate(priority_dispatch))

    conflicts = [
        tick
        for tick, hi_demand in enumerate(hi)
        if hi_demand + OBSERVER_UNITS_PER_TICK > capacity
    ]
    if conflicts:
        proposed = {"status": "UNSAT_SERVICE_CONTRACT", "reason": "same_tick_hi_observer_conflict", "dispatch": []}
    else:
        dispatch = []
        planner_remaining = LO_MINIMUM
        for tick, hi_demand in enumerate(hi):
            observer = OBSERVER_UNITS_PER_TICK
            residual = capacity - hi_demand - observer
            planner = min(residual, planner_remaining)
            planner_remaining -= planner
            dispatch.append(
                {
                    "tick": tick,
                    "hi": hi_demand,
                    "observer": observer,
                    "planner": planner,
                    "background": residual - planner,
                }
            )
        if planner_remaining:
            proposed = {"status": "UNSAT_SERVICE_CONTRACT", "reason": "lo_planner_minimum_unmet", "dispatch": []}
        else:
            proposed = {"status": "SAT", "reason": None, "dispatch": dispatch}

    return {
        "case_id": f"cap{capacity}-hi{''.join(map(str, bits))}",
        "capacity_per_tick": capacity,
        "hi_arrivals": list(bits),
        "hi_units_per_arrival": HI_UNITS_PER_ARRIVAL,
        "observer_units_per_tick": OBSERVER_UNITS_PER_TICK,
        "lo_planner_minimum": LO_MINIMUM,
        "aggregate_total": {
            "demand": aggregate_demand,
            "capacity": capacity * HORIZON,
            "feasible": aggregate_feasible,
        },
        "hi_priority_baseline": {
            "hi_deadline_misses": priority_hi_misses,
            "observer_max_gap_violations": priority_observer_misses,
            "dispatch": priority_dispatch,
        },
        "temporal_contract": proposed,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as stream:
        for capacity in CAPACITIES:
            for bits in itertools.product((0, 1), repeat=HORIZON):
                stream.write(json.dumps(build_row(capacity, bits), sort_keys=True, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    main()
