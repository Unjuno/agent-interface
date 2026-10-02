#!/usr/bin/env python3
"""Derive route-stability labels from an explicit finite endpoint graph."""

import json
import sys
from pathlib import Path


def _integer(value, field):
    if type(value) is not int or value < 0:
        raise ValueError(f"{field} must be a non-negative integer")
    return value


def evaluate(fixture):
    if fixture.get("selector") not in ("min_cost", "max_cost"):
        raise ValueError("selector must be min_cost or max_cost")
    routes = fixture.get("routes")
    if not isinstance(routes, list) or len(routes) < 2:
        raise ValueError("routes must contain at least two endpoints")

    route_ids = []
    normalized = []
    for route in routes:
        route_id = route.get("id")
        if not isinstance(route_id, str) or not route_id:
            raise ValueError("route id must be a non-empty string")
        route_ids.append(route_id)
        normalized.append(
            (
                route_id,
                _integer(route.get("baseline_ms"), "baseline_ms"),
                _integer(route.get("intervention_ms"), "intervention_ms"),
            )
        )
    if len(set(route_ids)) != len(route_ids):
        raise ValueError("route ids must be unique")

    def optimum(cost_index):
        costs = [route[cost_index] for route in normalized]
        target = min(costs) if fixture["selector"] == "min_cost" else max(costs)
        return sorted(route[0] for route in normalized if route[cost_index] == target)

    baseline = optimum(1)
    intervention = optimum(2)
    if len(baseline) != 1 or len(intervention) != 1:
        status = "TIE_SET"
        delta = None
    elif baseline != intervention:
        status = "NONSTATIONARY_INTERVENTION"
        delta = None
    else:
        status = "ROUTE_STABLE"
        chosen = baseline[0]
        before = next(route[1] for route in normalized if route[0] == chosen)
        after = next(route[2] for route in normalized if route[0] == chosen)
        delta = after - before

    return {
        "case_id": fixture["id"],
        "selector": fixture["selector"],
        "baseline_optima": baseline,
        "intervention_optima": intervention,
        "status": status,
        "endpoint_delta_ms": delta,
    }


def main(argv):
    if len(argv) != 2:
        raise SystemExit("usage: candidate.py FIXTURES.json")
    fixtures = json.loads(Path(argv[1]).read_text())
    results = [evaluate(fixture) for fixture in fixtures]
    print(json.dumps(results, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main(sys.argv)
