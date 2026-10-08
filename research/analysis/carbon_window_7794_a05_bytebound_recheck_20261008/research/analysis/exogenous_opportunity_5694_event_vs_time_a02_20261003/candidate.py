#!/usr/bin/env python3
"""Emit the frozen finite raw schedule and candidate event/time summaries."""
import argparse
import json
from pathlib import Path


def union_length(intervals):
    ordered = sorted((int(a), int(b)) for a, b in intervals if b > a)
    total = 0
    end = None
    for start, stop in ordered:
        if end is None or start > end:
            total += stop - start
            end = stop
        elif stop > end:
            total += stop - end
            end = stop
    return total


def summarize(schedule, route):
    if not schedule["onset_schedule_present"] or not schedule["clock_aligned"]:
        return {"status": "HOLD_NO_ELIGIBLE_ONSET_CLOCK", "event_coverage": None, "time_coverage": None}
    opportunities = schedule["opportunities"]
    ids = {row["id"] for row in opportunities}
    met = set(route["effect_opportunity_ids"])
    windows = [(row["onset"], row["expiry"]) for row in opportunities]
    denominator = union_length(windows)
    numerator = union_length(
        [(max(a, c), min(b, d)) for a, b in windows for c, d in route["coverage_intervals"] if max(a, c) < min(b, d)]
    )
    return {
        "status": "SCOPED",
        "event_coverage": {"numerator": len(ids & met), "denominator": len(ids)},
        "time_coverage": {"numerator": numerator, "denominator": denominator},
    }


def build_raw():
    equal = [{"id": f"E{i}", "onset": i * 10, "expiry": (i + 1) * 10} for i in range(4)]
    varied = [{"id": f"S{i:02}", "onset": i, "expiry": i + 1} for i in range(10)]
    varied.append({"id": "L", "onset": 10, "expiry": 100})
    return [
        {
            "case_id": "equal_duration",
            "onset_schedule_present": True,
            "clock_aligned": True,
            "opportunities": equal,
            "routes": [
                {"route_id": "half", "effect_opportunity_ids": ["E0", "E2"], "coverage_intervals": [[0, 10], [20, 30]]},
                {"route_id": "all", "effect_opportunity_ids": ["E0", "E1", "E2", "E3"], "coverage_intervals": [[0, 40]]},
            ],
        },
        {
            "case_id": "heterogeneous_duration",
            "onset_schedule_present": True,
            "clock_aligned": True,
            "opportunities": varied,
            "routes": [
                {"route_id": "long_only", "effect_opportunity_ids": ["L"], "coverage_intervals": [[10, 100]]},
                {"route_id": "shorts_only", "effect_opportunity_ids": [f"S{i:02}" for i in range(10)], "coverage_intervals": [[0, 10]]},
            ],
        },
        {
            "case_id": "no_onset_oracle",
            "onset_schedule_present": False,
            "clock_aligned": False,
            "opportunities": None,
            "routes": [
                {"route_id": "apparent_fast", "effect_opportunity_ids": [], "coverage_intervals": [[0, 5]]},
                {"route_id": "apparent_slow", "effect_opportunity_ids": [], "coverage_intervals": [[5, 10]]},
            ],
        },
    ]


def run():
    scenarios = build_raw()
    for scenario in scenarios:
        for route in scenario["routes"]:
            route["claimed_summary"] = summarize(scenario, route)
    return {"schema": "exogenous-opportunity-event-time-a02-v1", "scenarios": scenarios}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    result = run()
    out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"schema": result["schema"], "scenario_count": len(result["scenarios"]), "output": str(out)}, sort_keys=True))


if __name__ == "__main__":
    main()
