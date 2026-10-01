#!/usr/bin/env python3
"""Frozen deterministic paired-policy T0 for Issue #5715."""
import json
import sys

OPPS = [
    {"id": f"opp-{i:02d}", "boundary_ms": b, "hazard_ms": h, "event_id": f"evt-{i:02d}"}
    for i, (b, h) in enumerate(zip((100, 200, 300, 400), (110, 210, 310, 410)), 1)
]


def policy(name, admissions):
    return {
        "name": name,
        "opportunities": [
            {
                "id": opp["id"],
                "admission_ms": admission,
                "margin_ms": None if admission is None else opp["boundary_ms"] - admission,
                "event_id": opp["event_id"],
                "hazard_ms": opp["hazard_ms"],
                "forbidden_effect": admission is not None and admission > opp["boundary_ms"],
            }
            for opp, admission in zip(OPPS, admissions)
        ],
    }


def rows():
    early = policy("early", (40, 140, 240, 340))
    late = policy("late", (90, 190, 290, 390))
    yield {"case": "matched_policy_pair", "exogenous": OPPS, "arms": [early, late], "disposition": "OBSERVED"}
    yield {
        "case": "crossing", "opportunity": {"id": "cross-01", "boundary_ms": 100, "hazard_ms": 105, "event_id": "evt-cross"},
        "admission_ms": 103, "margin_ms": -3, "forbidden_effect": True, "disposition": "BOUNDARY_CROSSED",
    }
    yield {
        "case": "safe_stop", "opportunity": {"id": "stop-01", "boundary_ms": 100, "hazard_ms": 110, "event_id": "evt-stop"},
        "admission_ms": None, "stopped": True, "downstream_outcome": "UNKNOWN", "disposition": "STOP_RECORDED_OUTCOME_UNKNOWN",
    }
    yield {
        "case": "missing_time", "opportunity": {"id": "missing-01", "boundary_ms": 100, "hazard_ms": 110, "event_id": "evt-missing"},
        "admission_ms": None, "stopped": False, "margin_ms": None, "disposition": "UNKNOWN",
    }
    yield {
        "case": "altered_opportunities",
        "early_ids": ["opp-01", "opp-02", "opp-03", "opp-04"],
        "late_ids": ["opp-01", "opp-02", "opp-03", "opp-05"],
        "disposition": "HOLD_NO_STABLE_DENOMINATOR",
    }
    yield {
        "case": "equality", "opportunity": {"id": "eq-01", "boundary_ms": 100, "hazard_ms": 110, "event_id": "evt-eq"},
        "admission_ms": 100, "margin_ms": 0, "forbidden_effect": False, "disposition": "ZERO_MARGIN_NOT_CROSSED",
    }


def main(path):
    with open(path, "w", encoding="utf-8") as out:
        for item in rows():
            out.write(json.dumps(item, sort_keys=True, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    main(sys.argv[1])
