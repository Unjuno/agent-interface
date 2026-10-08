"""Finite synthetic response-capacity successor for Issue #5771."""

from __future__ import annotations

import json
from pathlib import Path


SCENARIOS = {
    "spare_capacity": {
        "now_ms": 10, "planner_busy_until_ms": 20, "threat_deadline_ms": 80,
        "lease_expires_ms": 100, "handoff_offered": False, "handoff_accepted": False,
        "release_lane_available": True,
    },
    "shared_saturation": {
        "now_ms": 10, "planner_busy_until_ms": 120, "threat_deadline_ms": 80,
        "lease_expires_ms": 100, "handoff_offered": False, "handoff_accepted": False,
        "release_lane_available": False,
    },
    "expired_lease": {
        "now_ms": 50, "planner_busy_until_ms": 50, "threat_deadline_ms": 80,
        "lease_expires_ms": 40, "handoff_offered": False, "handoff_accepted": False,
        "release_lane_available": True,
    },
    "handoff_not_accepted": {
        "now_ms": 10, "planner_busy_until_ms": 120, "threat_deadline_ms": 80,
        "lease_expires_ms": 100, "handoff_offered": True, "handoff_accepted": False,
        "release_lane_available": False,
    },
}

ARMS = ("nominal_repertoire", "capacity_aware", "reserved_safety_lane")


def classify(scenario: dict, arm: str) -> dict:
    planner_ready = scenario["planner_busy_until_ms"] <= scenario["threat_deadline_ms"]
    lease_valid = scenario["now_ms"] < scenario["lease_expires_ms"]
    accepted_handoff = scenario["handoff_offered"] and scenario["handoff_accepted"]
    if arm == "nominal_repertoire":
        threat = "COVERED"  # Nominal arm sees a response class, not its current capacity.
    else:
        threat = "COVERED" if ((planner_ready and lease_valid) or accepted_handoff) else "NO_RESPONSE"
    release_available = arm == "nominal_repertoire" or arm == "reserved_safety_lane" or scenario["release_lane_available"]
    stuck_input = "COVERED" if release_available else "SAFE_STOP_ONLY"
    return {"threat_requires_replan": threat, "stuck_input_requires_release": stuck_input}


def run() -> dict:
    rows = []
    for scenario_id, facts in SCENARIOS.items():
        for arm in ARMS:
            rows.append({"scenario_id": scenario_id, "arm": arm,
                         "facts": facts, "outcomes": classify(facts, arm),
                         "task_attainable": all(value == "COVERED" for value in classify(facts, arm).values()),
                         "authority_effect_applied": False})
    return {"rows": rows, "row_count": len(rows)}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
