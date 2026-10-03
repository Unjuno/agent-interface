#!/usr/bin/env python3
"""One-pass synthetic next-experiment selector for Issue #6003 A01."""

from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import platform
from pathlib import Path
from typing import Any


OUTCOMES = ("PASS", "FAIL", "HOLD", "STOP")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def predicate_refs(expr: dict[str, Any]) -> set[str]:
    if "predicate" in expr:
        return {expr["predicate"]}
    if "not" in expr:
        return predicate_refs(expr["not"])
    if "all" in expr or "any" in expr:
        key = "all" if "all" in expr else "any"
        refs: set[str] = set()
        for item in expr[key]:
            refs.update(predicate_refs(item))
        return refs
    raise ValueError("unsupported expression node")


def check_formula_edges(graph: dict[str, Any]) -> list[str]:
    """Fail closed if any predicate used by a top decision lacks a validated edge."""
    ignored = sorted(edge["id"] for edge in graph["edges"] if not edge["validated"])
    for claim_id, expr in graph["decisions"].items():
        for predicate in predicate_refs(expr):
            if not any(
                edge["from"] == predicate
                and edge["to"] == claim_id
                and edge["validated"] is True
                for edge in graph["edges"]
            ):
                raise ValueError("UNRANKABLE_GRAPH_EDGE_GAP:" + predicate + ":" + claim_id)
    return ignored


def eval_expr(expr: dict[str, Any], values: dict[str, bool]) -> bool:
    if "predicate" in expr:
        return values[expr["predicate"]]
    if "not" in expr:
        return not eval_expr(expr["not"], values)
    if "all" in expr:
        return all(eval_expr(item, values) for item in expr["all"])
    if "any" in expr:
        return any(eval_expr(item, values) for item in expr["any"])
    raise ValueError("unsupported expression node")


def eligible(graph: dict[str, Any], values: dict[str, bool]) -> list[str]:
    return sorted(
        claim for claim, expr in graph["decisions"].items()
        if eval_expr(expr, values)
    )


def source_groups(graph: dict[str, Any]) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {}
    for predicate, detail in graph["premises"].items():
        groups.setdefault(detail["source_id"], []).append(predicate)
    return {key: sorted(value) for key, value in sorted(groups.items()) if len(value) > 1}


def target_predicates(graph: dict[str, Any], target: dict[str, str]) -> list[str]:
    if target["kind"] == "predicate":
        if target["id"] not in graph["premises"]:
            raise ValueError("unknown target predicate")
        return [target["id"]]
    if target["kind"] == "source_id":
        members = [
            name for name, detail in graph["premises"].items()
            if detail["source_id"] == target["id"]
        ]
        if not members:
            raise ValueError("unknown target source id")
        return sorted(members)
    raise ValueError("unsupported experiment target")


def apply_test(
    graph: dict[str, Any],
    experiment: dict[str, Any],
    values: dict[str, bool],
    outcome: str,
    null_control: bool = False,
) -> dict[str, bool]:
    updated = dict(values)
    if null_control or outcome in ("HOLD", "STOP"):
        return updated
    value = outcome == "PASS"
    for predicate in target_predicates(graph, experiment["target"]):
        updated[predicate] = value
    return updated


def legacy_reversal_scores(spec: dict[str, Any], feasible: list[dict[str, Any]]) -> dict[str, float]:
    scores: dict[str, float] = {}
    for experiment in feasible:
        scenario_masses = []
        for scenario, baseline in spec["legacy_baseline_actions"].items():
            mass = sum(
                row["p"] for row in experiment["legacy_outcomes"][scenario]
                if row["next_action"] != "STOP" and row["next_action"] != baseline
            )
            scenario_masses.append(mass)
        scores[experiment["id"]] = min(scenario_masses)
    return scores


def outdegrees(graph: dict[str, Any]) -> dict[str, int]:
    result = {name: 0 for name in graph["premises"]}
    for edge in graph["edges"]:
        result[edge["from"]] = result.get(edge["from"], 0) + 1
    return result


def decision_trials(
    spec: dict[str, Any],
    feasible: list[dict[str, Any]],
    null_control: bool = False,
) -> tuple[list[str], dict[str, dict[str, Any]], dict[str, int]]:
    graph = spec["graph"]
    values = {name: detail["truth"] for name, detail in graph["premises"].items()}
    before = eligible(graph, values)
    details: dict[str, dict[str, Any]] = {}
    scores: dict[str, int] = {}
    for experiment in feasible:
        result_rows: dict[str, Any] = {}
        for outcome in OUTCOMES:
            after_values = apply_test(graph, experiment, values, outcome, null_control)
            after = eligible(graph, after_values)
            changed = sorted(
                claim for claim in graph["decisions"]
                if ((claim in before) != (claim in after))
            )
            result_rows[outcome] = {
                "eligible_after": after,
                "changed_top_claims": changed,
            }
        max_change = max(
            len(result_rows[outcome]["changed_top_claims"])
            for outcome in ("PASS", "FAIL")
        )
        details[experiment["id"]] = {
            "target": experiment["target"],
            "eligible_before": before,
            "outcomes": result_rows,
            "max_changed_top_claims": max_change,
        }
        scores[experiment["id"]] = max_change
    return before, details, scores


def choose_max(
    experiments: list[dict[str, Any]], scores: dict[str, float | int]
) -> str:
    best = max(scores.values(), default=0)
    if best <= 0:
        return "UNRANKABLE"
    candidates = [name for name, score in scores.items() if score == best]
    costs = {item["id"]: item["cost"] for item in experiments}
    return min(candidates, key=lambda name: (costs[name], name))


def graph_aware_choice(
    spec: dict[str, Any], experiments: list[dict[str, Any]], scores: dict[str, int]
) -> str:
    """Fail closed on incomplete coverage instead of ranking a partial graph."""
    if spec["graph"].get("coverage_complete") is not True:
        return "UNRANKABLE"
    return choose_max(experiments, scores)


def compute_core(spec: dict[str, Any]) -> dict[str, Any]:
    budget = spec["budget"]
    sentinel = budget["mandatory_sentinel"]
    experiments = spec["experiments"]
    feasible = [
        item for item in experiments
        if item["cost"] + sentinel["cost"] <= budget["total"]
    ]
    if sentinel["mandatory"] is not True or sentinel["cost"] > budget["total"]:
        raise ValueError("MANDATORY_SENTINEL_NOT_FEASIBLE")
    if not feasible:
        raise ValueError("NO_FEASIBLE_EXPERIMENT")

    graph = spec["graph"]
    ignored_edges = check_formula_edges(graph)
    degree = outdegrees(graph)
    degree_scores = {
        item["id"]: sum(degree[node] for node in target_predicates(graph, item["target"]))
        for item in feasible
    }
    reversal = legacy_reversal_scores(spec, feasible)
    before, trials, graph_scores = decision_trials(spec, feasible)

    cheapest = min(feasible, key=lambda item: (item["cost"], item["id"]))["id"]
    degree_choice = min(
        (name for name, score in degree_scores.items() if score == max(degree_scores.values())),
        key=lambda name: name,
    )
    reversal_choice = choose_max(feasible, reversal)
    graph_choice = graph_aware_choice(spec, feasible, graph_scores)

    _, null_trials, null_scores = decision_trials(spec, feasible, null_control=True)
    null_best = max(null_scores.values(), default=0)
    unknown = copy.deepcopy(spec)
    unknown["graph"]["coverage_complete"] = False
    unknown_choice = graph_aware_choice(unknown, feasible, graph_scores)
    disjoint = copy.deepcopy(spec)
    disjoint["graph"] = copy.deepcopy(spec["control_graphs"]["disjoint"])
    check_formula_edges(disjoint["graph"])
    _, disjoint_trials, disjoint_scores = decision_trials(disjoint, feasible)
    disjoint_choice = graph_aware_choice(disjoint, feasible, disjoint_scores)

    return {
        "selectors": {
            "cheapest_first": cheapest,
            "raw_node_degree": degree_choice,
            "legacy_robust_reversal": reversal_choice,
            "graph_aware": graph_choice,
        },
        "score_tables": {
            "raw_declared_outdegree": degree_scores,
            "legacy_worst_case_reversal_mass": reversal,
            "graph_max_changed_top_claims": graph_scores,
        },
        "graph_audit": {
            "coverage_complete": graph["coverage_complete"],
            "baseline_eligible": before,
            "trial_details": trials,
            "unvalidated_edges_ignored": ignored_edges,
            "correlated_source_groups_collapsed": source_groups(graph),
        },
        "controls": {
            "null_graph_aware": "UNRANKABLE" if null_best == 0 else choose_max(feasible, null_scores),
            "null_max_changed_top_claims": null_best,
            "unknown_coverage_graph_aware": unknown_choice,
            "unknown_coverage_reason": "UNKNOWN_GRAPH_COVERAGE",
            "null_trial_count": len(null_trials),
            "null_trial_details": null_trials,
            "disjoint_graph_aware": disjoint_choice,
            "disjoint_max_changed_top_claims": max(disjoint_scores.values(), default=0),
            "disjoint_score_table": disjoint_scores,
            "disjoint_trial_details": disjoint_trials,
        },
        "sentinel": {
            "id": sentinel["id"],
            "mandatory": sentinel["mandatory"],
            "cost": sentinel["cost"],
            "total_budget": budget["total"],
            "experiment_cost_cap": budget["total"] - sentinel["cost"],
            "all_feasible_tests_retain_sentinel": all(
                item["cost"] + sentinel["cost"] <= budget["total"] for item in feasible
            ),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--freeze", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    fixture_path = Path(args.fixture)
    freeze_path = Path(args.freeze)
    fixture_bytes = fixture_path.read_bytes()
    freeze_bytes = freeze_path.read_bytes()
    fixture = json.loads(fixture_bytes)
    freeze = json.loads(freeze_bytes)
    candidate_bytes = Path(__file__).read_bytes()
    hashes = freeze["sha256"]
    if sha256(fixture_bytes) != hashes["fixture.json"]:
        raise SystemExit("STOP_FIXTURE_HASH_MISMATCH")
    if sha256(candidate_bytes) != hashes["candidate.py"]:
        raise SystemExit("STOP_CANDIDATE_HASH_MISMATCH")
    if freeze["freeze_time_utc"] == "PENDING_FINAL_SOURCE_FREEZE":
        raise SystemExit("STOP_FREEZE_INCOMPLETE")

    result = {
        "allocation_id": freeze["allocation_id"],
        "issue": freeze["issue"],
        "main_sha": freeze["base_main_sha"],
        "freeze_sha256": sha256(freeze_bytes),
        "fixture_sha256": sha256(fixture_bytes),
        "candidate_sha256": sha256(candidate_bytes),
        "run_started_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "status": "SYNTHETIC_METHOD_CONSTRUCTION_ONLY",
        "scientific_support_events": 0,
        **compute_core(fixture),
        "scope": "one authored finite graph; no empirical prior, interface effect, runtime safety, or productivity result",
    }
    output_path = Path(args.output)
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"allocation_id": result["allocation_id"], "selectors": result["selectors"], "status": result["status"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
