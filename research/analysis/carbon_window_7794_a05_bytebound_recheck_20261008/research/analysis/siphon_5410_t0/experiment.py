#!/usr/bin/env python3
"""Deterministic bounded resource-allocation simulator for Issue #5410 T0."""
import copy
import json

RESOURCES = ("A", "B", "C", "D", "E")
BASE_WORKFLOWS = [
    {"name": "alpha", "actual": ["A", "B"], "declared": ["A", "B"]},
    {"name": "beta", "actual": ["B", "A"], "declared": ["B", "A"]},
    {"name": "gamma", "actual": ["C", "D"], "declared": ["C", "D"]},
    {"name": "delta", "actual": ["E"], "declared": ["E"]},
]
POLICIES = ("NAIVE", "GLOBAL_EXCLUSIVE", "SCC_GUARD", "SAFE_REACHABILITY")


def scenarios():
    result = []
    result.append({"id": "opposed_order_deadlock", "workflows": copy.deepcopy(BASE_WORKFLOWS), "events": [], "leases": {}})
    result.append({"id": "lease_expiry_recovery", "workflows": copy.deepcopy(BASE_WORKFLOWS), "events": [], "leases": {"beta": 2}})
    result.append({"id": "cancellation_release", "workflows": copy.deepcopy(BASE_WORKFLOWS),
                   "events": [{"tick": 1, "kind": "cancel", "workflow": "beta"}], "leases": {}})
    result.append({"id": "authority_revocation_release", "workflows": copy.deepcopy(BASE_WORKFLOWS),
                   "events": [{"tick": 1, "kind": "revoke", "workflow": "alpha"}], "leases": {}})
    hidden = copy.deepcopy(BASE_WORKFLOWS)
    hidden[1]["dependency_complete"] = False
    hidden[1]["declared"] = ["B"]
    result.append({"id": "hidden_dependency", "workflows": hidden, "events": [], "leases": {}})
    backoff = copy.deepcopy(BASE_WORKFLOWS)
    result.append({"id": "retry_backoff", "workflows": backoff, "events": [], "leases": {}, "guard_backoff": 2})
    independent = copy.deepcopy(BASE_WORKFLOWS)
    independent[0]["actual"] = independent[0]["declared"] = ["A"]
    independent[1]["actual"] = independent[1]["declared"] = ["B"]
    result.append({"id": "independent_workflows", "workflows": independent, "events": [], "leases": {}})
    return result


def closes_cycle(edges, source, target):
    stack, seen = [target], set()
    while stack:
        node = stack.pop()
        if node == source:
            return True
        if node not in seen:
            seen.add(node)
            stack.extend(edges.get(node, ()))
    return False


def safe_after_grant(workflows, capacities, candidate_name, candidate_resource):
    """Banker-style finite completion-sequence oracle over the declared max claims."""
    available = dict(capacities)
    for workflow in workflows:
        for resource in workflow["held"]:
            available[resource] -= 1
    available[candidate_resource] -= 1
    active = [w for w in workflows if w["state"] == "pending"]
    needs = {}
    for workflow in active:
        remaining = list(workflow["actual"][workflow["index"]:])
        if workflow["name"] == candidate_name:
            remaining = [r for r in remaining if r != candidate_resource]
        needs[workflow["name"]] = set(remaining)
    work = available.copy()
    unfinished = {w["name"] for w in active}
    while True:
        completable = None
        for workflow in active:
            name = workflow["name"]
            if name in unfinished and all(work.get(resource, 0) >= 1 for resource in needs[name]):
                completable = workflow
                break
        if completable is None:
            break
        name = completable["name"]
        unfinished.remove(name)
        for resource in completable["held"]:
            work[resource] += 1
        if name == candidate_name:
            work[candidate_resource] += 1
    return not unfinished


def simulate(scenario, policy):
    workflows = []
    for row in scenario["workflows"]:
        workflows.append({**copy.deepcopy(row), "state": "pending", "index": 0, "held": [],
                          "plan": sorted(row["actual"]) if policy == "GLOBAL_EXCLUSIVE" else list(row["actual"]),
                          "retry_at": 0, "lease_start": None, "retries": 0})
    by_name = {w["name"]: w for w in workflows}
    events = sorted(copy.deepcopy(scenario["events"]), key=lambda e: e["tick"])
    event_done = set()
    trace = []
    counters = {"guard_cycles": 0, "guard_replans": 0, "oracle_denials": 0,
                "lease_expiries": 0, "unknown_rejections": 0, "cancelled": 0, "revoked": 0}
    capacities = {resource: 1 for resource in RESOURCES}
    owner = {}
    edges_by_tick = {}
    max_tick = 40
    terminal_tick = max_tick

    def release(workflow, tick, kind):
        for resource in workflow["held"]:
            owner.pop(resource, None)
        trace.append({"tick": tick, "event": kind, "workflow": workflow["name"], "released": list(workflow["held"])})
        workflow["held"].clear()
        workflow["index"] = 0
        workflow["lease_start"] = None

    for tick in range(max_tick):
        progressed = False
        edges_by_tick = {}
        for event_index, event in enumerate(events):
            if event["tick"] != tick or event_index in event_done:
                continue
            event_done.add(event_index)
            workflow = by_name[event["workflow"]]
            if workflow["state"] == "pending":
                release(workflow, tick, event["kind"])
                workflow["state"] = "cancelled" if event["kind"] == "cancel" else "revoked"
                counters["cancelled" if event["kind"] == "cancel" else "revoked"] += 1
                progressed = True

        for workflow in workflows:
            limit = scenario["leases"].get(workflow["name"])
            if (workflow["state"] == "pending" and workflow["held"] and limit is not None
                    and tick - workflow["lease_start"] >= limit):
                release(workflow, tick, "lease_expire")
                workflow["retries"] += 1
                workflow["retry_at"] = tick + 1
                counters["lease_expiries"] += 1
                progressed = True

        for workflow in workflows:
            if workflow["state"] != "pending" or tick < workflow["retry_at"]:
                continue
            if policy in ("SCC_GUARD", "GLOBAL_EXCLUSIVE") and not workflow.get("dependency_complete", True):
                workflow["state"] = "unknown"
                counters["unknown_rejections"] += 1
                trace.append({"tick": tick, "event": "unknown_incomplete_dependency", "workflow": workflow["name"]})
                progressed = True
                continue
            if workflow["index"] >= len(workflow["plan"]):
                release(workflow, tick, "complete")
                workflow["state"] = "done"
                progressed = True
                continue
            if policy == "GLOBAL_EXCLUSIVE" and any(
                other["name"] != workflow["name"] and other["held"] for other in workflows
            ):
                continue
            resource = workflow["plan"][workflow["index"]]
            if resource not in owner:
                if policy == "SAFE_REACHABILITY" and not safe_after_grant(workflows, capacities, workflow["name"], resource):
                    counters["oracle_denials"] += 1
                    trace.append({"tick": tick, "event": "oracle_hold_unsafe", "workflow": workflow["name"], "resource": resource})
                    continue
                owner[resource] = workflow["name"]
                workflow["held"].append(resource)
                workflow["index"] += 1
                if workflow["lease_start"] is None:
                    workflow["lease_start"] = tick
                trace.append({"tick": tick, "event": "acquire", "workflow": workflow["name"], "resource": resource})
                progressed = True
            else:
                holder = owner[resource]
                edges_by_tick.setdefault(workflow["name"], set()).add(holder)
                trace.append({"tick": tick, "event": "wait", "workflow": workflow["name"], "resource": resource, "holder": holder})
                if policy == "SCC_GUARD" and closes_cycle(edges_by_tick, workflow["name"], holder):
                    counters["guard_cycles"] += 1
                    counters["guard_replans"] += 1
                    release(workflow, tick, "scc_guard_rollback_replan")
                    workflow["plan"] = sorted(workflow["actual"])
                    workflow["retry_at"] = tick + scenario.get("guard_backoff", 1)
                    workflow["retries"] += 1
                    progressed = True

        if all(w["state"] != "pending" for w in workflows):
            terminal_tick = tick + 1
            break
        if not progressed:
            future = any(event_index not in event_done and event["tick"] > tick
                         for event_index, event in enumerate(events))
            future = future or any(
                w["state"] == "pending" and w["held"] and scenario["leases"].get(w["name"]) is not None
                for w in workflows
            ) or any(w["state"] == "pending" and w["retry_at"] > tick for w in workflows)
            if not future:
                terminal_tick = tick + 1
                break

    pending = [w for w in workflows if w["state"] == "pending"]
    unrecovered = len(pending) > 0
    for workflow in pending:
        workflow["state"] = "deadlocked"
    return {
        "scenario": scenario["id"], "policy": policy,
        "terminal_statuses": {w["name"]: w["state"] for w in workflows},
        "completed_workflows": sum(w["state"] == "done" for w in workflows),
        "unrecovered_deadlock": unrecovered,
        "makespan_ticks": terminal_tick,
        "false_rejected_workflows": counters["unknown_rejections"],
        "counters": counters, "trace": trace,
    }


def main():
    rows = []
    for scenario in scenarios():
        for policy in POLICIES:
            rows.append(simulate(scenario, policy))
    print(json.dumps({
        "experiment": "issue-5410-siphon-t0-bounded-resource-simulator",
        "resources": list(RESOURCES),
        "capacity_per_resource": 1,
        "policies": list(POLICIES),
        "scenario_count": len(scenarios()),
        "runs": rows,
        "scope": "deterministic symbolic model; traces do not model real GUI/tool side effects",
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
