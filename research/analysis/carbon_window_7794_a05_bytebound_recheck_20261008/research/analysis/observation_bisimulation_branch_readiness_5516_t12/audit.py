"""Independent raw-only LTS audit; does not import the candidate."""

import json
import sys


def trace_set(graph, initial):
    seen = {()}
    todo = [(initial, ())]
    visited = set()
    while todo:
        state, word = todo.pop()
        if (state, word) in visited:
            continue
        visited.add((state, word))
        for label, targets in graph.get(state, {}).items():
            for target in targets:
                extended = word + (label,)
                seen.add(extended)
                todo.append((target, extended))
    return seen


def relation(left, right):
    rel = {(x, y) for x in left for y in right}
    while True:
        rejected = set()
        for x, y in rel:
            for label, destinations in left[x].items():
                for destination in destinations:
                    if not any(
                        (destination, candidate) in rel
                        for candidate in right[y].get(label, ())
                    ):
                        rejected.add((x, y))
            for label, destinations in right[y].items():
                for destination in destinations:
                    if not any(
                        (candidate, destination) in rel
                        for candidate in left[x].get(label, ())
                    ):
                        rejected.add((x, y))
        if not rejected:
            return rel
        rel -= rejected


def acyclic(graph):
    visiting, visited = set(), set()

    def visit(state):
        if state in visiting:
            return False
        if state in visited:
            return True
        visiting.add(state)
        for targets in graph[state].values():
            for target in targets:
                if not visit(target):
                    return False
        visiting.remove(state)
        visited.add(state)
        return True

    return all(visit(state) for state in graph)


def post_open_witness(left, right, initial_left, initial_right):
    witnesses = []
    for ls in left[initial_left].get("OPEN", ()):
        for rs in right[initial_right].get("OPEN", ()):
            la, ra = set(left[ls]), set(right[rs])
            if la != ra:
                witnesses.append({
                    "left_state": ls,
                    "right_state": rs,
                    "left_only_actions": sorted(la - ra),
                    "right_only_actions": sorted(ra - la),
                })
    return witnesses


EXPECTED = {
    "positive_control": (True, True),
    "branch_readiness_split": (True, False),
    "visible_label_mismatch": (False, False),
}


def audit_rows(rows):
    errors = []
    found = {}
    for index, row in enumerate(rows):
        case_id = row.get("case_id")
        if case_id in found:
            errors.append(f"row {index}: duplicate case")
            continue
        found[case_id] = row
        try:
            left, right = row["left"], row["right"]
            for graph, initial in ((left, row["initial_left"]), (right, row["initial_right"])):
                if initial not in graph:
                    raise ValueError("initial state missing")
                for edges in graph.values():
                    for targets in edges.values():
                        if not isinstance(targets, list) or any(target not in graph for target in targets):
                            raise ValueError("malformed edge target")
                if not acyclic(graph):
                    raise ValueError("cyclic graph outside frozen finite-word model")
            ltr, rtr = trace_set(left, row["initial_left"]), trace_set(right, row["initial_right"])
            trace_equal = ltr == rtr
            bisim = (row["initial_left"], row["initial_right"]) in relation(left, right)
            if row.get("trace_equal") != trace_equal:
                errors.append(f"row {index}: forged trace_equal summary")
            if row.get("bisimilar") != bisim:
                errors.append(f"row {index}: forged bisimilar summary")
            if set(map(tuple, row.get("left_traces", []))) != ltr:
                errors.append(f"row {index}: left trace serialization mismatch")
            if set(map(tuple, row.get("right_traces", []))) != rtr:
                errors.append(f"row {index}: right trace serialization mismatch")
            if (trace_equal, bisim) != EXPECTED.get(case_id):
                errors.append(f"row {index}: case classification {trace_equal, bisim} unexpected")
            if case_id == "branch_readiness_split" and not post_open_witness(left, right, row["initial_left"], row["initial_right"]):
                errors.append(f"row {index}: expected a post-OPEN action-set witness")
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(f"row {index}: invalid graph: {exc}")
    if set(found) != set(EXPECTED):
        errors.append("case inventory mismatch")
    witnesses = post_open_witness(
        found["branch_readiness_split"]["left"],
        found["branch_readiness_split"]["right"],
        found["branch_readiness_split"]["initial_left"],
        found["branch_readiness_split"]["initial_right"],
    ) if "branch_readiness_split" in found else []
    return {"rows": len(rows), "branch_witnesses": witnesses, "errors": errors, "audit": "PASS" if not errors else "FAIL"}


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as handle:
        rows = [json.loads(line) for line in handle if line.strip()]
    print(json.dumps(audit_rows(rows), sort_keys=True, separators=(",", ":")))
