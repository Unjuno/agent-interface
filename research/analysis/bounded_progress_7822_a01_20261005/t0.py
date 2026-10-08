"""Finite T0 for Issue #7822: candidate traces plus independently encoded checker."""
import copy
import json

# Candidate-side trace contract. The task-marker oracle is deliberately absent.
CANDIDATE = {
    "wait_cycle": {
        "ordinary": {"decisions": ["wait", "wait", "wait"], "alternate_marker_action": "progress",
                     "claim": "SAFE_NONBLOCKING"},
        "bounded": {"decisions": ["progress"], "claim": "BOUNDED_PROGRESS", "bound": 1},
    },
    "bounded_async": {
        "bounded": {"decisions": ["tick", "tick", "progress"], "claim": "BOUNDED_PROGRESS", "bound": 3},
    },
    "uncontrollable_cycle": {
        "bounded": {"decisions": ["safe_yield"], "claim": "PROGRESS_NOT_GUARANTEEABLE",
                    "marker_path_exists": True, "guaranteed": False},
    },
    "unknown_evidence": {
        "bounded": {"decisions": ["safe_yield"], "claim": "SAFE_YIELD",
                    "marker_evidence": "UNKNOWN", "completion_claim": False},
    },
}

# Checker-side graph is independently encoded: (source, event, target, controllability, safety, marker-evidence).
ORACLE = {
    "wait_cycle": {
        "start": "s", "markers": {"g"},
        "edges": [("s","wait","w","C",True,False), ("w","wait","w","C",True,False),
                  ("s","progress","g","C",True,True), ("w","progress","g","C",True,True),
                  ("s","forbidden","x","C",False,False)],
    },
    "bounded_async": {
        "start": "a0", "markers": {"g"},
        "edges": [("a0","tick","a1","U",True,False), ("a1","tick","ready","U",True,False),
                  ("ready","progress","g","C",True,True)],
    },
    "uncontrollable_cycle": {
        "start": "u", "markers": {"g"},
        "edges": [("u","nature","u","U",True,False), ("u","progress","g","C",True,True)],
    },
    "unknown_evidence": {
        "start": "q", "markers": set(),
        "edges": [("q","attempt","done","C",True,False)],
    },
}

def allowed(case, edge, policy):
    src, event, dst, controllability, safe, evidence = edge
    if not safe:
        return False
    if case == "wait_cycle" and policy == "bounded":
        return event == "progress"
    if case == "unknown_evidence" and policy == "bounded":
        return False
    return True

def graph_metrics(case, policy):
    graph = ORACLE[case]
    start, markers, edges = graph["start"], graph["markers"], graph["edges"]
    active = [e for e in edges if allowed(case, e, policy)]
    adjacency = {}
    for s, ev, t, kind, safe, evidence in active:
        adjacency.setdefault(s, []).append((t, ev, kind, evidence))
    reachable, stack = set(), [start]
    while stack:
        s = stack.pop()
        if s in reachable:
            continue
        reachable.add(s)
        stack.extend(t for t, _, _, _ in adjacency.get(s, []))
    # A state is nonblocking iff some permitted finite path reaches an oracle marker.
    coreachable = set(markers)
    changed = True
    while changed:
        changed = False
        for s, rows in adjacency.items():
            if s not in coreachable and any(t in coreachable for t, _, _, _ in rows):
                coreachable.add(s)
                changed = True
    nonblocking = all(s in coreachable for s in reachable)

    # A reachable directed cycle in the non-marker subgraph is an infinite non-progress run.
    color, cycle = {}, False
    def visit(s):
        nonlocal cycle
        if s in markers:
            return
        color[s] = 1
        for t, _, _, _ in adjacency.get(s, []):
            if t in markers:
                continue
            if color.get(t) == 1:
                cycle = True
            elif color.get(t, 0) == 0:
                visit(t)
        color[s] = 2
    for s in reachable:
        if s not in markers and color.get(s, 0) == 0:
            visit(s)

    # Exact worst-case transition distance; any non-marker cycle/dead end is unbounded.
    memo, visiting = {}, set()
    def worst(s):
        if s in markers:
            return 0
        if s in visiting:
            return None
        if s in memo:
            return memo[s]
        rows = adjacency.get(s, [])
        if not rows:
            memo[s] = None
            return None
        visiting.add(s)
        values = [worst(t) for t, _, _, _ in rows]
        visiting.remove(s)
        memo[s] = None if any(v is None for v in values) else 1 + max(values)
        return memo[s]
    return {"reachable": sorted(reachable), "nonblocking": nonblocking,
            "nonmarker_cycle": cycle, "worst_steps": worst(start),
            "unsafe_enabled": any(not e[4] for e in active),
            "marker_evidence_edges": sum(int(e[5]) for e in active)}

def replay_trace(case, events):
    graph = ORACLE[case]
    state = graph["start"]
    seen_evidence = []
    for event in events:
        matches = [e for e in graph["edges"] if e[0] == state and e[1] == event and e[4]]
        if len(matches) != 1:
            return state, seen_evidence, False
        edge = matches[0]
        state = edge[2]
        seen_evidence.append(bool(edge[5]))
    return state, seen_evidence, True

def audit(raw):
    errors = []
    expected = {
        ("wait_cycle","ordinary"): {"nonblocking": True, "nonmarker_cycle": True, "worst_steps": None},
        ("wait_cycle","bounded"): {"nonblocking": True, "nonmarker_cycle": False, "worst_steps": 1},
        ("bounded_async","bounded"): {"nonblocking": True, "nonmarker_cycle": False, "worst_steps": 3},
        ("uncontrollable_cycle","bounded"): {"nonblocking": True, "nonmarker_cycle": True, "worst_steps": None},
        ("unknown_evidence","bounded"): {"nonblocking": False, "nonmarker_cycle": False, "worst_steps": None},
    }
    for (case, policy), facts in expected.items():
        got = graph_metrics(case, policy)
        for name, value in facts.items():
            if got[name] != value:
                errors.append(f"oracle:{case}:{policy}:{name}")
        if got["unsafe_enabled"]:
            errors.append(f"unsafe:{case}:{policy}")
    if raw.get("wait_cycle", {}).get("ordinary", {}).get("claim") != "SAFE_NONBLOCKING":
        errors.append("ordinary_claim")
    if raw.get("wait_cycle", {}).get("bounded", {}).get("bound") != 1:
        errors.append("positive_bound")
    if raw.get("bounded_async", {}).get("bounded", {}).get("bound") != 3:
        errors.append("async_bound")
    trap = raw.get("uncontrollable_cycle", {}).get("bounded", {})
    if trap.get("claim") != "PROGRESS_NOT_GUARANTEEABLE" or trap.get("guaranteed") is not False:
        errors.append("uncontrollable_claim")
    unknown = raw.get("unknown_evidence", {}).get("bounded", {})
    if unknown.get("claim") != "SAFE_YIELD" or unknown.get("completion_claim") is not False:
        errors.append("unknown_claim")
    if raw.get("controller_observed_markers"):
        errors.append("oracle_leak")
    progress_events = set()
    for graph in ORACLE.values():
        progress_events.update(e[1] for e in graph["edges"] if e[5])
    if any(e not in progress_events for e in raw.get("self_reported_progress_events", [])):
        errors.append("activity_not_progress")
    if raw.get("omitted_uncontrollable_cycle") is True:
        errors.append("uncontrollable_edge_omitted")
    if raw.get("fairness_assumed") is True:
        errors.append("unfrozen_fairness")
    if raw.get("unsafe_enabled") is True:
        errors.append("unsafe_enable")
    traces = [
        ("wait_cycle", raw.get("wait_cycle", {}).get("ordinary", {}).get("decisions", []), "w", False),
        ("wait_cycle", [raw.get("wait_cycle", {}).get("ordinary", {}).get("alternate_marker_action")], "g", True),
        ("wait_cycle", raw.get("wait_cycle", {}).get("bounded", {}).get("decisions", []), "g", True),
        ("bounded_async", raw.get("bounded_async", {}).get("bounded", {}).get("decisions", []), "g", True),
    ]
    for case, events, final_state, has_evidence in traces:
        state, evidence, valid = replay_trace(case, events)
        if not valid or state != final_state or any(evidence) != has_evidence:
            errors.append(f"trace:{case}:{events}")
    return errors

def main():
    raw = copy.deepcopy(CANDIDATE)
    raw["controller_observed_markers"] = []
    raw["self_reported_progress_events"] = []
    baseline = audit(raw)
    mutations = {}
    tests = [
        ("activity_as_progress", lambda x: x.update(self_reported_progress_events=["wait"])),
        ("omit_uncontrollable_cycle", lambda x: x.update(omitted_uncontrollable_cycle=True)),
        ("oracle_leak", lambda x: x.update(controller_observed_markers=["g"])),
        ("assume_fairness", lambda x: x.update(fairness_assumed=True)),
        ("unsafe_enable", lambda x: x.update(unsafe_enabled=True)),
    ]
    for name, mutate in tests:
        changed = copy.deepcopy(raw)
        mutate(changed)
        mutations[name] = bool(audit(changed))
    metrics = {f"{case}:{policy}": graph_metrics(case, policy)
               for case, policy in [("wait_cycle","ordinary"),("wait_cycle","bounded"),
                                    ("bounded_async","bounded"),("uncontrollable_cycle","bounded"),
                                    ("unknown_evidence","bounded")]}
    result = {"raw": raw, "audit_errors": baseline, "mutation_rejected": mutations,
              "metrics": metrics,
              "disposition": "PASS_METHOD_SCOPED" if not baseline and all(mutations.values()) else "FAIL"}
    print(json.dumps(result, sort_keys=True, separators=(",",":")))

if __name__ == "__main__":
    main()
