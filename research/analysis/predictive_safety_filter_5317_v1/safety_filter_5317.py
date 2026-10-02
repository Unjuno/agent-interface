"""Finite-state safety-filter discriminator for Issue #5317."""

from collections import deque


POLICIES = ("POSTHOC_VERIFY", "ONE_STEP_FILTER", "HORIZON_FILTER",
            "VIABILITY_FILTER", "UNKNOWN_FAIL_CLOSED")


def _successors(graph, state, action):
    return graph.get((state, action))


def _has_recovery(graph, state, goals, forbidden, max_depth=8):
    if state in goals:
        return True
    seen = {state}
    q = deque([(state, 0)])
    actions = {a for (_, a) in graph}
    while q:
        current, depth = q.popleft()
        if depth >= max_depth:
            continue
        for action in actions:
            for nxt in _successors(graph, current, action) or ():
                if nxt in forbidden:
                    continue
                if nxt in goals:
                    return True
                if nxt not in seen:
                    seen.add(nxt)
                    q.append((nxt, depth + 1))
    return False


def _prefix_states(graph, initial, actions):
    states = {initial}
    for action in actions:
        next_states = set()
        for state in states:
            successors = _successors(graph, state, action)
            if not successors:
                return None
            next_states.update(successors)
        states = next_states
    return states


def decide(case, policy, horizon=2):
    graph = case["model"]
    initial = case["initial"]
    actions = case["plan"]
    bad = set(case["forbidden"])
    quality = case["model_quality"]
    if policy == "POSTHOC_VERIFY":
        return True, "EXECUTE_THEN_CHECK"
    if quality in ("stale", "missing"):
        return False, "UNKNOWN_REACHABILITY"
    if policy == "ONE_STEP_FILTER":
        if not actions:
            return True, "EMPTY_PREFIX"
        successors = _successors(graph, initial, actions[0])
        if not successors or any(s in bad for s in successors):
            return False, "BLOCKED_UNSAFE_OR_UNKNOWN_NEXT"
        return True, "ONE_STEP_SAFE"
    if policy == "HORIZON_FILTER":
        successors = _prefix_states(graph, initial, actions[:horizon])
        if successors is None:
            return False, "UNKNOWN_REACHABILITY"
        if any(s in bad for s in successors):
            return False, "BLOCKED_UNSAFE_PREFIX"
        return True, "HORIZON_SAFE"
    if policy == "VIABILITY_FILTER":
        states = {initial}
        for action in actions:
            next_states = set()
            for state in states:
                successors = _successors(graph, state, action)
                if not successors:
                    return False, "UNKNOWN_REACHABILITY"
                for nxt in successors:
                    exit_states = set(case["goals"]) | set(case["recoveries"])
                    if nxt in bad or not _has_recovery(graph, nxt, exit_states, bad):
                        return False, "BLOCKED_NO_VIABLE_RECOVERY"
                    next_states.add(nxt)
            states = next_states
        return True, "ALL_PREFIXES_VIABLE"
    if policy == "UNKNOWN_FAIL_CLOSED":
        if quality != "exact":
            return False, "MODEL_NOT_EXACT"
        successors = _prefix_states(graph, initial, actions[:horizon])
        if successors is None or any(s in bad for s in successors):
            return False, "UNKNOWN_OR_UNSAFE"
        return True, "KNOWN_SAFE_WITHIN_HORIZON"
    raise ValueError(policy)


def execute_truth(case):
    states = {case["initial"]}
    unsafe = False
    for action in case["plan"]:
        next_states = set()
        for state in states:
            successors = _successors(case["truth"], state, action)
            if successors is None:
                next_states.add("UNKNOWN")
            else:
                next_states.update(successors)
        states = next_states
        if states & set(case["forbidden"]):
            unsafe = True
    goals = set(case["goals"])
    recoveries = set(case["recoveries"])
    stranded = any(s not in goals | recoveries and not _has_recovery(case["truth"], s, goals | recoveries,
                                                                        set(case["forbidden"]))
                   for s in states)
    return {"terminal_states": sorted(states), "unsafe_prefix": unsafe,
            "goal_reached": bool(states & goals), "stranded": stranded}


def run_case(case, policy):
    admitted, reason = decide(case, policy)
    truth = execute_truth(case) if admitted or policy == "POSTHOC_VERIFY" else None
    return {"admitted": admitted, "reason": reason,
            "unsafe_prefix": bool(truth and truth["unsafe_prefix"]),
            "goal_reached": bool(truth and truth["goal_reached"]),
            "stranded": bool(truth and truth["stranded"]),
            "authority_created": False, "effect_claim_created": False}
