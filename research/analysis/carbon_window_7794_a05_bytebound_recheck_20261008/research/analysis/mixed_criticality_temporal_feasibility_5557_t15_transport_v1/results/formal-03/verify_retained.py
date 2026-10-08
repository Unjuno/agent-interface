"""Post-retrieval integrity check; does not invoke the frozen candidate/auditor."""

from __future__ import annotations

import itertools
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
rows = [json.loads(line) for line in (ROOT / "raw.jsonl").read_text().splitlines()]
assert len(rows) == 32
by_id = {row["case_id"]: row for row in rows}
expected_ids = {
    f"cap{capacity}-hi{''.join(map(str, bits))}"
    for capacity in (2, 3)
    for bits in itertools.product((0, 1), repeat=4)
}
assert len(by_id) == 32 and set(by_id) == expected_ids

for row in rows:
    capacity = row["capacity_per_tick"]
    bits = row["hi_arrivals"]
    total_demand = 2 * sum(bits) + 4 + 1
    assert row["aggregate_total"] == {
        "demand": total_demand,
        "capacity": capacity * 4,
        "feasible": total_demand <= capacity * 4,
    }
    residuals = [capacity - 2 * bit - 1 for bit in bits]
    temporal = row["temporal_contract"]
    conflict = any(residual < 0 for residual in residuals)
    if conflict:
        assert temporal == {
            "status": "UNSAT_SERVICE_CONTRACT",
            "reason": "same_tick_hi_observer_conflict",
            "dispatch": [],
        }
    elif sum(residuals) < 1:
        assert temporal == {
            "status": "UNSAT_SERVICE_CONTRACT",
            "reason": "lo_planner_minimum_unmet",
            "dispatch": [],
        }
    else:
        assert temporal["status"] == "SAT" and temporal["reason"] is None
        assert len(temporal["dispatch"]) == 4
        assert sum(item["planner"] for item in temporal["dispatch"]) >= 1
        for tick, item in enumerate(temporal["dispatch"]):
            assert item["tick"] == tick
            assert item["hi"] == 2 * bits[tick]
            assert item["observer"] == 1
            assert item["planner"] + item["background"] == residuals[tick]

audit = json.loads((ROOT / "AUDIT.json").read_text())
assert audit["status"] == "PASS_TEMPORAL_SERVICE_CONTRACT_SCOPED"
assert audit["rows"] == 32 and audit["errors"] == []
assert all(control["rejected"] for control in audit["mutation_controls"])

counts = {
    capacity: {
        status: sum(
            row["capacity_per_tick"] == capacity
            and row["temporal_contract"]["status"] == status
            for row in rows
        )
        for status in ("SAT", "UNSAT_SERVICE_CONTRACT")
    }
    for capacity in (2, 3)
}
assert counts == {
    2: {"SAT": 1, "UNSAT_SERVICE_CONTRACT": 15},
    3: {"SAT": 15, "UNSAT_SERVICE_CONTRACT": 1},
}
aggregate_temporal_gap = sum(
    row["capacity_per_tick"] == 2
    and row["aggregate_total"]["feasible"]
    and row["temporal_contract"]["status"] == "UNSAT_SERVICE_CONTRACT"
    for row in rows
)
assert aggregate_temporal_gap == 4

print(
    json.dumps(
        {
            "posthoc_raw_invariant_check": "PASS",
            "rows": len(rows),
            "decision_counts_by_capacity": counts,
            "aggregate_feasible_but_temporal_unsat_at_capacity_2": aggregate_temporal_gap,
            "official_auditor_status": audit["status"],
        },
        sort_keys=True,
    )
)
