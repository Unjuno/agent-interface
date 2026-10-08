"""Independent raw-output reconstruction and gate audit for Issue #8675 T0."""

from __future__ import annotations

import copy
import itertools
import json
import math
import sys

LIMIT_COST = 0.12
SOFT_TEMPERATURE = 0.05
REQUIRED_PROBABILITY = 0.95
REQUIRED_MARGIN = 0.90


def attributes(node):
    return node["role"], node["label"], node["actionable"]


def graph_relations(graph):
    nodes = {node["id"]: node for node in graph["nodes"]}
    parents = {child: parent for parent, child in graph["edges"]}
    children = {item: [] for item in nodes}
    for parent, child in graph["edges"]:
        children[parent].append(child)
    for item in list(parents):
        parent = parents[item]
        while nodes[parent]["role"] == "container" and len(children[parent]) == 1:
            parent = parents.get(parent)
            if parent is None:
                break
        if parent is None:
            parents.pop(item)
        else:
            parents[item] = parent
    ancestor_sets = {}
    for item in nodes:
        chain, cursor = set(), item
        while cursor in parents:
            cursor = parents[cursor]
            chain.add(cursor)
        ancestor_sets[item] = chain

    def kind(left, right):
        if left in ancestor_sets[right]:
            return "ancestor"
        if right in ancestor_sets[left]:
            return "descendant"
        if parents.get(left) is not None and parents.get(left) == parents.get(right):
            return "same_parent"
        return "separate"

    return nodes, kind


def independent_predictions(case):
    data = case["input"]
    old, new, target = data["source_graph"], data["current_graph"], data["source_target_id"]
    old_nodes = {node["id"]: node for node in old["nodes"]}
    target_node = old_nodes[target]
    exact = [node["id"] for node in new["nodes"]
             if node["id"] == target and node["path"] == target_node["path"]]
    attr = [node["id"] for node in new["nodes"] if attributes(node) == attributes(target_node)]
    output = {"ID_PATH": exact[0] if len(exact) == 1 else None,
              "ROLE_LABEL": attr[0] if len(attr) == 1 else None}

    a_nodes, a_relation = graph_relations(old)
    b_nodes, b_relation = graph_relations(new)
    a_ids, b_ids = sorted(a_nodes), sorted(b_nodes)
    pairs = [(x, y) for pos, x in enumerate(a_ids) for y in a_ids[pos + 1:]]
    values = []

    def visit(position, assigned, used):
        if position == len(a_ids):
            correspondence = dict(zip(a_ids, assigned))
            attr_errors = sum(attributes(a_nodes[x]) != attributes(b_nodes[correspondence[x]]) for x in a_ids)
            rel_errors = sum(a_relation(x, y) != b_relation(correspondence[x], correspondence[y])
                             for x, y in pairs)
            fused = 0.5 * attr_errors / len(a_ids) + 0.5 * rel_errors / len(pairs)
            values.append((fused, correspondence[target]))
            return
        for candidate in b_ids:
            if candidate not in used:
                visit(position + 1, assigned + [candidate], used | {candidate})

    visit(0, [], set())
    minimum = min(score for score, _ in values)
    unnormalized = [(math.exp(-(score - minimum) / SOFT_TEMPERATURE), candidate)
                    for score, candidate in values]
    partition = sum(weight for weight, _ in unnormalized)
    probabilities = {}
    for weight, candidate in unnormalized:
        probabilities[candidate] = probabilities.get(candidate, 0.0) + weight / partition
    ranked = sorted(((prob, candidate) for candidate, prob in probabilities.items()), reverse=True)
    best_prob, best_id = ranked[0]
    gap = best_prob - ranked[1][0] if len(ranked) > 1 else 1.0
    output["RELATIONAL"] = best_id if (minimum <= LIMIT_COST and best_prob >= REQUIRED_PROBABILITY
                                       and gap >= REQUIRED_MARGIN) else None
    return output


def validate(raw, design):
    issues = []
    if raw.get("schema") != "issue-8675-candidate-output-v1":
        issues.append("wrong output schema")
    expected_ids = [case["case_id"] for case in design["cases"]]
    rows = raw.get("rows", [])
    row_ids = [row.get("case_id") for row in rows]
    if len(row_ids) != len(set(row_ids)):
        issues.append("duplicate case id")
    if set(row_ids) != set(expected_ids) or len(row_ids) != len(expected_ids):
        issues.append("case coverage mismatch")
    row_map = {row.get("case_id"): row for row in rows}
    case_map = {case["case_id"]: case for case in design["cases"]}
    for case_id in expected_ids:
        row = row_map.get(case_id)
        if row is None:
            continue
        case = case_map[case_id]
        for field in ("split", "family"):
            if row.get(field) != case[field]:
                issues.append(f"{case_id}: {field} mismatch")
        expected = independent_predictions(case)
        got = row.get("predictions")
        if got != expected:
            issues.append(f"{case_id}: prediction differs from independent reconstruction")
    return issues


def stats(raw, design):
    by_id = {row["case_id"]: row for row in raw["rows"]}
    result = {}
    for policy in ("ID_PATH", "ROLE_LABEL", "RELATIONAL"):
        positives = [case for case in design["cases"] if case["split"] == "heldout_positive"]
        negatives = [case for case in design["cases"] if case["split"] == "heldout_negative"]
        correct = sum(by_id[c["case_id"]]["predictions"][policy] == c["oracle"]["target_current_id"]
                      for c in positives)
        false = sum(by_id[c["case_id"]]["predictions"][policy] is not None for c in negatives)
        result[policy] = {"heldout_positive_correct": correct, "heldout_positive_total": len(positives),
                          "coverage": correct / len(positives), "heldout_negative_false_rebinds": false,
                          "heldout_negative_total": len(negatives),
                          "false_rebind_rate": false / len(negatives),
                          "false_rebind_upper_95_one_sided": 1.0 - 0.05 ** (1 / len(negatives))
                          if false == 0 else None}
    return result


def corruption_checks(raw, design):
    checks = []
    mutations = []
    changed = copy.deepcopy(raw)
    changed["rows"][0]["predictions"]["RELATIONAL"] = "corrupted"
    mutations.append(("altered_prediction", changed))
    changed = copy.deepcopy(raw)
    changed["rows"].pop()
    mutations.append(("missing_row", changed))
    changed = copy.deepcopy(raw)
    changed["rows"].append(copy.deepcopy(changed["rows"][0]))
    mutations.append(("duplicate_row", changed))
    changed = copy.deepcopy(raw)
    changed["rows"][0]["family"] = "corrupted"
    mutations.append(("altered_case_metadata", changed))
    changed = copy.deepcopy(raw)
    del changed["rows"][0]["predictions"]["ROLE_LABEL"]
    mutations.append(("missing_policy", changed))
    for name, corrupted in mutations:
        detected = bool(validate(corrupted, design))
        checks.append({"control": name, "detected": detected})
    return checks


def audit(raw, design):
    findings = validate(raw, design)
    performance = stats(raw, design) if not findings else {}
    gates = {}
    if performance:
        relational = performance["RELATIONAL"]
        strongest_baseline = max(performance["ID_PATH"]["coverage"], performance["ROLE_LABEL"]["coverage"])
        gates["coverage_gain_ge_15pp"] = relational["coverage"] - strongest_baseline >= 0.15
        gates["false_rebind_upper_le_1pct"] = (relational["false_rebind_upper_95_one_sided"] is not None
                                                  and relational["false_rebind_upper_95_one_sided"] <= 0.01)
        gates["all_automorphism_controls_abstain"] = all(
            raw_row["predictions"]["RELATIONAL"] is None
            for raw_row in raw["rows"] if raw_row["family"] == "automorphism")
        gates["all_semantic_change_controls_abstain"] = all(
            raw_row["predictions"]["RELATIONAL"] is None
            for raw_row in raw["rows"] if raw_row["family"] == "semantic_role_change")
    checks = corruption_checks(raw, design)
    gates["corruption_controls_detected"] = all(check["detected"] for check in checks)
    gates["raw_reconstructed"] = not findings
    return {"schema": "issue-8675-independent-audit-v1", "status": "PASS_RELATIONAL_REIDENTIFICATION_SCOPED"
            if gates and all(gates.values()) else "FAIL_NO_GAIN_OR_FALSE_BIND",
            "findings": findings, "gates": gates, "metrics": performance,
            "corruption_controls": checks}


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as f:
        corpus = json.load(f)
    with open(sys.argv[2], encoding="utf-8") as f:
        output = json.load(f)
    report = audit(output, corpus)
    json.dump(report, sys.stdout, sort_keys=True, separators=(",", ":"))
    sys.stdout.write("\n")
    raise SystemExit(0 if report["status"] == "PASS_RELATIONAL_REIDENTIFICATION_SCOPED" else 1)
