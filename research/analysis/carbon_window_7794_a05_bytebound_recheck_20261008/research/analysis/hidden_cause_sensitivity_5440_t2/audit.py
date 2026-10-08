"""Raw-only exact oracle for T2; intentionally does not import candidate.py."""
import hashlib
import itertools
import json
import sys
from fractions import Fraction
from pathlib import Path


def canon(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def q(value):
    return Fraction(value)


def enc(value):
    return f"{value.numerator}/{value.denominator}"


def expected(data):
    rows = []
    for pair in data["pairs"]:
        graph = {
            "pair_id": pair["pair_id"],
            "nominal": pair["nominal"],
            "declared_risk": pair["declared_risk"],
            "family_id": data["declared_family_id"],
        }
        digest = hashlib.sha256(canon(graph)).hexdigest()
        declared = q(pair["nominal"]) - q(pair["declared_risk"])
        hidden_risk = declared + q(data["hidden_risk_delta"])
        # Independent exhaustive enumeration of declared and audit-only hidden
        # binary causes. Candidate never receives the hidden cause or this truth.
        declared_vertices = [Fraction(0), q(pair["declared_risk"])]
        hidden_vertices = [Fraction(0), hidden_risk]
        for mode, decision in (("attested_complete", "ROBUST" if declared > 0 else "SENSITIVE"),
                               ("unverified_family", "UNIDENTIFIED")):
            full_world_margins = [q(pair["nominal"]) - d - h
                                  for d, h in itertools.product(
                                      declared_vertices,
                                      [Fraction(0)] if mode == "attested_complete" else hidden_vertices,
                                  )]
            actual_worst = min(full_world_margins)
            rows.append({
                "case_id": pair["pair_id"] + ":" + mode,
                "pair_id": pair["pair_id"],
                "mode": mode,
                "declared_family_sha256": digest,
                "declared_worst_margin": enc(declared),
                "decision": decision,
                "authority": False,
                "audit_only_truth": {
                    "actual_worst_margin": enc(actual_worst),
                    "reversal": actual_worst <= 0,
                    "hidden_cause_in_world": mode == "unverified_family",
                    "vertices": len(full_world_margins),
                },
            })

    pair = data["pairs"][0]
    graph = {"pair_id": pair["pair_id"], "nominal": pair["nominal"],
             "declared_risk": pair["declared_risk"], "family_id": data["declared_family_id"]}
    digest = hashlib.sha256(canon(graph)).hexdigest()
    declared = q(pair["nominal"]) - q(pair["declared_risk"])
    for mode in data["candidate_controls"]:
        rows.append({
            "case_id": pair["pair_id"] + ":" + mode,
            "pair_id": pair["pair_id"],
            "mode": mode,
            "declared_family_sha256": "0" * 64 if mode == "wrong_scope_digest" else digest,
            "declared_worst_margin": enc(declared),
            "decision": "UNIDENTIFIED",
            "authority": False,
            "audit_only_truth": {"control_rejected": True},
        })
    return rows


def main():
    root = Path(__file__).parent
    data_bytes = (root / "cases.json").read_bytes()
    candidate_bytes = (root / "candidate.py").read_bytes()
    raw_bytes = Path("/out/raw.json").read_bytes()
    data = json.loads(data_bytes)
    raw = json.loads(raw_bytes)
    errors = []
    if raw.get("schema") != "hidden-cause-sensitivity-t2-raw-v1": errors.append("raw_schema")
    if raw.get("base_main_sha") != "bde4e1d8a3bedfa16aefbb993a816fb3b0f65c92": errors.append("base_main_sha")
    if raw.get("input_sha256") != hashlib.sha256(data_bytes).hexdigest(): errors.append("input_hash")
    if raw.get("candidate_sha256") != hashlib.sha256(candidate_bytes).hexdigest(): errors.append("candidate_hash")
    if raw.get("container") != {"image": "python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9", "platform": "linux/amd64", "network": "none"}: errors.append("container_identity")
    actual_rows = raw.get("rows")
    expected_rows = expected(data)
    if not isinstance(actual_rows, list) or len(actual_rows) != len(expected_rows):
        errors.append("row_count")
        actual_rows = []
    for i, (actual, wanted) in enumerate(itertools.zip_longest(actual_rows, expected_rows)):
        if actual != {k: v for k, v in wanted.items() if k != "audit_only_truth"}:
            errors.append(f"candidate_row_{i}")
    truth = [r["audit_only_truth"] for r in expected_rows[:16]]
    reversals = sum(row["reversal"] for row in truth)
    hidden_false_robust = sum(
        q(data["pairs"][(i - 1) // 2]["nominal"])
        - q(data["pairs"][(i - 1) // 2]["declared_risk"]) > 0
        and expected_rows[i]["audit_only_truth"]["reversal"]
        for i in range(1, 16, 2)
    )
    coverage_abstentions = sum(r["decision"] == "UNIDENTIFIED" for r in expected_rows[:16])
    summary = {
        "primary_rows": 16,
        "control_rows": len(expected_rows) - 16,
        "exact_candidate_rows": len(errors) == 0,
        "declared_only_false_robust_on_hidden_rows": hidden_false_robust,
        "coverage_gate_unidentified_rows": coverage_abstentions,
        "audit_only_reversal_rows": reversals,
        "mutation_controls_rejected": all(r["decision"] == "UNIDENTIFIED" for r in expected_rows[16:]),
    }
    audit = {
        "schema": "hidden-cause-sensitivity-t2-independent-audit-v1",
        "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "errors": errors,
        "summary": summary,
        "decision": "PASS_T2_SYNTHETIC_SCOPE_GATING" if not errors and reversals == 8 and hidden_false_robust == 8 and coverage_abstentions == 8 else "FAIL",
        "limits": ["The complete-family attestation is a trusted synthetic fixture input, not cryptographic proof or a real-world completeness guarantee.",
                   "Latent risks and margins are exact authored toy values, not calibrated probabilities.",
                   "No real causal identification, production safety, or actuation authority is established."],
    }
    Path("/out/audit.json").write_text(json.dumps(audit, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"decision": audit["decision"], "summary": summary, "errors": errors}))
    if errors or audit["decision"] != "PASS_T2_SYNTHETIC_SCOPE_GATING":
        sys.exit(1)


if __name__ == "__main__":
    main()
