"""Finite synthetic topology/subgoal scorer construction for Issue #2988."""
from collections import deque
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
GRAPH = {
    "nodes": {
        "start": [0, 0], "north": [0, 5], "east": [4, 5],
        "approach": [4, 0], "exit": [5, 0],
        "loop1": [-1, 0], "loop2": [-1, 1], "wrong": [0, -1],
    },
    "edges": [["start", "north"], ["north", "east"],
              ["east", "approach"], ["approach", "exit"],
              ["start", "loop1"], ["loop1", "loop2"],
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


def canonical_sha(value):
    data = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(data).hexdigest()


def distances(graph):
    rev = {n: [] for n in graph["nodes"]}
    for a, b in graph["edges"]:
        rev[b].append(a)
    result = {graph["goal"]: 0}
    todo = deque([graph["goal"]])
    while todo:
        n = todo.popleft()
        for p in rev[n]:
            if p not in result:
                result[p] = result[n] + 1
                todo.append(p)
    return result


def euclidean(graph, a, b):
    x1, y1 = graph["nodes"][a]
    x2, y2 = graph["nodes"][b]
    return ((x1-x2)**2 + (y1-y2)**2) ** 0.5


def score(graph, trace):
    dist = distances(graph)
    rows = []
    prev = None
    for node in trace:
        if node not in graph["nodes"] or node not in dist:
            state = "UNKNOWN"
            route_delta = None
            euclidean_delta = None
        elif prev is None:
            state = "NO_BASELINE"
            route_delta = None
            euclidean_delta = None
        else:
            route_delta = dist[prev] - dist[node]
            euclidean_delta = euclidean(graph, prev, graph["goal"]) - euclidean(graph, node, graph["goal"])
            state = "USEFUL_PROGRESS" if route_delta > 0 else (
                "REGRESSION" if route_delta < 0 else "NO_ROUTE_PROGRESS")
        rows.append({"node": node, "route_progress_delta": route_delta,
                     "euclidean_progress_delta": euclidean_delta, "class": state,
                     "subgoal_reached": node in graph["subgoals"]})
        prev = node if node in graph["nodes"] and node in dist else None
    return rows


def main():
    result = {"schema": "issue2988-topology-construction-v1",
              "graph_sha256": canonical_sha(GRAPH),
              "trace_deck_sha256": canonical_sha(TRACES),
              "cases": {name: score(GRAPH, trace) for name, trace in TRACES.items()},
              "scope": "synthetic method construction only; no MAP01 or runtime evidence"}
    (ROOT / "raw.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({name: [r["class"] for r in rows]
                      for name, rows in result["cases"].items()}, indent=2))


if __name__ == "__main__":
    main()
