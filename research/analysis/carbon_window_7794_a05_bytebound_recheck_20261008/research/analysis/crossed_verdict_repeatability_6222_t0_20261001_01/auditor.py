#!/usr/bin/env python3
"""Independent raw-only reconstruction for Issue #6222 synthetic T0."""

import argparse
import copy
import hashlib
import json
from collections import defaultdict
from pathlib import Path


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _expected(fixture, freeze):
    if fixture.get("schema") != "agent-interface/6222-crossed-verdict-fixture-v1":
        raise ValueError("fixture_schema")
    if fixture.get("routes") != ["A", "B"] or fixture.get("evaluators") != ["E0", "E1"]:
        raise ValueError("axis_contract")
    if fixture.get("setups") != ["S0", "S1"] or fixture.get("repeats") != [1, 2, 3]:
        raise ValueError("crossing_contract")
    artifacts = {}
    for case in fixture["cases"]:
        counts = {"A": 0, "B": 0}
        for artifact in case["artifacts"]:
            if artifact["id"] in artifacts or artifact["route"] not in counts:
                raise ValueError("duplicate_or_invalid_artifact")
            if artifact["oracle"] not in ("PASS", "FAIL", "UNKNOWN"):
                raise ValueError("invalid_oracle_label")
            artifacts[artifact["id"]] = (case["id"], artifact)
            counts[artifact["route"]] += 1
        if counts != {"A": 2, "B": 2}:
            raise ValueError("unbalanced_case")

    observed = []
    for case in fixture["cases"]:
        for artifact in case["artifacts"]:
            for evaluator in ("E0", "E1"):
                for setup in ("S0", "S1"):
                    for repeat in (1, 2, 3):
                        matches = [rule for rule in fixture["rules"] if (
                            rule["artifact_id"] == artifact["id"]
                            and rule["evaluator"] in ("*", evaluator)
                            and rule["setup"] in ("*", setup)
                            and rule["repeat"] in ("*", repeat)
                        )]
                        if len(matches) > 1:
                            raise ValueError("overlapping_rules")
                        verdict = matches[0]["verdict"] if matches else artifact["oracle"]
                        if verdict is not None and verdict not in ("PASS", "FAIL", "UNKNOWN"):
                            raise ValueError("invalid_verdict")
                        observed.append({
                            "case_id": case["id"], "artifact_id": artifact["id"],
                            "route": artifact["route"], "oracle": artifact["oracle"],
                            "evaluator": evaluator, "setup": setup,
                            "repeat": repeat, "verdict": verdict,
                        })
    reference = []
    for standard in fixture["reference_deck"]:
        for evaluator in ("E0", "E1"):
            for setup in ("S0", "S1"):
                for repeat in (1, 2, 3):
                    reference.append({
                        "artifact_id": standard["id"], "oracle": standard["oracle"],
                        "evaluator": evaluator, "setup": setup,
                        "repeat": repeat, "verdict": standard["oracle"],
                    })

    score_table = {}
    single = {}
    ranks_by_cell = {}
    for case in fixture["cases"]:
        cid = case["id"]
        score_table[cid] = {}
        ranks = []
        for evaluator in ("E0", "E1"):
            for setup in ("S0", "S1"):
                for repeat in (1, 2, 3):
                    key = f"{evaluator}/{setup}/{repeat}"
                    selected = [x for x in observed if x["case_id"] == cid and x["evaluator"] == evaluator and x["setup"] == setup and x["repeat"] == repeat]
                    rates = {}
                    for route in ("A", "B"):
                        usable = [x for x in selected if x["route"] == route and x["oracle"] != "UNKNOWN"]
                        den = len(usable)
                        n_pass = sum(x["verdict"] == "PASS" for x in usable)
                        n_missing = sum(x["verdict"] is None for x in usable)
                        rates[route] = {
                            "passed": n_pass, "missing": n_missing,
                            "denominator": den,
                            "lower": n_pass / den if den else None,
                            "upper": (n_pass + n_missing) / den if den else None,
                        }
                    a, b = rates["A"], rates["B"]
                    if not a["denominator"] or not b["denominator"]:
                        rank = "NO_COMPARABLE_EVIDENCE"
                    elif a["passed"] * b["denominator"] > (b["passed"] + b["missing"]) * a["denominator"]:
                        rank = "A>B"
                    elif b["passed"] * a["denominator"] > (a["passed"] + a["missing"]) * b["denominator"]:
                        rank = "B>A"
                    elif not a["missing"] and not b["missing"] and a["passed"] * b["denominator"] == b["passed"] * a["denominator"]:
                        rank = "TIE"
                    else:
                        rank = "UNRESOLVED"
                    score_table[cid][key] = rates
                    ranks.append(rank)
        one_rank = None
        for key, rates in score_table[cid].items():
            if key == "E0/S0/1":
                a, b = rates["A"], rates["B"]
                if not a["denominator"] or not b["denominator"]:
                    one_rank = "NO_COMPARABLE_EVIDENCE"
                elif a["passed"] * b["denominator"] > (b["passed"] + b["missing"]) * a["denominator"]:
                    one_rank = "A>B"
                elif b["passed"] * a["denominator"] > (a["passed"] + a["missing"]) * b["denominator"]:
                    one_rank = "B>A"
                elif not a["missing"] and not b["missing"] and a["passed"] * b["denominator"] == b["passed"] * a["denominator"]:
                    one_rank = "TIE"
                else:
                    one_rank = "UNRESOLVED"
        single[cid] = [one_rank]
        ranks_by_cell[cid] = sorted(set(ranks))

    def disagreement_count(key_fields, case_fields):
        groups = defaultdict(set)
        for row in observed:
            if row["verdict"] in ("PASS", "FAIL"):
                key = tuple(row[k] for k in key_fields)
                groups[key].add(row["verdict"])
        return sum(len(v) > 1 for v in groups.values())

    within_flips = disagreement_count(("case_id", "artifact_id", "evaluator", "setup"), ())
    setup_flips = disagreement_count(("case_id", "artifact_id", "evaluator", "repeat"), ())
    evaluator_flips = disagreement_count(("case_id", "artifact_id", "setup", "repeat"), ())
    by_artifact = defaultdict(list)
    for row in observed:
        by_artifact[row["artifact_id"]].append(row)
    shared = []
    for aid, rows in by_artifact.items():
        oracle = artifacts[aid][1]["oracle"]
        seen = {r["verdict"] for r in rows if r["verdict"] in ("PASS", "FAIL")}
        if oracle in ("PASS", "FAIL") and len(seen) == 1 and all(r["verdict"] in ("PASS", "FAIL") for r in rows) and next(iter(seen)) != oracle:
            shared.append(aid)
    unknown = {case["id"]: sum(r["verdict"] == "UNKNOWN" for r in observed if r["case_id"] == case["id"]) for case in fixture["cases"]}
    missing = {case["id"]: sum(r["verdict"] is None for r in observed if r["case_id"] == case["id"]) for case in fixture["cases"]}
    reversals = sorted(cid for cid in single if single[cid] == ["A>B"] and "B>A" in ranks_by_cell[cid])
    return {
        "schema": "agent-interface/6222-crossed-verdict-candidate-v1",
        "allocation_id": freeze["allocation_id"],
        "main_sha": freeze["main_sha"],
        "fixture_sha256": hashlib.sha256(_canonical(fixture).encode("utf-8")).hexdigest(),
        "observations": observed,
        "reference_rows": reference,
        "reference_deck_pass": all(r["verdict"] == r["oracle"] and r["verdict"] in ("PASS", "FAIL") for r in reference),
        "within_scorer_flip_cells": within_flips,
        "setup_disagreement_cells": setup_flips,
        "evaluator_disagreement_cells": evaluator_flips,
        "one_pass_rankings": single,
        "crossed_rankings": ranks_by_cell,
        "ranking_reversals": reversals,
        "score_intervals": score_table,
        "shared_bias_flags": sorted(shared),
        "shared_bias_is_validity_certificate": False,
        "unknown_rows_by_case": unknown,
        "missing_rows_by_case": missing,
    }


def _validate(document, expected):
    errors = []
    if not isinstance(document, dict):
        return ["document_not_object"]
    if document.get("allocation_id") != expected["allocation_id"]:
        errors.append("allocation_id_mismatch")
    if document.get("main_sha") != expected["main_sha"]:
        errors.append("main_sha_mismatch")
    if _canonical(document) != _canonical(expected):
        errors.append("reconstruction_mismatch")
    return errors


def _mutations(document, expected):
    cases = []
    changed = copy.deepcopy(document)
    changed["allocation_id"] = "CROSS-VERDICT-WRONG-ALLOCATION"
    cases.append(("allocation_id", changed))
    changed = copy.deepcopy(document)
    changed["observations"].pop()
    cases.append(("row_omission", changed))
    changed = copy.deepcopy(document)
    changed["observations"][0]["verdict"] = "FAIL" if changed["observations"][0]["verdict"] != "FAIL" else "PASS"
    cases.append(("verdict_flip", changed))
    changed = copy.deepcopy(document)
    changed["observations"][0]["oracle"] = "FAIL" if changed["observations"][0]["oracle"] != "FAIL" else "PASS"
    cases.append(("oracle_tamper", changed))
    changed = copy.deepcopy(document)
    missing_index = next(i for i, row in enumerate(changed["observations"]) if row["verdict"] is None)
    changed["observations"][missing_index]["verdict"] = "FAIL"
    cases.append(("missingness_launder", changed))
    return [{"mutation": name, "rejected": bool(_validate(candidate, expected))} for name, candidate in cases]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--freeze", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    fixture = json.loads(Path(args.fixture).read_text(encoding="utf-8"))
    freeze = json.loads(Path(args.freeze).read_text(encoding="utf-8"))
    raw = Path(args.candidate).read_bytes()
    candidate = json.loads(raw.decode("utf-8"))
    expected = _expected(fixture, freeze)
    errors = _validate(candidate, expected)
    mutations = _mutations(candidate, expected)
    rejected = sum(m["rejected"] for m in mutations)
    disposition = "PASS_AUDIT_METHOD_SCOPED" if not errors and rejected == len(mutations) else "FAIL_AUDIT_INTEGRITY"
    result = {
        "schema": "agent-interface/6222-crossed-verdict-audit-v1",
        "allocation_id_expected": freeze["allocation_id"],
        "allocation_id_observed": candidate.get("allocation_id"),
        "candidate_sha256": hashlib.sha256(raw).hexdigest(),
        "rows_reconstructed": len(expected["observations"]),
        "errors": errors,
        "mutations": mutations,
        "mutations_rejected": rejected,
        "disposition": disposition,
    }
    out = Path(args.output)
    if out.exists():
        raise FileExistsError(f"output collision: {out}")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"disposition": disposition, "rows": result["rows_reconstructed"], "mutations_rejected": rejected, "errors": errors}, sort_keys=True))
    return 0 if disposition == "PASS_AUDIT_METHOD_SCOPED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
