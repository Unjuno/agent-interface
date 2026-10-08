"""Independent raw-only reconstruction for Issue #5557 T15.

This module intentionally does not import or execute experiment.py.
"""

from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path


HORIZON = 4


def reference_row(capacity: int, bits: tuple[int, ...]) -> dict:
    hi = [2 * value for value in bits]
    observer_total = 4
    aggregate_demand = sum(hi) + observer_total + 1
    aggregate_feasible = aggregate_demand <= capacity * HORIZON

    baseline = []
    for tick in range(HORIZON):
        verifier = hi[tick] if hi[tick] <= capacity else capacity
        left = capacity - verifier
        observation = 1 if left else 0
        baseline.append(
            {"tick": tick, "hi": verifier, "observer": observation, "planner": left - observation, "background": 0}
        )
    missed_hi = sum(baseline[tick]["hi"] != hi[tick] for tick in range(HORIZON))
    missed_observations = sum(item["observer"] != 1 for item in baseline)

    collision_ticks = [tick for tick in range(HORIZON) if hi[tick] + 1 > capacity]
    if collision_ticks:
        result = {"status": "UNSAT_SERVICE_CONTRACT", "reason": "same_tick_hi_observer_conflict", "dispatch": []}
    else:
        residual_by_tick = [capacity - hi[tick] - 1 for tick in range(HORIZON)]
        planner_by_tick = [0] * HORIZON
        needed = 1
        for tick in range(HORIZON):
            amount = min(residual_by_tick[tick], needed) if needed else 0
            planner_by_tick[tick] = amount
            needed -= amount
        if needed:
            result = {"status": "UNSAT_SERVICE_CONTRACT", "reason": "lo_planner_minimum_unmet", "dispatch": []}
        else:
            result = {
                "status": "SAT",
                "reason": None,
                "dispatch": [
                    {
                        "tick": tick,
                        "hi": hi[tick],
                        "observer": 1,
                        "planner": planner_by_tick[tick],
                        "background": residual_by_tick[tick] - planner_by_tick[tick],
                    }
                    for tick in range(HORIZON)
                ],
            }
    return {
        "case_id": f"cap{capacity}-hi{''.join(map(str, bits))}",
        "capacity_per_tick": capacity,
        "hi_arrivals": list(bits),
        "hi_units_per_arrival": 2,
        "observer_units_per_tick": 1,
        "lo_planner_minimum": 1,
        "aggregate_total": {"demand": aggregate_demand, "capacity": capacity * HORIZON, "feasible": aggregate_feasible},
        "hi_priority_baseline": {
            "hi_deadline_misses": missed_hi,
            "observer_max_gap_violations": missed_observations,
            "dispatch": baseline,
        },
        "temporal_contract": result,
    }


def validate(rows: list[dict]) -> list[str]:
    errors: list[str] = []
    expected = [
        reference_row(capacity, bits)
        for capacity in (2, 3)
        for bits in itertools.product((0, 1), repeat=HORIZON)
    ]
    actual_by_id = {row.get("case_id"): row for row in rows}
    if len(rows) != 32 or len(actual_by_id) != 32:
        errors.append("row_count_or_unique_id_mismatch")
    for wanted in expected:
        found = actual_by_id.get(wanted["case_id"])
        if found != wanted:
            errors.append(f"independent_reconstruction_mismatch:{wanted['case_id']}")
    if not any(row["capacity_per_tick"] == 2 and row["aggregate_total"]["feasible"] and row["temporal_contract"]["status"] == "UNSAT_SERVICE_CONTRACT" for row in rows):
        errors.append("aggregate_temporal_gap_not_exposed")
    if not any(row["capacity_per_tick"] == 3 and row["temporal_contract"]["status"] == "SAT" and sum(row["hi_arrivals"]) == 3 for row in rows):
        errors.append("feasible_planner_service_control_missing")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("raw")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    raw = Path(args.raw).read_bytes()
    rows = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line]
    errors = validate(rows)

    controls = []
    unsat = next(row for row in rows if row["capacity_per_tick"] == 2 and sum(row["hi_arrivals"]) == 1)
    tampered = json.loads(json.dumps(rows))
    target = next(row for row in tampered if row["case_id"] == unsat["case_id"])
    target["temporal_contract"]["status"] = "SAT"
    controls.append({"name": "false_sat_on_temporal_conflict", "rejected": bool(validate(tampered))})

    feasible = next(row for row in rows if row["capacity_per_tick"] == 3 and sum(row["hi_arrivals"]) == 0)
    tampered = json.loads(json.dumps(rows))
    target = next(row for row in tampered if row["case_id"] == feasible["case_id"])
    target["temporal_contract"]["dispatch"][0]["observer"] = 0
    controls.append({"name": "omitted_required_observation", "rejected": bool(validate(tampered))})

    tampered = json.loads(json.dumps(rows))
    target = next(row for row in tampered if row["case_id"] == feasible["case_id"])
    target["temporal_contract"]["dispatch"] = [
        {**entry, "planner": 0, "background": entry["background"] + entry["planner"]}
        for entry in target["temporal_contract"]["dispatch"]
    ]
    controls.append({"name": "silent_lo_planner_minimum_drop", "rejected": bool(validate(tampered))})

    result = {
        "status": "PASS_TEMPORAL_SERVICE_CONTRACT_SCOPED" if not errors and all(item["rejected"] for item in controls) else "FAIL_AUDIT",
        "rows": len(rows),
        "errors": errors,
        "mutation_controls": controls,
        "scope": "finite synthetic 4-tick shared-resource model only",
    }
    Path(args.output).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if result["status"] != "PASS_TEMPORAL_SERVICE_CONTRACT_SCOPED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
