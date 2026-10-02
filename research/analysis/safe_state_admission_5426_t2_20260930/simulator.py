"""Deterministic policies for the frozen safe-state admission trace suite."""
from collections import Counter, deque
from copy import deepcopy

POLICIES = ("quota", "siphon", "banker", "global_lock")
CAPACITY = (1, 1, 1)


def safe_sequence(available, allocation, claims, statuses):
    work = list(available)
    unfinished = {w for w, s in statuses.items() if s == "active"}
    sequence = []
    while unfinished:
        chosen = None
        for workflow in sorted(unfinished):
            need = [claims[workflow][i] - allocation[workflow][i]
                    for i in range(len(work))]
            if all(need[i] >= 0 and need[i] <= work[i] for i in range(len(work))):
                chosen = workflow
                break
        if chosen is None:
            return None
        work = [work[i] + allocation[chosen][i] for i in range(len(work))]
        unfinished.remove(chosen)
        sequence.append(chosen)
    return sequence


def _cycle(graph):
    visiting, visited = set(), set()

    def visit(node):
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        if any(visit(child) for child in graph.get(node, ())):
            return True
        visiting.remove(node)
        visited.add(node)
        return False

    return any(visit(node) for node in graph)


def _held_total(vector):
    return sum(vector)


def _actual_feasible(available, allocation, actual, statuses):
    """Independent-in-spirit lower-demand comparator used to label false holds."""
    return safe_sequence(available, allocation, actual, statuses) is not None


def run_one(scenario, policy):
    names = sorted(scenario["claims"])
    claims = deepcopy(scenario["claims"])
    original_claims = deepcopy(scenario["claims"])
    actual = deepcopy(scenario["actual"])
    allocation = {w: [0, 0, 0] for w in names}
    status = {w: "active" for w in names}
    available = list(CAPACITY)
    events = []
    pending = deque()
    seen_pending = set()
    generation = [0, 0, 0]
    global_owner = None
    counters = Counter()
    peak_holders = 0

    def holder_ids(resource):
        return [w for w in names if allocation[w][resource] > 0 and status[w] == "active"]

    def wait_graph(extra=None):
        graph = {w: set() for w in names if status[w] == "active"}
        rows = list(pending)
        if extra is not None:
            rows.append(extra)
        for row in rows:
            w, r = row["workflow"], row["resource"]
            if w not in graph:
                continue
            graph[w].update(x for x in holder_ids(r) if x != w)
        return graph

    def release(workflow, reason):
        nonlocal global_owner
        held = allocation[workflow]
        released = list(held)
        available[:] = [available[i] + held[i] for i in range(3)]
        allocation[workflow] = [0, 0, 0]
        if any(p["workflow"] == workflow for p in pending):
            retained = [p for p in pending if p["workflow"] != workflow]
            pending.clear()
            pending.extend(retained)
        if global_owner == workflow:
            global_owner = None
        events.append({"kind": "release", "workflow": workflow,
                       "vector": released, "reason": reason})

    def abort(workflow, reason):
        if status[workflow] != "active":
            return
        release(workflow, reason)
        status[workflow] = "aborted"
        counters["aborts"] += 1
        events.append({"kind": "abort", "workflow": workflow, "reason": reason})

    def complete(workflow, reason):
        nonlocal global_owner
        if status[workflow] != "active":
            return
        status[workflow] = "completed"
        counters["completions"] += 1
        events.append({"kind": "complete", "workflow": workflow, "reason": reason})
        release(workflow, "completion")

    def maybe_complete(workflow):
        if workflow not in finish_requested or status[workflow] != "active":
            return
        if all(allocation[workflow][i] >= actual[workflow][i] for i in range(3)):
            complete(workflow, "actual_demand_satisfied")

    finish_requested = set()

    def grant(row, reason):
        nonlocal global_owner, peak_holders
        w, r = row["workflow"], row["resource"]
        if status[w] != "active" or available[r] < 1:
            return False
        tentative = deepcopy(allocation)
        tentative[w][r] += 1
        remaining = [available[i] - (1 if i == r else 0) for i in range(3)]
        witness = None
        if policy == "banker":
            witness = safe_sequence(remaining, tentative, claims, status)
            if witness is None:
                actual_witness = _actual_feasible(remaining, tentative, actual, status)
                counters["banker_unsafe_holds"] += 1
                if actual_witness:
                    counters["banker_false_holds"] += 1
                events.append({"kind": "hold", "workflow": w, "resource": r,
                               "reason": "no_declared_claim_completion_witness",
                               "actual_completion_witness": actual_witness})
                return False
        allocation[w][r] += 1
        available[r] -= 1
        if policy == "global_lock" and global_owner is None:
            global_owner = w
        if _held_total(allocation[w]) > 0:
            peak_holders = max(peak_holders, sum(_held_total(allocation[x]) > 0 for x in names))
        events.append({"kind": "grant", "workflow": w, "resource": r,
                       "reason": reason, "witness": witness})
        maybe_complete(w)
        return True

    def request(workflow, resource, source="trace"):
        if status[workflow] != "active":
            events.append({"kind": "request_rejected", "workflow": workflow,
                           "resource": resource, "reason": "workflow_not_active"})
            return
        row = {"workflow": workflow, "resource": resource, "source": source}
        if policy == "global_lock" and global_owner not in (None, workflow):
            counters["serialized_waits"] += 1
            key = (workflow, resource)
            if key not in seen_pending:
                pending.append(row)
                seen_pending.add(key)
            events.append({"kind": "hold", "workflow": workflow, "resource": resource,
                           "reason": "global_exclusive_owner"})
            return
        if available[resource] > 0:
            if grant(row, "trace_request"):
                return
            key = (workflow, resource)
            if key not in seen_pending:
                pending.append(row)
                seen_pending.add(key)
            return
        key = (workflow, resource)
        if key not in seen_pending:
            pending.append(row)
            seen_pending.add(key)
        events.append({"kind": "wait", "workflow": workflow, "resource": resource,
                       "reason": "capacity_unavailable"})
        if policy == "siphon" and _cycle(wait_graph()):
            counters["siphon_cycle_aborts"] += 1
            abort(workflow, "reactive_wait_cycle_guard")

    def retry_pending():
        nonlocal global_owner
        changed = True
        while changed:
            changed = False
            for row in list(pending):
                w, r = row["workflow"], row["resource"]
                if status[w] != "active":
                    pending.remove(row)
                    seen_pending.discard((w, r))
                    changed = True
                    break
                if policy == "global_lock" and global_owner not in (None, w):
                    continue
                if available[r] > 0 and grant(row, "pending_retry"):
                    pending.remove(row)
                    seen_pending.discard((w, r))
                    changed = True
                    break

    for ordinal, event in enumerate(scenario["events"]):
        kind = event[0]
        if kind == "request":
            _, workflow, resource = event
            request(workflow, resource)
        elif kind == "finish":
            workflow = event[1]
            finish_requested.add(workflow)
            maybe_complete(workflow)
            events.append({"kind": "finish_requested", "workflow": workflow})
        elif kind == "expand":
            _, workflow, new_claim = event
            if any(new_claim[i] > original_claims[workflow][i] for i in range(3)) and policy == "banker":
                counters["claim_expansion_invalidations"] += 1
                abort(workflow, "declared_maximum_claim_exceeded")
            else:
                claims[workflow] = list(new_claim)
                actual[workflow] = [max(actual[workflow][i], new_claim[i]) for i in range(3)]
                events.append({"kind": "claim_expanded", "workflow": workflow,
                               "new_claim": list(new_claim)})
        elif kind == "expire":
            workflow = event[1]
            counters["expiries"] += 1
            abort(workflow, "lease_expired")
        elif kind == "invalidate":
            resource = event[1]
            generation[resource] += 1
            affected = [w for w in names if allocation[w][resource] > 0]
            events.append({"kind": "shared_fault", "resource": resource,
                           "generation": generation[resource], "affected": affected})
            counters["shared_faults"] += 1
            for workflow in affected:
                abort(workflow, "resource_generation_invalidated")
        else:
            raise ValueError(f"unknown event: {event}")
        retry_pending()

    graph = wait_graph()
    terminal_cycle = _cycle(graph)
    unresolved = [w for w in names if status[w] == "active"]
    counters["terminal_wait_cycle"] = int(terminal_cycle)
    counters["unfinished"] = len(unresolved)
    return {
        "scenario": scenario["id"], "policy": policy,
        "truthful_claims": bool(scenario["truthful"]),
        "status": status, "available": available,
        "allocation": allocation, "resource_generation": generation,
        "metrics": {
            "completed": counters["completions"], "aborted": counters["aborts"],
            "unfinished": counters["unfinished"],
            "unrecovered_deadlocks": counters["terminal_wait_cycle"],
            "siphon_cycle_aborts": counters["siphon_cycle_aborts"],
            "banker_unsafe_holds": counters["banker_unsafe_holds"],
            "banker_false_holds": counters["banker_false_holds"],
            "claim_expansion_invalidations": counters["claim_expansion_invalidations"],
            "expiries": counters["expiries"], "shared_faults": counters["shared_faults"],
            "peak_simultaneous_holders": peak_holders,
        },
        "event_log": events,
        "terminal_wait_graph": {w: sorted(v) for w, v in graph.items()},
    }


def run_suite(scenarios):
    rows = [run_one(scenario, policy)
            for scenario in scenarios for policy in POLICIES]
    return {"schema": "safe-state-admission-t2-raw-v1", "capacity": list(CAPACITY),
            "resources": ["input_authority", "verifier_slot", "observation_slot"],
            "policies": list(POLICIES), "rows": rows}
