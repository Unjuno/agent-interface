#!/usr/bin/env python3
"""Finite equality-closure saturation and extraction for Issue #7462 T0."""
import argparse
import copy
import hashlib
import json
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
RULE_ORDER = ("deduplicate_passive_check", "idempotent_trim", "idempotent_lower", "commute_trim_lower")


def canon(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def expr_rewrites(expr):
    out = []
    if not isinstance(expr, list) or len(expr) != 2:
        return out
    op, child = expr
    for child_rule, changed in expr_rewrites(child):
        out.append((child_rule, [op, changed]))
    if isinstance(child, list) and len(child) == 2:
        child_op, grandchild = child
        if op == child_op == "TRIM":
            out.append(("idempotent_trim", [op, grandchild]))
        elif op == child_op == "LOWER":
            out.append(("idempotent_lower", [op, grandchild]))
        elif {op, child_op} == {"TRIM", "LOWER"}:
            out.append(("commute_trim_lower", [child_op, [op, grandchild]]))
    return out


def rewrites(program):
    out = []
    for rule, expr in expr_rewrites(program["pure_expr"]):
        changed = copy.deepcopy(program)
        changed["pure_expr"] = expr
        out.append((rule, changed))
    for path_name, steps in program["paths"].items():
        for index in range(len(steps) - 1):
            left, right = steps[index:index + 2]
            if left == right and left.get("op") == "PASSIVE_CHECK":
                changed = copy.deepcopy(program)
                del changed["paths"][path_name][index + 1]
                out.append(("deduplicate_passive_check", changed))
    return [(rule, value) for rule, value in out if canon(value) != canon(program)]


def cost(program, weights):
    pure_ops = []
    node = program["pure_expr"]
    while isinstance(node, list) and len(node) == 2:
        pure_ops.append(node[0])
        node = node[1]
    ops = pure_ops + [step["op"] for path in program["paths"].values() for step in path]
    return (sum(weights.get(op, 0) for op in ops), sum(1 for op in ops if weights.get(op, 0) > 0))


def greedy(source, weights):
    current = copy.deepcopy(source)
    while True:
        selected = None
        for rule in RULE_ORDER:
            candidates = [value for name, value in rewrites(current) if name == rule]
            for value in sorted(candidates, key=canon):
                if cost(value, weights) < cost(current, weights):
                    selected = value
                    break
            if selected is not None:
                break
        if selected is None:
            return current
        current = selected


def saturate_extract(source, weights, max_terms, max_rounds):
    started = time.perf_counter_ns()
    source_key = canon(source)
    terms = {source_key: copy.deepcopy(source)}
    frontier = [source_key]
    rounds = 0
    complete = True
    while frontier:
        if rounds >= max_rounds:
            complete = False
            break
        rounds += 1
        next_frontier = []
        for key in frontier:
            for _, value in rewrites(terms[key]):
                new_key = canon(value)
                if new_key in terms:
                    continue
                if len(terms) >= max_terms:
                    complete = False
                    frontier = []
                    break
                terms[new_key] = value
                next_frontier.append(new_key)
            if not complete:
                break
        frontier = next_frontier if complete else []
    elapsed = time.perf_counter_ns() - started
    chosen_key = min(terms, key=lambda key: (cost(terms[key], weights), key))
    return terms[chosen_key], {
        "saturated": complete,
        "term_count": len(terms),
        "rounds": rounds,
        "saturation_time_ns": elapsed,
        "extraction_failure": not complete,
        "selected_cost": list(cost(terms[chosen_key], weights)),
        "selected_sha256": hashlib.sha256(chosen_key.encode()).hexdigest(),
        "term_set_sha256": hashlib.sha256("\n".join(sorted(terms)).encode()).hexdigest(),
        "saturated_terms": [terms[key] for key in sorted(terms)],
    }


def run(fixture):
    results = []
    for source in fixture["programs"]:
        greedy_program = greedy(source, fixture["cost_units"])
        extracted, stats = saturate_extract(source, fixture["cost_units"],
                                             fixture["limits"]["max_terms"],
                                             fixture["limits"]["max_rounds"])
        results.append({"program_id": source["program_id"], "source": source,
                        "greedy": greedy_program, "extracted": extracted,
                        "source_cost": list(cost(source, fixture["cost_units"])),
                        "greedy_cost": list(cost(greedy_program, fixture["cost_units"])),
                        "extracted_cost": list(cost(extracted, fixture["cost_units"])),
                        "saturation": stats})
    return {"schema": "unjuno.issue7462.t0.candidate.v1",
            "fixture_sha256": hashlib.sha256((HERE / "fixture.json").read_bytes()).hexdigest(),
            "candidate_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "results": results}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    fixture = json.loads((HERE / "fixture.json").read_text(encoding="utf-8"))
    result = run(fixture)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"schema": result["schema"], "program_count": len(result["results"]),
                      "saturation": {r["program_id"]: r["saturation"] for r in result["results"]}}, sort_keys=True))


if __name__ == "__main__":
    main()
