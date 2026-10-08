#!/usr/bin/env python3
"""Pending-aware finite-fixture route card. Reads visible data only."""
import json
import sys
from fractions import Fraction


def route_bounds(attempts):
    n = len(attempts)
    successes = sum(a["effect_status"] == "VERIFIED_SUCCESS" for a in attempts)
    failures = sum(a["effect_status"] == "VERIFIED_FAILURE" for a in attempts)
    pending = sum(a["effect_status"] == "PENDING" for a in attempts)
    return Fraction(successes, n), Fraction(successes + pending, n), successes, failures, pending


def decide(case):
    if case["attribution"] != "identified":
        return {"classification": "NONIDENTIFIABLE", "bounds": {}}
    routes = {}
    for attempt in case["attempts"]:
        if attempt["eligible"]:
            routes.setdefault(attempt["route"], []).append(attempt)
    stats = {route: route_bounds(attempts) for route, attempts in routes.items()}
    # Unknown/outcome-dependent censoring invalidates route comparisons even if
    # the attribution label alone is identified.
    if case["censor_model"] not in {"none", "random_independent_of_outcome_known_window", "known_window_still_open"}:
        return {"classification": "NONIDENTIFIABLE", "bounds": {}}
    bounds = {route: {"lower": str(v[0]), "upper": str(v[1]), "n": len(routes[route])} for route, v in stats.items()}
    if not stats or all(v[4] == len(routes[r]) for r, v in stats.items()):
        return {"classification": "NO_RANKING", "bounds": bounds}
    names = list(stats)
    if len(names) == 2 and stats[names[0]][0] == stats[names[1]][0] and stats[names[0]][1] == stats[names[1]][1]:
        return {"classification": "NO_PREFERENCE", "bounds": bounds}
    # Select only with strict, non-overlapping identified bounds. In a declared
    # noninformative censoring case, a complete-case comparator is not used.
    winners = [r for r in names if all(r == q or stats[r][0] > stats[q][1] for q in names)]
    if len(winners) == 1:
        return {"classification": "SELECT:" + winners[0], "bounds": bounds}
    if case["censor_model"] == "known_window_still_open":
        return {"classification": "NO_RANKING", "bounds": bounds}
    return {"classification": "NO_RANKING", "bounds": bounds}


def main(source="/input/visible.json", destination="/output/candidate.json"):
    with open(source, encoding="utf-8") as f:
        visible = json.load(f)
    result = {"schema": "pending-route-candidate-v1", "checkpoint": visible["update_time"], "cases": {}}
    for case in visible["cases"]:
        result["cases"][case["case_id"]] = decide(case)
    with open(destination, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, sort_keys=True)
        f.write("\n")


if __name__ == "__main__":
    main(*(sys.argv[1:3]))
