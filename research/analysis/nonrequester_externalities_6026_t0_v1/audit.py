"""Independent raw-fixture audit; intentionally recomputes rather than imports candidate."""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path


def audit(f, result):
    ev = f["events"]
    check_counts = Counter()
    def require(condition, name):
        check_counts[name] += 1
        if not condition:
            raise AssertionError(name)

    require(len({x["id"] for x in ev}) == len(ev), "unique_event_ids")
    require(set(result["event_ids"]) == {x["id"] for x in ev}, "event_omission_addition")
    effects = [x for x in ev if x["kind"] == "task_effect"]
    expected_assignments = {(t,r) for t in f["offered_tasks"] for r in f["routes"]}
    observed_assignments = [(x["task"],x["route"]) for x in effects]
    require(len(observed_assignments) == len(expected_assignments) and set(observed_assignments) == expected_assignments, "assigned_task_route_coverage_and_uniqueness")
    expected = {route:{p:{"task_effect_minutes":0,"delivered_interruptions":0,"active_minutes":0,"unsolicited":0,"cleanup_minutes":0,"no_response":0,"suppressed":0,"maximum_burst_events":0,"maximum_burst_minutes":0} for p in f["principals"]} for route in f["routes"]}
    status_counts = defaultdict(int)
    burst_groups = defaultdict(list)
    for x in ev:
        require(x["recipient"] in f["principals"] and x["route"] in f["routes"], "known_recipient_route")
        row = expected[x["route"]][x["recipient"]]
        status_counts[x["status"]] += 1
        if x["kind"] == "task_effect" and x["status"] == "verified": row["task_effect_minutes"] += x["active_minutes"]
        if x["status"] in ("delivered", "performed"):
            if x["kind"] != "task_effect": row["delivered_interruptions"] += 1
            row["active_minutes"] += x["active_minutes"]
            if x["kind"] == "cleanup": row["cleanup_minutes"] += x["active_minutes"]
            if x["kind"] in ("status_ping","deferrable_alert","review_request") and not x.get("scheduled",False): row["unsolicited"] += 1
        if x["status"] == "no_response": row["no_response"] += 1
        if x["status"] == "suppressed": row["suppressed"] += 1
        if x["kind"] != "task_effect" and x["status"] in ("delivered","performed"):
            require(bool(x.get("burst_id")), "delivered_event_has_burst_id")
            burst_groups[(x["route"],x["recipient"],x["burst_id"])].append(x)
    for (route,principal,_),group in burst_groups.items():
        row=expected[route][principal]
        row["maximum_burst_events"]=max(row["maximum_burst_events"],len(group))
        row["maximum_burst_minutes"]=max(row["maximum_burst_minutes"],sum(x["active_minutes"] for x in group))
    require(result["assigned_tasks"] == len(f["offered_tasks"]), "assigned_task_count")
    require(result["by_route_and_principal"] == expected, "route_principal_vector")
    require(dict(sorted(status_counts.items())) == f["expected_status_counts"], "fixture_status_inventory")
    require(result["event_status_counts"] == dict(sorted(status_counts.items())), "event_status_output")
    require(result["logged_event_count"] == len(ev), "logged_event_count")
    require({r:expected[r]["requester"]["task_effect_minutes"] for r in f["routes"]} == {"plain":28,"fast":14}, "requester_route_task_effect_minutes")
    require(result["requester_only_fast_gain_minutes"] == 14, "requester_only_contrast")
    require(result["collaborator_burden_minutes_by_route"] == {"plain":1,"fast":17}, "collaborator_route_burden")
    require(expected["fast"]["collab-b"]["maximum_burst_events"] == 3, "deferrable_alert_burst_count")
    require(expected["fast"]["collab-a"]["maximum_burst_events"] == 2, "redundant_ping_burst_count")
    require(expected["fast"]["collab-b"]["no_response"] == 1, "raw_nonresponse_retained")
    require(result["by_route_and_principal"]["fast"]["collab-b"]["no_response"] == 1, "candidate_nonresponse_retained")
    require(any(x["status"] == "suppressed" for x in ev), "suppressed_event_retained")
    return {"status":"PASS_METHOD_SCOPED","checks":sum(check_counts.values()),"check_counts":dict(sorted(check_counts.items())),"claims_excluded":["human attention cost","real notification effect","joint welfare"]}


if __name__ == "__main__":
    f=json.loads(Path(sys.argv[1]).read_text()); r=json.loads(Path(sys.argv[2]).read_text())
    print(json.dumps(audit(f,r), sort_keys=True, indent=2))
