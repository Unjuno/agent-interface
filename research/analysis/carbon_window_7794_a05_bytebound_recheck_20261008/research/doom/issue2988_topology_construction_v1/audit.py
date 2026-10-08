"""Independent, fail-closed audit of the retained synthetic result."""
from collections import deque
import copy
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
GRAPH = {
    "nodes": {"start": [0, 0], "north": [0, 5], "east": [4, 5],
              "approach": [4, 0], "exit": [5, 0], "loop1": [-1, 0],
              "loop2": [-1, 1], "wrong": [0, -1]},
    "edges": [["start", "north"], ["north", "east"], ["east", "approach"],
              ["approach", "exit"], ["start", "loop1"], ["loop1", "loop2"],
              ["loop2", "loop1"], ["loop1", "north"], ["loop2", "north"],
              ["start", "wrong"], ["wrong", "start"]],
    "goal": "exit", "subgoals": ["approach", "exit"],
}
TRACES = {
    "detour_progress": ["start", "north", "east", "approach", "exit"],
    "coverage_only": ["start", "loop1", "loop2", "loop1"],
    "wrong_direction": ["start", "wrong"],
    "unknown_state": ["start", "unmapped"],
}
EXPECTED_GRAPH_SHA = "6b785ce2db15daca490906000debf8ef731ecee67a77b9819be31737ea7b59fc"
EXPECTED_TRACE_SHA = "fc3084812942ec058bdb38f62744fe803c496f380887c88f830e7e7e9c2a1416"
EXPECTED = {
    "detour_progress": ["NO_BASELINE", "USEFUL_PROGRESS", "USEFUL_PROGRESS",
                         "USEFUL_PROGRESS", "USEFUL_PROGRESS"],
    "coverage_only": ["NO_BASELINE", "NO_ROUTE_PROGRESS", "NO_ROUTE_PROGRESS",
                       "NO_ROUTE_PROGRESS"],
    "wrong_direction": ["NO_BASELINE", "REGRESSION"],
    "unknown_state": ["NO_BASELINE", "UNKNOWN"],
}


def canonical_sha(value):
    data = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(data).hexdigest()


def independently_recompute(graph, trace):
    reverse = {n: [] for n in graph["nodes"]}
    for source, dest in graph["edges"]:
        reverse[dest].append(source)
    distance = {graph["goal"]: 0}
    queue = deque([graph["goal"]])
    while queue:
        node = queue.popleft()
        for predecessor in reverse[node]:
            if predecessor not in distance:
                distance[predecessor] = distance[node] + 1
                queue.append(predecessor)
    rows, previous = [], None
    for node in trace:
        known = node in graph["nodes"] and node in distance
        if not known:
            route_delta = euclidean_delta = None
            classification = "UNKNOWN"
        elif previous is None:
            route_delta = euclidean_delta = None
            classification = "NO_BASELINE"
        else:
            route_delta = distance[previous] - distance[node]
            p, q, target = graph["nodes"][previous], graph["nodes"][node], graph["nodes"][graph["goal"]]
            old_d = math.dist(p, target)
            new_d = math.dist(q, target)
            euclidean_delta = old_d - new_d
            classification = ("USEFUL_PROGRESS" if route_delta > 0 else
                              "REGRESSION" if route_delta < 0 else "NO_ROUTE_PROGRESS")
        rows.append({"node": node, "route_progress_delta": route_delta,
                     "euclidean_progress_delta": euclidean_delta, "class": classification,
                     "subgoal_reached": node in graph["subgoals"]})
        previous = node if known else None
    return rows


def errors_for(raw):
    errors = []
    if raw.get("graph_sha256") != EXPECTED_GRAPH_SHA:
        errors.append("graph identity mismatch")
    if raw.get("trace_deck_sha256") != EXPECTED_TRACE_SHA:
        errors.append("trace deck identity mismatch")
    if set(raw.get("cases", {})) != set(EXPECTED):
        errors.append("case inventory mismatch")
    for name in EXPECTED:
        rows = raw.get("cases", {}).get(name, [])
        if rows != independently_recompute(GRAPH, TRACES[name]):
            errors.append(f"{name}: independent replay mismatch")
        if [r.get("class") for r in rows] != EXPECTED[name]:
            errors.append(f"{name}: class sequence mismatch")
    return errors


def euclidean(a, b):
    return math.dist(a, b)


def main():
    raw = json.loads((ROOT / "raw.json").read_text())
    errors = errors_for(raw)
    detour = raw["cases"]["detour_progress"][1]
    if not (detour["euclidean_progress_delta"] < 0 and detour["route_progress_delta"] > 0):
        errors.append("detour counterexample not separated")
    if raw["cases"]["unknown_state"][-1].get("subgoal_reached") is not False:
        errors.append("unknown observation falsely receives subgoal")
    graph_mutation = copy.deepcopy(raw)
    graph_mutation["graph_sha256"] = "0" * 64
    inventory_mutation = copy.deepcopy(raw)
    inventory_mutation["cases"].pop("coverage_only")
    decision_mutation = copy.deepcopy(raw)
    decision_mutation["cases"]["wrong_direction"][-1]["class"] = "USEFUL_PROGRESS"
    controls = {"graph_identity_mutation_rejected": bool(errors_for(graph_mutation)),
                "omitted_case_rejected": bool(errors_for(inventory_mutation)),
                "decision_mutation_rejected": bool(errors_for(decision_mutation))}
    if not all(controls.values()):
        errors.append("frozen mutation control accepted")
    status = "PASS_CONSTRUCTION_SCOPED" if not errors else "FAIL_CONSTRUCTION"
    audit = {"status": status, "errors": errors,
             "controls": {**controls,
                          "detour_vs_euclidean_disagreement_detected":
                              detour["euclidean_progress_delta"] < 0 < detour["route_progress_delta"],
                          "unknown_not_imputed": raw["cases"]["unknown_state"][-1]["class"] == "UNKNOWN",
                          "independent_replay": not errors_for(raw)},
             "scope": "synthetic graph only; formal Issue #2988 remains untested"}
    (ROOT / "audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    print(json.dumps(audit, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
