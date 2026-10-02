#!/usr/bin/env python3
"""Independent raw-only auditor; does not import candidate.py."""
import argparse
import copy
import json
from pathlib import Path


EXPECTED_EQUAL = [{"id": f"E{i}", "onset": i * 10, "expiry": (i + 1) * 10} for i in range(4)]
EXPECTED_VARIED = [{"id": f"S{i:02}", "onset": i, "expiry": i + 1} for i in range(10)] + [
    {"id": "L", "onset": 10, "expiry": 100}
]
SPEC = {
    "equal_duration": {
        "onset_schedule_present": True, "clock_aligned": True, "opportunities": EXPECTED_EQUAL,
        "routes": {
            "half": (["E0", "E2"], [[0, 10], [20, 30]]),
            "all": (["E0", "E1", "E2", "E3"], [[0, 40]]),
        },
    },
    "heterogeneous_duration": {
        "onset_schedule_present": True, "clock_aligned": True, "opportunities": EXPECTED_VARIED,
        "routes": {
            "long_only": (["L"], [[10, 100]]),
            "shorts_only": ([f"S{i:02}" for i in range(10)], [[0, 10]]),
        },
    },
    "no_onset_oracle": {
        "onset_schedule_present": False, "clock_aligned": False, "opportunities": None,
        "routes": {
            "apparent_fast": ([], [[0, 5]]),
            "apparent_slow": ([], [[5, 10]]),
        },
    },
}


def union_measure(intervals):
    pairs = sorted((int(a), int(b)) for a, b in intervals if int(a) < int(b))
    total = 0
    right = None
    for left, end in pairs:
        if right is None or left > right:
            total += end - left
            right = end
        elif end > right:
            total += end - right
            right = end
    return total


def independent_summary(has_schedule, aligned, opportunities, effect_ids, intervals):
    if not has_schedule or not aligned:
        return {"status": "HOLD_NO_ELIGIBLE_ONSET_CLOCK", "event_coverage": None, "time_coverage": None}
    eligible = {item["id"] for item in opportunities}
    hits = eligible.intersection(effect_ids)
    windows = [(o["onset"], o["expiry"]) for o in opportunities]
    denominator = union_measure(windows)
    covered = union_measure(
        [(max(a, c), min(b, d)) for a, b in windows for c, d in intervals if max(a, c) < min(b, d)]
    )
    return {
        "status": "SCOPED",
        "event_coverage": {"numerator": len(hits), "denominator": len(eligible)},
        "time_coverage": {"numerator": covered, "denominator": denominator},
    }


def audit(document):
    errors = []
    if not isinstance(document, dict) or document.get("schema") != "exogenous-opportunity-event-time-a02-v1":
        return ["schema mismatch"]
    scenarios = document.get("scenarios")
    if not isinstance(scenarios, list) or len(scenarios) != len(SPEC):
        return ["scenario count mismatch"]
    seen = set()
    for row in scenarios:
        cid = row.get("case_id")
        if cid not in SPEC or cid in seen:
            errors.append(f"unknown/duplicate case: {cid}")
            continue
        seen.add(cid)
        expected = SPEC[cid]
        for field in ("onset_schedule_present", "clock_aligned", "opportunities"):
            if row.get(field) != expected[field]:
                errors.append(f"{cid}: {field} mismatch")
        routes = row.get("routes")
        if not isinstance(routes, list) or len(routes) != len(expected["routes"]):
            errors.append(f"{cid}: route count mismatch")
            continue
        route_seen = set()
        for route in routes:
            rid = route.get("route_id")
            if rid not in expected["routes"] or rid in route_seen:
                errors.append(f"{cid}: unknown/duplicate route {rid}")
                continue
            route_seen.add(rid)
            effect_ids, intervals = expected["routes"][rid]
            if route.get("effect_opportunity_ids") != effect_ids:
                errors.append(f"{cid}/{rid}: effect IDs mismatch")
            if route.get("coverage_intervals") != intervals:
                errors.append(f"{cid}/{rid}: coverage intervals mismatch")
            computed = independent_summary(
                expected["onset_schedule_present"], expected["clock_aligned"], expected["opportunities"],
                effect_ids, intervals
            )
            if route.get("claimed_summary") != computed:
                errors.append(f"{cid}/{rid}: claimed summary mismatch")
        if route_seen != set(expected["routes"]):
            errors.append(f"{cid}: route set mismatch")
    if seen != set(SPEC):
        errors.append("case set mismatch")
    return errors


def mutation_results(document):
    outcomes = {}
    mutations = [
        ("omit_short_opportunity", lambda d: d["scenarios"][1]["opportunities"].pop(0)),
        ("alter_duration", lambda d: d["scenarios"][1]["opportunities"][0].update(expiry=2)),
        ("double_count_interval_claim", lambda d: d["scenarios"][1]["routes"][0]["claimed_summary"]["time_coverage"].update(numerator=180)),
        ("invent_missing_onset_schedule", lambda d: d["scenarios"][2].update(onset_schedule_present=True, clock_aligned=True, opportunities=[{"id": "invented", "onset": 0, "expiry": 5}])),
    ]
    for label, edit in mutations:
        changed = copy.deepcopy(document)
        edit(changed)
        outcomes[label] = bool(audit(changed))
    return outcomes


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    source = json.loads(Path(args.candidate).read_text(encoding="utf-8"))
    errors = audit(source)
    mutations = mutation_results(source)
    if not all(mutations.values()):
        errors.append("one or more mutation controls were accepted")
    result = {
        "schema": "exogenous-opportunity-event-time-audit-v1",
        "disposition": "PASS_METHOD_SCOPED" if not errors else "FAIL_AUDIT",
        "errors": errors,
        "scenarios_checked": len(SPEC),
        "routes_checked": sum(len(v["routes"]) for v in SPEC.values()),
        "mutation_rejections": mutations,
        "reconstructed": {
            "equal_half": independent_summary(True, True, EXPECTED_EQUAL, ["E0", "E2"], [[0, 10], [20, 30]]),
            "hetero_long_only": independent_summary(True, True, EXPECTED_VARIED, ["L"], [[10, 100]]),
            "hetero_shorts_only": independent_summary(True, True, EXPECTED_VARIED, [f"S{i:02}" for i in range(10)], [[0, 10]]),
            "no_onset": independent_summary(False, False, None, [], [[0, 5]]),
        },
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if not errors else 1)


if __name__ == "__main__":
    main()
