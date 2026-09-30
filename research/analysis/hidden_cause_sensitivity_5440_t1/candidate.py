from __future__ import annotations

import argparse
import hashlib
import json
import os
from fractions import Fraction
from pathlib import Path

SCHEMA = "hidden-cause-sensitivity-t1-raw-v1"
BUDGET = Fraction(1, 4)


def q(value: str) -> Fraction:
    if not isinstance(value, str):
        raise TypeError("rational values must be strings")
    return Fraction(value)


def enc(value: Fraction) -> str:
    return f"{value.numerator}/{value.denominator}"


def compute(data: dict, input_bytes: bytes, source_bytes: bytes, image: str, platform: str) -> dict:
    if data.get("schema") != "hidden-cause-sensitivity-t1-input-v1":
        raise ValueError("unexpected input schema")
    claims = data.get("claims")
    if not isinstance(claims, list) or len(claims) != 16:
        raise ValueError("exactly 16 frozen claims required")
    ids = [row.get("case_id") for row in claims]
    if len(set(ids)) != len(ids) or any(not isinstance(x, str) for x in ids):
        raise ValueError("unique case ids required")

    rows = []
    for claim in claims:
        evidence = claim["evidence"]
        evidence_ids = [item["evidence_id"] for item in evidence]
        if len(evidence_ids) != len(set(evidence_ids)):
            raise ValueError("duplicate evidence id")
        if any(item.get("provenance") != "ATTESTED" for item in evidence):
            raise ValueError("provenance-only comparison requires attested inputs")
        nominal = sum((q(item["margin"]) for item in evidence), Fraction())
        causes = {item["cause_id"]: q(item["bound"]) for item in claim["latent_causes"]}
        if len(causes) != len(claim["latent_causes"]):
            raise ValueError("duplicate latent cause")
        by_cause = {cause_id: Fraction() for cause_id in causes}
        for edge in claim["influence_edges"]:
            cause_id = edge["cause_id"]
            if cause_id not in causes or edge["evidence_id"] not in evidence_ids:
                raise ValueError("edge references unknown node")
            weight = q(edge["adverse_weight"])
            if weight < 0:
                raise ValueError("adverse weight must be non-negative")
            by_cause[cause_id] += weight
        cause_risks = {cause_id: by_cause[cause_id] * bound for cause_id, bound in causes.items()}
        worst = nominal - sum(cause_risks.values(), Fraction())
        status = "ROBUST" if worst > 0 else ("SENSITIVE" if nominal > 0 else "ABSTAIN")
        rows.append({
            "case_id": claim["case_id"],
            "matched_pair": claim["matched_pair"],
            "nominal_margin": enc(nominal),
            "worst_case_margin": enc(worst),
            "cause_risks": {key: enc(cause_risks[key]) for key in sorted(cause_risks)},
            "status": status,
        })

    n = len(rows)
    allowance = (n * BUDGET.numerator) // BUDGET.denominator
    margin_only = sorted(rows, key=lambda r: (q(r["nominal_margin"]), r["case_id"]))[:allowance]
    margin_only_ids = sorted(r["case_id"] for r in margin_only)
    sensitivity_ids = sorted(r["case_id"] for r in rows if r["status"] == "SENSITIVE")
    margin_unsafe = sum(1 for r in rows if r["case_id"] not in margin_only_ids and q(r["worst_case_margin"]) <= 0)
    sensitivity_unsafe = sum(1 for r in rows if r["case_id"] not in sensitivity_ids and q(r["worst_case_margin"]) <= 0)
    return {
        "schema": SCHEMA,
        "base_main_sha": os.environ.get("EXPERIMENT_BASE_SHA", "UNSET"),
        "container": {"image": image, "platform": platform, "network": "none"},
        "input_sha256": hashlib.sha256(input_bytes).hexdigest(),
        "candidate_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "claim_count": n,
        "nominal_commit_count": sum(1 for r in rows if q(r["nominal_margin"]) > 0),
        "robust_commit_count": sum(1 for r in rows if r["status"] == "ROBUST"),
        "sensitivity_abstention_count": len(sensitivity_ids),
        "sensitivity_abstention_rate": enc(Fraction(len(sensitivity_ids), n)),
        "matched_budget": {
            "fraction": enc(BUDGET),
            "abstention_cap": allowance,
            "margin_only_abstained_ids": margin_only_ids,
            "sensitivity_abstained_ids": sensitivity_ids,
            "margin_only_residual_unsafe_admissions": margin_unsafe,
            "sensitivity_residual_unsafe_admissions": sensitivity_unsafe,
        },
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    input_bytes = args.input.read_bytes()
    result = compute(
        json.loads(input_bytes), input_bytes, Path(__file__).read_bytes(),
        os.environ["EXPERIMENT_IMAGE"], os.environ["EXPERIMENT_PLATFORM"],
    )
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in (
        "schema", "claim_count", "robust_commit_count",
        "sensitivity_abstention_count", "sensitivity_abstention_rate", "matched_budget",
    )}, sort_keys=True))


if __name__ == "__main__":
    main()
