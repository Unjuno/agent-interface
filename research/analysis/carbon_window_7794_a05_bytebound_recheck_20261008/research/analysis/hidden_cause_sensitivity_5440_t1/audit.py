from __future__ import annotations

import argparse
import copy
import hashlib
import itertools
import json
from fractions import Fraction
from pathlib import Path

AUDIT_SCHEMA = "hidden-cause-sensitivity-t1-independent-audit-v1"


def q(value: str) -> Fraction:
    if not isinstance(value, str):
        raise TypeError("rational values must be strings")
    return Fraction(value)


def enc(value: Fraction) -> str:
    return f"{value.numerator}/{value.denominator}"


def audit_data(data: dict, input_bytes: bytes, raw: dict, candidate_bytes: bytes) -> tuple[list[str], dict]:
    errors: list[str] = []
    if data.get("schema") != "hidden-cause-sensitivity-t1-input-v1":
        errors.append("input_schema")
    if raw.get("schema") != "hidden-cause-sensitivity-t1-raw-v1":
        errors.append("raw_schema")
    actual_input_hash = hashlib.sha256(input_bytes).hexdigest()
    if raw.get("input_sha256") != actual_input_hash:
        errors.append("input_hash")
    if actual_input_hash != "02ba32c8f1a4c8ab3d65e7fa138f459602a22a8ab2224859d9b916315a14f20e":
        errors.append("frozen_input_hash")
    actual_candidate_hash = hashlib.sha256(candidate_bytes).hexdigest()
    if raw.get("candidate_sha256") != actual_candidate_hash:
        errors.append("candidate_hash")
    if actual_candidate_hash != "ec6adc9966d439a247f30ccb50b42f1185f7522393e60f2b65daabaf36e1a680":
        errors.append("frozen_candidate_hash")
    if raw.get("base_main_sha") != "ffb0d43b5f0408011a3f70223da43d4aa3f27fe4":
        errors.append("base_main_sha")
    if raw.get("container") != {
        "image": "python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9",
        "platform": "linux/amd64",
        "network": "none",
    }:
        errors.append("container_identity")

    claims = data.get("claims", [])
    expected: dict[str, dict] = {}
    for claim in claims:
        case_id = claim.get("case_id")
        if not isinstance(case_id, str) or case_id in expected:
            errors.append("duplicate_or_invalid_case_id")
            continue
        try:
            evidence = claim["evidence"]
            evidence_ids = [row["evidence_id"] for row in evidence]
            if len(set(evidence_ids)) != len(evidence_ids) or any(row.get("provenance") != "ATTESTED" for row in evidence):
                raise ValueError("evidence integrity")
            nominal = sum((q(row["margin"]) for row in evidence), Fraction())
            cause_rows = claim["latent_causes"]
            cause_ids = [row["cause_id"] for row in cause_rows]
            if len(set(cause_ids)) != len(cause_ids):
                raise ValueError("duplicate cause")
            bounds = {row["cause_id"]: q(row["bound"]) for row in cause_rows}
            if any(value < 0 for value in bounds.values()):
                raise ValueError("negative bound")
            edges = claim["influence_edges"]
            if any(edge["cause_id"] not in bounds or edge["evidence_id"] not in evidence_ids for edge in edges):
                raise ValueError("orphan edge")
            if any(q(edge["adverse_weight"]) < 0 for edge in edges):
                raise ValueError("negative weight")

            # Independent algorithm: enumerate every vertex of the latent cube.
            worst = None
            for bits in itertools.product((False, True), repeat=len(cause_ids)):
                latent = {
                    cause_id: (bounds[cause_id] if active else Fraction())
                    for cause_id, active in zip(cause_ids, bits)
                }
                loss = sum(
                    (q(edge["adverse_weight"]) * latent[edge["cause_id"]] for edge in edges),
                    Fraction(),
                )
                score = nominal - loss
                worst = score if worst is None else min(worst, score)
            if worst is None:
                worst = nominal
            status = "ROBUST" if worst > 0 else ("SENSITIVE" if nominal > 0 else "ABSTAIN")
            grouped: dict[str, Fraction] = {key: Fraction() for key in bounds}
            for edge in edges:
                grouped[edge["cause_id"]] += q(edge["adverse_weight"])
            expected[case_id] = {
                "case_id": case_id,
                "matched_pair": claim["matched_pair"],
                "nominal_margin": enc(nominal),
                "worst_case_margin": enc(worst),
                "cause_risks": {
                    key: enc(grouped[key] * bounds[key]) for key in sorted(grouped)
                },
                "status": status,
            }
        except (KeyError, TypeError, ValueError, ZeroDivisionError):
            errors.append(f"invalid_graph:{case_id}")

    rows = raw.get("rows")
    if not isinstance(rows, list):
        errors.append("rows_not_list")
        rows = []
    actual: dict[str, dict] = {}
    for row in rows:
        case_id = row.get("case_id") if isinstance(row, dict) else None
        if not isinstance(case_id, str) or case_id in actual:
            errors.append("duplicate_or_invalid_raw_case_id")
            continue
        actual[case_id] = row
    if set(actual) != set(expected):
        errors.append("case_set")
    for case_id in set(actual) & set(expected):
        if actual[case_id] != expected[case_id]:
            errors.append(f"row_mismatch:{case_id}")

    n = len(expected)
    cap = n // 4
    margin_order = sorted(expected.values(), key=lambda row: (q(row["nominal_margin"]), row["case_id"]))
    margin_abstain = sorted(row["case_id"] for row in margin_order[:cap])
    sensitivity_abstain = sorted(
        case_id for case_id, row in expected.items() if row["status"] == "SENSITIVE"
    )
    margin_unsafe = sum(
        1 for case_id, row in expected.items()
        if case_id not in margin_abstain and q(row["worst_case_margin"]) <= 0
    )
    sensitivity_unsafe = sum(
        1 for case_id, row in expected.items()
        if case_id not in sensitivity_abstain and q(row["worst_case_margin"]) <= 0
    )
    summary = {
        "claim_count": n,
        "nominal_commit_count": sum(1 for row in expected.values() if q(row["nominal_margin"]) > 0),
        "robust_commit_count": sum(1 for row in expected.values() if row["status"] == "ROBUST"),
        "sensitivity_abstention_count": len(sensitivity_abstain),
        "sensitivity_abstention_rate": enc(Fraction(len(sensitivity_abstain), n)) if n else "0/1",
        "matched_budget": {
            "fraction": "1/4",
            "abstention_cap": cap,
            "margin_only_abstained_ids": margin_abstain,
            "sensitivity_abstained_ids": sensitivity_abstain,
            "margin_only_residual_unsafe_admissions": margin_unsafe,
            "sensitivity_residual_unsafe_admissions": sensitivity_unsafe,
        },
    }
    for key, value in summary.items():
        if raw.get(key) != value:
            errors.append(f"summary_mismatch:{key}")
    gate = (
        n == 16 and summary["nominal_commit_count"] == 16
        and summary["sensitivity_abstention_count"] == 4
        and sensitivity_unsafe == 0 and margin_unsafe >= 1
    )
    if not gate:
        errors.append("preregistered_decision_gate")
    return errors, summary


def mutation_controls(data: dict, input_bytes: bytes, raw: dict, candidate_bytes: bytes) -> dict:
    mutations = {}
    changed = copy.deepcopy(raw)
    changed["rows"][0]["status"] = "SENSITIVE"
    mutations["status_flip"] = changed
    changed = copy.deepcopy(raw)
    changed["rows"].pop()
    mutations["omitted_row"] = changed
    changed = copy.deepcopy(raw)
    changed["sensitivity_abstention_count"] += 1
    mutations["summary_count"] = changed
    changed = copy.deepcopy(raw)
    changed["matched_budget"]["sensitivity_abstained_ids"] = ["forged"]
    mutations["forged_abstention"] = changed
    rejected = {}
    for name, damaged in mutations.items():
        errs, _ = audit_data(data, input_bytes, damaged, candidate_bytes)
        rejected[name] = bool(errs)
    return rejected


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--raw", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    input_bytes = args.input.read_bytes()
    raw_bytes = args.raw.read_bytes()
    data = json.loads(input_bytes)
    raw = json.loads(raw_bytes)
    candidate_bytes = args.input.with_name("candidate.py").read_bytes()
    auditor_bytes = Path(__file__).read_bytes()
    errors, summary = audit_data(data, input_bytes, raw, candidate_bytes)
    mutations = mutation_controls(data, input_bytes, raw, candidate_bytes)
    if not all(mutations.values()):
        errors.append("mutation_control_accepted")
    result = {
        "schema": AUDIT_SCHEMA,
        "disposition": "PASS_T1_SYNTHETIC_SENSITIVITY_GATE" if not errors else "FAIL_INDEPENDENT_AUDIT",
        "input_sha256": hashlib.sha256(input_bytes).hexdigest(),
        "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "candidate_sha256": hashlib.sha256(candidate_bytes).hexdigest(),
        "auditor_sha256": hashlib.sha256(auditor_bytes).hexdigest(),
        "graph_algorithm": "exhaustive_vertices",
        "vertices_evaluated": sum(2 ** len(row.get("latent_causes", [])) for row in data["claims"]),
        "mutation_controls": mutations,
        "summary": summary,
        "errors": errors,
    }
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "disposition": result["disposition"],
        "vertices_evaluated": result["vertices_evaluated"],
        "mutation_controls": mutations,
        "errors": errors,
    }, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
