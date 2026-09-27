"""Construction-only probe for effective partial-order audit mutations.

Does not import or rerun the consumed Issue #4889 formal allocation.
"""
import json
from itertools import permutations

START = (-1, 0, -1, -1, -1, 0, 0, 0, 0)


def step(state, event):
    obs, obs_rev, plan, plan_rev, tool, auth, auth_gen, clock, lease = state
    out = "APPLIED"
    if event == "OPEN":
        auth, auth_gen, lease, out = 1, min(2, auth_gen + 1), min(2, clock + 1), "OPENED"
    elif event == "CLOSE":
        auth, auth_gen, lease, out = 0, min(2, auth_gen + 1), clock, "CLOSED"
    else:
        raise ValueError(event)
    return (obs, obs_rev, plan, plan_rev, tool, auth, auth_gen, clock, lease), out


def trace(events, order):
    state = START
    outputs = {}
    for index in order:
        state, outputs[str(index)] = step(state, events[index])
    return {"events": list(events), "dependent_edges": [[0, 1]], "edge_count": 1,
            "total_order_edges": 1, "linearizations": 1, "mismatches": 0,
            "first_mismatch": None, "final_state": list(state), "event_outputs": outputs}


def validator(row, expected):
    return row == expected


def main():
    events = ("OPEN", "CLOSE")
    expected = trace(events, (0, 1))
    mutations = {
        "events": lambda r: r.update(events=["CLOSE", "OPEN"]),
        "edges": lambda r: r.update(dependent_edges=[]),
        "edge_count": lambda r: r.update(edge_count=0),
        "linearizations": lambda r: r.update(linearizations=0),
        "mismatches": lambda r: r.update(mismatches=1),
        "first_mismatch": lambda r: r.update(first_mismatch=[1, 0]),
        "final_state": lambda r: r.update(final_state=list(START)),
        "event_outputs": lambda r: r.update(event_outputs={"0": "CLOSED", "1": "OPENED"}),
    }
    controls = []
    for name, mutate in mutations.items():
        changed = json.loads(json.dumps(expected))
        mutate(changed)
        effective = changed != expected
        rejected = not validator(changed, expected)
        controls.append({"name": name, "mutation_effective": effective, "rejected": rejected})
    control_reference = trace(events, (0, 1))
    divergences = sum(trace(events, order) != control_reference for order in permutations((0, 1)))
    result = {"classification": "CONSTRUCTION_ONLY_PASS" if all(x["mutation_effective"] and x["rejected"] for x in controls) and divergences == 1 else "CONSTRUCTION_FAIL",
              "lineage": "Issue #4889 / PR #4892; consumed allocation not rerun",
              "formal_rows": 0, "formal_claim": False, "controls": controls,
              "effective_controls": sum(x["mutation_effective"] for x in controls),
              "rejected_controls": sum(x["rejected"] for x in controls),
              "total_controls": len(controls), "open_close_omitted_edge_divergences": divergences}
    print(json.dumps(result, sort_keys=True))
    if result["classification"] != "CONSTRUCTION_ONLY_PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
