#!/usr/bin/env python3
"""Independent raw-only oracle; imports no candidate or selector module."""

from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import platform
from pathlib import Path
from typing import Any


OBSERVED = ("PASS", "FAIL", "HOLD", "STOP")


def digest(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def variables(expression: dict[str, Any]) -> set[str]:
    if "predicate" in expression:
        return {expression["predicate"]}
    if "not" in expression:
        return variables(expression["not"])
    children = expression.get("all", expression.get("any"))
    if children is None:
        raise ValueError("oracle received an unsupported expression")
    output: set[str] = set()
    for child in children:
        output |= variables(child)
    return output


def validate_decision_witnesses(graph: dict[str, Any]) -> list[str]:
    invalid = sorted(item["id"] for item in graph["edges"] if item["validated"] is not True)
    for decision, formula in graph["decisions"].items():
        for premise in variables(formula):
            witnessed = any(
                link["from"] == premise
                and link["to"] == decision
                and link["validated"] is True
                for link in graph["edges"]
            )
            if not witnessed:
                raise ValueError("UNRANKABLE_GRAPH_EDGE_GAP:" + premise + ":" + decision)
    return invalid


def truth(expression: dict[str, Any], valuation: dict[str, bool]) -> bool:
    if "predicate" in expression:
        return valuation[expression["predicate"]]
    if "not" in expression:
        return not truth(expression["not"], valuation)
    if "all" in expression:
        return all(truth(part, valuation) for part in expression["all"])
    if "any" in expression:
        return any(truth(part, valuation) for part in expression["any"])
    raise ValueError("oracle received an unsupported expression")


def actions(graph: dict[str, Any], valuation: dict[str, bool]) -> list[str]:
    return sorted(name for name, formula in graph["decisions"].items() if truth(formula, valuation))


def grouped_origins(graph: dict[str, Any]) -> dict[str, list[str]]:
    seen: dict[str, list[str]] = {}
    for premise, metadata in graph["premises"].items():
        seen.setdefault(metadata["source_id"], []).append(premise)
    return {key: sorted(items) for key, items in sorted(seen.items()) if len(items) > 1}


def tested_variables(graph: dict[str, Any], experiment: dict[str, Any]) -> list[str]:
    target = experiment["target"]
    if target["kind"] == "predicate":
        if target["id"] not in graph["premises"]:
            raise ValueError("oracle received an unknown predicate target")
        return [target["id"]]
    if target["kind"] == "source_id":
        matched = sorted(
            premise for premise, metadata in graph["premises"].items()
            if metadata["source_id"] == target["id"]
        )
        if not matched:
            raise ValueError("oracle received an unknown source-id target")
        return matched
    raise ValueError("oracle received an unknown target kind")


def update_valuation(
    graph: dict[str, Any], experiment: dict[str, Any], original: dict[str, bool], observation: str,
    null_mode: bool = False,
) -> dict[str, bool]:
    changed = dict(original)
    if null_mode or observation in ("HOLD", "STOP"):
        return changed
    for premise in tested_variables(graph, experiment):
        changed[premise] = observation == "PASS"
    return changed


def reversal_table(spec: dict[str, Any], runnable: list[dict[str, Any]]) -> dict[str, float]:
    table = {}
    for experiment in runnable:
        fractions = []
        for scenario, initial_choice in spec["legacy_baseline_actions"].items():
            fractions.append(sum(
                row["p"] for row in experiment["legacy_outcomes"][scenario]
                if row["next_action"] != "STOP" and row["next_action"] != initial_choice
            ))
        table[experiment["id"]] = min(fractions)
    return table


def degrees(graph: dict[str, Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for relation in graph["edges"]:
        origin = relation["from"]
        counts[origin] = counts.get(origin, 0) + 1
    return counts


def exhaustive_trial_table(
    spec: dict[str, Any], runnable: list[dict[str, Any]], suppress_effects: bool = False
) -> tuple[list[str], dict[str, Any], dict[str, int]]:
    graph = spec["graph"]
    valuation = {key: item["truth"] for key, item in graph["premises"].items()}
    initial = actions(graph, valuation)
    tables: dict[str, Any] = {}
    impact: dict[str, int] = {}
    for experiment in runnable:
        one_test = {}
        for observation in OBSERVED:
            updated = update_valuation(graph, experiment, valuation, observation, suppress_effects)
            after = actions(graph, updated)
            changed = sorted(
                decision for decision in graph["decisions"]
                if (decision in initial) != (decision in after)
            )
            one_test[observation] = {"eligible_after": after, "changed_top_claims": changed}
        extent = max(len(one_test[tag]["changed_top_claims"]) for tag in ("PASS", "FAIL"))
        tables[experiment["id"]] = {
            "target": experiment["target"],
            "eligible_before": initial,
            "outcomes": one_test,
            "max_changed_top_claims": extent,
        }
        impact[experiment["id"]] = extent
    return initial, tables, impact


def ranked_choice(runnable: list[dict[str, Any]], evidence: dict[str, float | int]) -> str:
    top = max(evidence.values(), default=0)
    if top <= 0:
        return "UNRANKABLE"
    prices = {item["id"]: item["cost"] for item in runnable}
    tied = [name for name, score in evidence.items() if score == top]
    return min(tied, key=lambda name: (prices[name], name))


def choose_decision_test(
    portfolio: dict[str, Any], runnable: list[dict[str, Any]], impact: dict[str, int]
) -> str:
    """The audit oracle also abstains when the supplied graph is incomplete."""
    if portfolio["graph"].get("coverage_complete") is not True:
        return "UNRANKABLE"
    return ranked_choice(runnable, impact)


def oracle_core(spec: dict[str, Any]) -> dict[str, Any]:
    budget = spec["budget"]
    hard = budget["mandatory_sentinel"]
    runnable = [
        test for test in spec["experiments"]
        if test["cost"] + hard["cost"] <= budget["total"]
    ]
    if hard["mandatory"] is not True or hard["cost"] > budget["total"] or not runnable:
        raise ValueError("MANDATORY_SENTINEL_OR_FEASIBILITY_GATE")
    graph = spec["graph"]
    invalid_relations = validate_decision_witnesses(graph)
    degree = degrees(graph)
    degree_scores = {
        test["id"]: sum(degree.get(item, 0) for item in tested_variables(graph, test))
        for test in runnable
    }
    reversal_scores = reversal_table(spec, runnable)
    before, outcomes, effects = exhaustive_trial_table(spec, runnable)
    cheapest = sorted(runnable, key=lambda item: (item["cost"], item["id"]))[0]["id"]
    degree_top = max(degree_scores.values())
    degree_winner = sorted(name for name, value in degree_scores.items() if value == degree_top)[0]
    reversal_winner = ranked_choice(runnable, reversal_scores)
    graph_winner = choose_decision_test(spec, runnable, effects)

    _, no_effect_trials, no_effect_scores = exhaustive_trial_table(spec, runnable, suppress_effects=True)
    no_effect_top = max(no_effect_scores.values(), default=0)
    unknown_spec = copy.deepcopy(spec)
    unknown_spec["graph"]["coverage_complete"] = False
    unknown_winner = choose_decision_test(unknown_spec, runnable, effects)
    disjoint_spec = {**spec, "graph": spec["control_graphs"]["disjoint"]}
    validate_decision_witnesses(disjoint_spec["graph"])
    _, disjoint_outcomes, disjoint_impact = exhaustive_trial_table(disjoint_spec, runnable)
    disjoint_winner = choose_decision_test(disjoint_spec, runnable, disjoint_impact)

    return {
        "selectors": {
            "cheapest_first": cheapest,
            "raw_node_degree": degree_winner,
            "legacy_robust_reversal": reversal_winner,
            "graph_aware": graph_winner,
        },
        "score_tables": {
            "raw_declared_outdegree": degree_scores,
            "legacy_worst_case_reversal_mass": reversal_scores,
            "graph_max_changed_top_claims": effects,
        },
        "graph_audit": {
            "coverage_complete": graph["coverage_complete"],
            "baseline_eligible": before,
            "trial_details": outcomes,
            "unvalidated_edges_ignored": invalid_relations,
            "correlated_source_groups_collapsed": grouped_origins(graph),
        },
        "controls": {
            "null_graph_aware": "UNRANKABLE" if no_effect_top == 0 else ranked_choice(runnable, no_effect_scores),
            "null_max_changed_top_claims": no_effect_top,
            "unknown_coverage_graph_aware": unknown_winner,
            "unknown_coverage_reason": "UNKNOWN_GRAPH_COVERAGE",
            "null_trial_count": len(runnable),
            "null_trial_details": no_effect_trials,
            "disjoint_graph_aware": disjoint_winner,
            "disjoint_max_changed_top_claims": max(disjoint_impact.values(), default=0),
            "disjoint_score_table": disjoint_impact,
            "disjoint_trial_details": disjoint_outcomes,
        },
        "sentinel": {
            "id": hard["id"],
            "mandatory": hard["mandatory"],
            "cost": hard["cost"],
            "total_budget": budget["total"],
            "experiment_cost_cap": budget["total"] - hard["cost"],
            "all_feasible_tests_retain_sentinel": all(
                test["cost"] + hard["cost"] <= budget["total"] for test in runnable
            ),
        },
    }


CORE_KEYS = ("selectors", "score_tables", "graph_audit", "controls", "sentinel")


def semantic_errors(
    fixture: dict[str, Any], result: dict[str, Any], freeze_digest: str,
    fixture_digest: str, selector_digest: str, freeze: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    expected = oracle_core(fixture)
    if result.get("allocation_id") != freeze["allocation_id"]:
        errors.append("allocation identity mismatch")
    if result.get("issue") != freeze["issue"] or result.get("main_sha") != freeze["base_main_sha"]:
        errors.append("issue or main source binding mismatch")
    if result.get("freeze_sha256") != freeze_digest:
        errors.append("freeze digest mismatch")
    if result.get("fixture_sha256") != fixture_digest:
        errors.append("fixture digest mismatch")
    if result.get("candidate_sha256") != selector_digest:
        errors.append("candidate source digest mismatch")
    if result.get("status") != "SYNTHETIC_METHOD_CONSTRUCTION_ONLY":
        errors.append("scope/status promotion mismatch")
    if result.get("scientific_support_events") != 0:
        errors.append("synthetic output mislabeled as scientific support")
    for key in CORE_KEYS:
        if result.get(key) != expected[key]:
            errors.append("independent oracle mismatch: " + key)
    for key, selected in freeze["expected_selectors"].items():
        category = "selectors" if key in expected["selectors"] else "controls"
        if result.get(category, {}).get(key) != selected:
            errors.append("frozen selector gate mismatch: " + key)
    for key, value in freeze["expected_control_values"].items():
        if result.get("controls", {}).get(key) != value:
            errors.append("frozen control gate mismatch: " + key)
    return errors


def corruption_controls(
    fixture: dict[str, Any], result: dict[str, Any], freeze_digest: str,
    fixture_digest: str, selector_digest: str, freeze: dict[str, Any],
) -> list[dict[str, Any]]:
    variants: list[tuple[str, Any]] = []

    def variant(name: str, mutate: Any) -> None:
        altered = copy.deepcopy(result)
        mutate(altered)
        variants.append((name, altered))

    variant("promote_high_degree_decoy", lambda r: r["selectors"].__setitem__("graph_aware", "E-degree-decoy"))
    variant("drop_mandatory_sentinel", lambda r: r["sentinel"].__setitem__("mandatory", False))
    variant("trust_unvalidated_edge", lambda r: r["graph_audit"].__setitem__("unvalidated_edges_ignored", []))
    variant("split_correlated_origin", lambda r: r["graph_audit"].__setitem__("correlated_source_groups_collapsed", {}))
    variant("launder_stop_as_decisive", lambda r: r["graph_audit"]["trial_details"]["E-shared-prerequisite"]["outcomes"]["STOP"].__setitem__("eligible_after", []))
    variant("manufacture_null_value", lambda r: r["controls"].__setitem__("null_graph_aware", "E-shared-prerequisite"))
    variant("rank_incomplete_coverage", lambda r: r["controls"].__setitem__("unknown_coverage_graph_aware", "E-shared-prerequisite"))
    variant("manufacture_disjoint_shared_value", lambda r: r["controls"]["disjoint_trial_details"]["E-shared-prerequisite"]["outcomes"]["FAIL"].__setitem__("eligible_after", []))

    checks = []
    for name, altered in variants:
        errors = semantic_errors(
            fixture, altered, freeze_digest, fixture_digest, selector_digest, freeze
        )
        checks.append({"id": name, "rejected": bool(errors), "error_count": len(errors)})
    return checks


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--freeze", required=True)
    parser.add_argument("--candidate-result", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    fixture_bytes = Path(args.fixture).read_bytes()
    freeze_bytes = Path(args.freeze).read_bytes()
    candidate_bytes = Path(__file__).with_name("candidate.py").read_bytes()
    auditor_bytes = Path(__file__).read_bytes()
    fixture = json.loads(fixture_bytes)
    freeze = json.loads(freeze_bytes)
    result = json.loads(Path(args.candidate_result).read_text(encoding="utf-8"))
    observed_hashes = {
        "fixture.json": digest(fixture_bytes),
        "candidate.py": digest(candidate_bytes),
        "audit.py": digest(auditor_bytes),
    }
    errors = []
    for name, actual in observed_hashes.items():
        if freeze["sha256"].get(name) != actual:
            errors.append("frozen source hash mismatch: " + name)
    if freeze["freeze_time_utc"] == "PENDING_FINAL_SOURCE_FREEZE":
        errors.append("freeze not finalized")
    freeze_hash = digest(freeze_bytes)
    fixture_hash = digest(fixture_bytes)
    candidate_hash = digest(candidate_bytes)
    errors.extend(semantic_errors(fixture, result, freeze_hash, fixture_hash, candidate_hash, freeze))
    controls = corruption_controls(fixture, result, freeze_hash, fixture_hash, candidate_hash, freeze)
    rejected = sum(1 for control in controls if control["rejected"])
    if rejected != len(controls):
        errors.append("one or more effective corruption controls were accepted")

    report = {
        "allocation_id": freeze["allocation_id"],
        "status": "PASS_METHOD_SCOPED" if not errors else "FAIL_AUDIT",
        "errors": errors,
        "raw_only_oracle": "independently implemented in audit.py; imports no selector code",
        "freeze_sha256": freeze_hash,
        "fixture_sha256": fixture_hash,
        "candidate_sha256": candidate_hash,
        "auditor_sha256": digest(auditor_bytes),
        "auditor_started_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": platform.python_version(),
        "primary_selectors_reconstructed": bool(not semantic_errors(
            fixture, result, freeze_hash, fixture_hash, candidate_hash, freeze
        )),
        "mutation_controls": controls,
        "mutation_controls_rejected": rejected,
        "mutation_controls_total": len(controls),
        "scope": "finite authored synthetic graph and selector only; no empirical prior, interface, or safety claim",
    }
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "errors": errors, "mutation_controls_rejected": rejected}, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
