"""Bounded-horizon supervisor synthesis over the public finite event graphs."""
import json
import sys


def synthesize(case, cap):
    edges = case["edges"]
    goals = set(case["goal_states"])
    states = {case["start"]}
    for edge in edges:
        states.update((edge["source"], edge["target"]))

    # Winning[h] contains states from which the controller can force a
    # certified goal in at most h transitions with no fairness assumption.
    winning = [set(goals)]
    for horizon in range(1, cap + 1):
        previous = winning[horizon - 1]
        current = set(goals)
        for state in states - goals:
            outgoing_u = [e for e in edges if e["source"] == state and e["kind"] == "U"]
            if any(not e["safe"] or not e["evidence_available"] or e["target"] not in previous
                   for e in outgoing_u):
                continue
            eligible_c = [e for e in edges if e["source"] == state and e["kind"] == "C"
                          and e["safe"] and e["evidence_available"] and e["target"] in previous]
            if outgoing_u or eligible_c:
                current.add(state)
        winning.append(current)

    bound = next((h for h, states_at_h in enumerate(winning) if case["start"] in states_at_h), None)
    if bound is None:
        return {
            "status": "SAFE_YIELD",
            "completion_claim": False,
            "app_actions": [],
            "policy_layers": [],
            "bound": None,
            "nonblocking_baseline": nonblocking(case),
        }

    layers = []
    for horizon in range(1, bound + 1):
        previous = winning[horizon - 1]
        policy = {}
        for state in sorted(winning[horizon] - goals):
            selected = [e["id"] for e in edges if e["source"] == state and e["kind"] == "U"]
            selected.extend(e["id"] for e in edges if e["source"] == state and e["kind"] == "C"
                            and e["safe"] and e["evidence_available"] and e["target"] in previous)
            policy[state] = sorted(selected)
        layers.append({"remaining": horizon, "allowed_edges": policy})
    return {
        "status": "POLICY_PROPOSED",
        "completion_claim": False,
        "app_actions": [],
        "policy_layers": layers,
        "bound": bound,
        "nonblocking_baseline": nonblocking(case),
    }


def nonblocking(case):
    edges = [e for e in case["edges"] if e["safe"] and e["evidence_available"]]
    reachable, stack = set(), [case["start"]]
    while stack:
        state = stack.pop()
        if state in reachable:
            continue
        reachable.add(state)
        stack.extend(e["target"] for e in edges if e["source"] == state)
    coreachable = set(case["goal_states"])
    changed = True
    while changed:
        changed = False
        for edge in edges:
            if edge["target"] in coreachable and edge["source"] not in coreachable:
                coreachable.add(edge["source"])
                changed = True
    return reachable <= coreachable


def run(public):
    return {
        "allocation": public["allocation"],
        "cases": {case["id"]: synthesize(case, public["max_horizon"])
                  for case in public["cases"]},
    }


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as stream:
        print(json.dumps(run(json.load(stream)), sort_keys=True, separators=(",", ":")))
