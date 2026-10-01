"""Method-scoped synthetic accounting candidate for Issue #6026."""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path


def score(fixture):
    events = fixture["events"]
    ids = [e["id"] for e in events]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate_event_id")
    validate_coverage(fixture)
    by_route = {route: {p: {"task_effect_minutes": 0, "delivered_interruptions": 0,
                            "active_minutes": 0, "unsolicited": 0,
                            "cleanup_minutes": 0, "no_response": 0,
                            "suppressed": 0, "maximum_burst_events": 0,
                            "maximum_burst_minutes": 0}
                        for p in fixture["principals"]}
                for route in fixture["routes"]}
    event_status_counts = Counter(e["status"] for e in events)
    burst_groups = defaultdict(list)
    for e in events:
        if e["recipient"] not in fixture["principals"] or e["route"] not in by_route:
            raise ValueError("unknown_recipient")
        row = by_route[e["route"]][e["recipient"]]
        if e["kind"] == "task_effect" and e["status"] == "verified":
            row["task_effect_minutes"] += e["active_minutes"]
        if e["status"] in ("delivered", "performed"):
            if e["kind"] != "task_effect":
                row["delivered_interruptions"] += 1
            row["active_minutes"] += e["active_minutes"]
            if e["kind"] == "cleanup":
                row["cleanup_minutes"] += e["active_minutes"]
            if e["kind"] in ("status_ping", "deferrable_alert", "review_request") and not e.get("scheduled", False):
                row["unsolicited"] += 1
        if e["status"] == "no_response":
            row["no_response"] += 1
        if e["status"] == "suppressed":
            row["suppressed"] += 1
        if e["kind"] != "task_effect" and e["status"] in ("delivered", "performed"):
            if not e.get("burst_id"):
                raise ValueError("missing_burst_id")
            burst_groups[(e["route"],e["recipient"],e["burst_id"])].append(e)
    for (route,recipient,_), grouped in burst_groups.items():
        row=by_route[route][recipient]
        row["maximum_burst_events"] = max(row["maximum_burst_events"],len(grouped))
        row["maximum_burst_minutes"] = max(row["maximum_burst_minutes"],sum(e["active_minutes"] for e in grouped))
    route_task_minutes = {r: by_route[r][fixture["requester"]]["task_effect_minutes"] for r in fixture["routes"]}
    collaborator_burden = {r: sum(by_route[r][p]["active_minutes"] for p in fixture["principals"] if p != fixture["requester"]) for r in fixture["routes"]}
    if any(event_status_counts[s] != n for s, n in fixture["expected_status_counts"].items()):
        raise ValueError("event_status_count")
    return {
        "assigned_tasks": len(fixture["offered_tasks"]),
        "logged_event_count": len(events),
        "event_ids": sorted(ids),
        "by_route_and_principal": by_route,
        "event_status_counts": dict(sorted(event_status_counts.items())),
        "requester_minutes": route_task_minutes,
        "requester_only_fast_gain_minutes": route_task_minutes["plain"] - route_task_minutes["fast"],
        "collaborator_burden_minutes_by_route": collaborator_burden,
        "method_scope": "synthetic accounting only; no human effect measured"
    }


def validate_coverage(fixture):
    expected_assignments = {(t, r) for t in fixture["offered_tasks"] for r in fixture["routes"]}
    observed = [(e["task"], e["route"]) for e in fixture["events"] if e["kind"] == "task_effect"]
    if len(observed) != len(expected_assignments) or expected_assignments != set(observed):
        raise ValueError("task_assignment_coverage")


if __name__ == "__main__":
    data = json.loads(Path(sys.argv[1]).read_text())
    print(json.dumps(score(data), sort_keys=True, indent=2))
