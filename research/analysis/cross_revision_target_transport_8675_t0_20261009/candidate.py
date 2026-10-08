"""Deterministic finite graph-matching comparison for Issue #8675 T0."""

from __future__ import annotations

import itertools
import json
import math
import sys

MAX_COST = 0.12
TEMPERATURE = 0.05
MIN_TARGET_PROBABILITY = 0.95
MIN_TARGET_MARGIN = 0.90


def feature(n):
    return n["role"], n["label"], n["actionable"]


def relation_graph(graph):
    by_id = {n["id"]: n for n in graph["nodes"]}
    parent = {child: par for par, child in graph["edges"]}
    children = {node_id: [] for node_id in by_id}
    for par, child in graph["edges"]:
        children[par].append(child)

    def effective_parent(node_id):
        par = parent.get(node_id)
        while par is not None and by_id[par]["role"] == "container" and len(children[par]) == 1:
            par = parent.get(par)
        return par

    parent = {node_id: effective_parent(node_id) for node_id in by_id}

    def ancestors(node_id):
        out = []
        while node_id in parent:
            node_id = parent[node_id]
            out.append(node_id)
        return out

    anc = {node_id: ancestors(node_id) for node_id in by_id}

    def relation(a, b):
        if a in anc[b]:
            return "ancestor"
        if b in anc[a]:
            return "descendant"
        if parent.get(a) is not None and parent.get(a) == parent.get(b):
            return "same_parent"
        return "separate"

    return by_id, relation


def exact_id_path(source, current, target_id):
    source_nodes = {n["id"]: n for n in source["nodes"]}
    wanted = source_nodes[target_id]
    hits = [n for n in current["nodes"] if n["id"] == target_id and n["path"] == wanted["path"]]
    return hits[0]["id"] if len(hits) == 1 else None


def role_label(source, current, target_id):
    wanted = feature(next(n for n in source["nodes"] if n["id"] == target_id))
    hits = [n for n in current["nodes"] if feature(n) == wanted]
    return hits[0]["id"] if len(hits) == 1 else None


def relational(source, current, target_id):
    src, src_rel = relation_graph(source)
    cur, cur_rel = relation_graph(current)
    source_ids = tuple(sorted(src))
    current_ids = tuple(sorted(cur))
    n = len(source_ids)
    scored = []
    for assigned in itertools.permutations(current_ids, n):
        mapping = dict(zip(source_ids, assigned))
        feature_cost = sum(feature(src[s]) != feature(cur[mapping[s]]) for s in source_ids) / n
        pairs = [(a, b) for i, a in enumerate(source_ids) for b in source_ids[i + 1:]]
        relation_cost = sum(src_rel(a, b) != cur_rel(mapping[a], mapping[b]) for a, b in pairs) / len(pairs)
        cost = 0.5 * feature_cost + 0.5 * relation_cost
        scored.append((cost, mapping[target_id]))
    best_cost = min(cost for cost, _ in scored)
    weights = [(math.exp(-(cost - best_cost) / TEMPERATURE), target) for cost, target in scored]
    total_weight = sum(weight for weight, _ in weights)
    marginals = {}
    for weight, target in weights:
        marginals[target] = marginals.get(target, 0.0) + weight / total_weight
    target_scores = sorted(((probability, target) for target, probability in marginals.items()), reverse=True)
    top_probability, top_target = target_scores[0]
    margin = top_probability - target_scores[1][0] if len(target_scores) > 1 else 1.0
    if best_cost > MAX_COST or top_probability < MIN_TARGET_PROBABILITY or margin < MIN_TARGET_MARGIN:
        return None
    return top_target


def evaluate(case):
    inp = case["input"]
    policies = {
        "ID_PATH": exact_id_path(inp["source_graph"], inp["current_graph"], inp["source_target_id"]),
        "ROLE_LABEL": role_label(inp["source_graph"], inp["current_graph"], inp["source_target_id"]),
        "RELATIONAL": relational(inp["source_graph"], inp["current_graph"], inp["source_target_id"]),
    }
    return {"case_id": case["case_id"], "split": case["split"], "family": case["family"],
            "predictions": policies}


if __name__ == "__main__":
    design = json.load(open(sys.argv[1], encoding="utf-8"))
    json.dump({"schema": "issue-8675-candidate-output-v1",
               "rows": [evaluate(case) for case in design["cases"]]},
              sys.stdout, sort_keys=True, separators=(",", ":"))
    sys.stdout.write("\n")
