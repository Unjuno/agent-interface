#!/usr/bin/env python3
"""Finite synthetic crossed-verdict assay for Issue #6222 (no model or app)."""

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path


VALID = {"PASS", "FAIL", "UNKNOWN"}


def _matches(rule, artifact_id, evaluator, setup, repeat):
    return (
        rule["artifact_id"] == artifact_id
        and rule["evaluator"] in ("*", evaluator)
        and rule["setup"] in ("*", setup)
        and rule["repeat"] in ("*", repeat)
    )


def _verdict(artifact, fixture, evaluator, setup, repeat):
    matches = [r for r in fixture["rules"] if _matches(r, artifact["id"], evaluator, setup, repeat)]
    if len(matches) > 1:
        raise ValueError(f"overlapping fixture rules for {artifact['id']} {evaluator}/{setup}/{repeat}")
    if matches:
        return matches[0]["verdict"]
    return artifact["oracle"]


def _check_fixture(fixture):
    if fixture.get("schema") != "agent-interface/6222-crossed-verdict-fixture-v1":
        raise ValueError("unexpected fixture schema")
    if fixture.get("routes") != ["A", "B"]:
        raise ValueError("routes must remain [A, B]")
    if fixture.get("evaluators") != ["E0", "E1"] or fixture.get("setups") != ["S0", "S1"]:
        raise ValueError("crossing axes changed")
    if fixture.get("repeats") != [1, 2, 3]:
        raise ValueError("repeat axis changed")
    artifact_ids = []
    case_ids = []
    for case in fixture["cases"]:
        case_ids.append(case["id"])
        if len(case["artifacts"]) != 4:
            raise ValueError("each case must have two artifacts per route")
        route_counts = {"A": 0, "B": 0}
        for artifact in case["artifacts"]:
            artifact_ids.append(artifact["id"])
            if artifact["route"] not in route_counts or artifact["oracle"] not in VALID:
                raise ValueError("invalid route/oracle")
            route_counts[artifact["route"]] += 1
        if route_counts != {"A": 2, "B": 2}:
            raise ValueError("route panel is not balanced")
    if len(set(case_ids)) != len(case_ids) or len(set(artifact_ids)) != len(artifact_ids):
        raise ValueError("duplicate case/artifact identity")
    for rule in fixture["rules"]:
        if rule["verdict"] is not None and rule["verdict"] not in VALID:
            raise ValueError("invalid planted verdict")


def _expand(fixture):
    rows = []
    for case in fixture["cases"]:
        for artifact in case["artifacts"]:
            for evaluator in fixture["evaluators"]:
                for setup in fixture["setups"]:
                    for repeat in fixture["repeats"]:
                        rows.append({
                            "case_id": case["id"],
                            "artifact_id": artifact["id"],
                            "route": artifact["route"],
                            "oracle": artifact["oracle"],
                            "evaluator": evaluator,
                            "setup": setup,
                            "repeat": repeat,
                            "verdict": _verdict(artifact, fixture, evaluator, setup, repeat),
                        })
    deck = []
    for artifact in fixture["reference_deck"]:
        for evaluator in fixture["evaluators"]:
            for setup in fixture["setups"]:
                for repeat in fixture["repeats"]:
                    deck.append({
                        "artifact_id": artifact["id"],
                        "oracle": artifact["oracle"],
                        "evaluator": evaluator,
                        "setup": setup,
                        "repeat": repeat,
                        "verdict": artifact["oracle"],
                    })
    return rows, deck


def _rate(rows):
    known = [r for r in rows if r["oracle"] != "UNKNOWN"]
    denominator = len(known)
    passed = sum(r["verdict"] == "PASS" for r in known)
    missing = sum(r["verdict"] is None for r in known)
    return {
        "passed": passed,
        "missing": missing,
        "denominator": denominator,
        "lower": passed / denominator if denominator else None,
        "upper": (passed + missing) / denominator if denominator else None,
    }


def _rank(a, b):
    if not a["denominator"] or not b["denominator"]:
        return "NO_COMPARABLE_EVIDENCE"
    a_low, a_high = a["passed"], a["passed"] + a["missing"]
    b_low, b_high = b["passed"], b["passed"] + b["missing"]
    if a_low * b["denominator"] > b_high * a["denominator"]:
        return "A>B"
    if b_low * a["denominator"] > a_high * b["denominator"]:
        return "B>A"
    if a["missing"] == 0 and b["missing"] == 0 and a_low * b["denominator"] == b_low * a["denominator"]:
        return "TIE"
    return "UNRESOLVED"


def analyze(fixture, freeze):
    _check_fixture(fixture)
    rows, deck = _expand(fixture)
    cells = [f"{e}/{s}/{r}" for e in fixture["evaluators"] for s in fixture["setups"] for r in fixture["repeats"]]
    scores = {}
    one_pass = {}
    crossed = {}
    for case in fixture["cases"]:
        case_id = case["id"]
        scores[case_id] = {}
        ranks = []
        for cell in cells:
            evaluator, setup, repeat_text = cell.split("/")
            repeat = int(repeat_text)
            cell_rows = [r for r in rows if r["case_id"] == case_id and r["evaluator"] == evaluator and r["setup"] == setup and r["repeat"] == repeat]
            by_route = {route: _rate([r for r in cell_rows if r["route"] == route]) for route in ("A", "B")}
            scores[case_id][cell] = by_route
            ranks.append(_rank(by_route["A"], by_route["B"]))
        one_pass[case_id] = [_rank(scores[case_id]["E0/S0/1"]["A"], scores[case_id]["E0/S0/1"]["B"])]
        crossed[case_id] = sorted(set(ranks))

    within = defaultdict(set)
    across_setups = defaultdict(set)
    across_evaluators = defaultdict(set)
    for row in rows:
        verdict = row["verdict"]
        if verdict not in ("PASS", "FAIL"):
            continue
        within[(row["artifact_id"], row["evaluator"], row["setup"])].add(verdict)
        across_setups[(row["artifact_id"], row["evaluator"], row["repeat"])].add(verdict)
        across_evaluators[(row["artifact_id"], row["setup"], row["repeat"])].add(verdict)
    within_flips = sum(len(values) > 1 for values in within.values())
    setup_disagreements = sum(len(values) > 1 for values in across_setups.values())
    evaluator_disagreements = sum(len(values) > 1 for values in across_evaluators.values())

    artifacts = {a["id"]: a for c in fixture["cases"] for a in c["artifacts"]}
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["artifact_id"]].append(row)
    shared_bias = []
    for artifact_id, artifact_rows in grouped.items():
        oracle = artifacts[artifact_id]["oracle"]
        observed = {r["verdict"] for r in artifact_rows if r["verdict"] in ("PASS", "FAIL")}
        all_observed = all(r["verdict"] in ("PASS", "FAIL") for r in artifact_rows)
        if oracle in ("PASS", "FAIL") and len(observed) == 1 and all_observed and next(iter(observed)) != oracle:
            shared_bias.append(artifact_id)
    unknown_by_case = {case["id"]: sum(r["verdict"] == "UNKNOWN" for r in rows if r["case_id"] == case["id"]) for case in fixture["cases"]}
    missing_by_case = {case["id"]: sum(r["verdict"] is None for r in rows if r["case_id"] == case["id"]) for case in fixture["cases"]}
    ranking_reversals = sorted(
        case_id for case_id in one_pass
        if one_pass[case_id] == ["A>B"] and "B>A" in crossed[case_id]
    )
    deck_pass = all(r["verdict"] == r["oracle"] and r["verdict"] in VALID for r in deck)
    return {
        "schema": "agent-interface/6222-crossed-verdict-candidate-v1",
        "allocation_id": freeze["allocation_id"],
        "main_sha": freeze["main_sha"],
        "fixture_sha256": hashlib.sha256(json.dumps(fixture, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        "observations": rows,
        "reference_rows": deck,
        "reference_deck_pass": deck_pass,
        "within_scorer_flip_cells": within_flips,
        "setup_disagreement_cells": setup_disagreements,
        "evaluator_disagreement_cells": evaluator_disagreements,
        "one_pass_rankings": one_pass,
        "crossed_rankings": crossed,
        "ranking_reversals": ranking_reversals,
        "score_intervals": scores,
        "shared_bias_flags": sorted(shared_bias),
        "shared_bias_is_validity_certificate": False,
        "unknown_rows_by_case": unknown_by_case,
        "missing_rows_by_case": missing_by_case,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--freeze", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    fixture_path = Path(args.fixture)
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    freeze = json.loads(Path(args.freeze).read_text(encoding="utf-8"))
    result = analyze(fixture, freeze)
    out = Path(args.output)
    if out.exists():
        raise FileExistsError(f"output collision: {out}")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"disposition": "CANDIDATE_COMPLETE", "observations": len(result["observations"]), "ranking_reversals": result["ranking_reversals"]}, sort_keys=True))


if __name__ == "__main__":
    main()
