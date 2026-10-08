"""Independent v2 audit: recomputes the finite worlds without candidate code."""
import hashlib
import itertools
import json
import sys
from fractions import Fraction
from pathlib import Path


BASE = "a2469a821f4d27d2ec9a1d5d63ed8b81e57f81c3"
IMAGE = "python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9"


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def fraction(text):
    return Fraction(text)


def rational(value):
    return f"{value.numerator}/{value.denominator}"


def inspect(raw, data, input_bytes, candidate_bytes, raw_bytes):
    faults = []
    if raw.get("schema") != "hidden-cause-sensitivity-t2-raw-v1": faults.append("schema")
    if raw.get("base_main_sha") != BASE: faults.append("frozen_base")
    if raw.get("input_sha256") != hashlib.sha256(input_bytes).hexdigest(): faults.append("input_digest")
    if raw.get("input_sha256") != "724dad606aa4bcea0b8ec47a4d0e45abbb11cc5226843f8ea62304042d691d66": faults.append("frozen_input_digest")
    if raw.get("candidate_sha256") != hashlib.sha256(candidate_bytes).hexdigest(): faults.append("candidate_digest")
    if raw.get("candidate_sha256") != "5610c1aefb0a43f57c880ef08477d57eb4e97111c650c83a350e70979feadf01": faults.append("frozen_candidate_digest")
    if raw.get("container") != {"image": IMAGE, "platform": "linux/amd64", "network": "none"}: faults.append("container")
    if any(raw.get(field) != 0 for field in ("authority_grants", "network_calls", "model_calls", "gui_input_calls")):
        faults.append("forbidden_activity_count")

    records = raw.get("rows")
    if not isinstance(records, list):
        faults.append("rows_type")
        records = []

    by_id = {}
    for row in records:
        key = row.get("case_id") if isinstance(row, dict) else None
        if not isinstance(key, str) or key in by_id:
            faults.append("duplicate_or_bad_case_id")
        else:
            by_id[key] = row

    expected_ids = set()
    truth_rows = []
    for pair in data["pairs"]:
        graph = {"pair_id": pair["pair_id"], "nominal": pair["nominal"],
                 "declared_risk": pair["declared_risk"], "family_id": data["declared_family_id"]}
        graph_hash = hashlib.sha256(canonical(graph)).hexdigest()
        margin = fraction(pair["nominal"])
        declared_loss = fraction(pair["declared_risk"])
        declared_floor = margin - declared_loss
        hidden_loss = declared_floor + fraction(data["hidden_risk_delta"])

        # Enumerate latent corners separately for the closed and omitted-family worlds.
        closed_world = [margin - bit * declared_loss for bit in (0, 1)]
        omitted_world = [margin - d * declared_loss - h * hidden_loss
                         for d, h in itertools.product((0, 1), (0, 1))]
        closed_floor, omitted_floor = min(closed_world), min(omitted_world)
        for mode, wanted, world_floor in (
            ("attested_complete", "ROBUST" if declared_floor > 0 else "SENSITIVE", closed_floor),
            ("unverified_family", "UNIDENTIFIED", omitted_floor),
        ):
            key = pair["pair_id"] + ":" + mode
            expected_ids.add(key)
            expected_row = {
                "case_id": key,
                "pair_id": pair["pair_id"],
                "mode": mode,
                "declared_family_sha256": graph_hash,
                "declared_worst_margin": rational(declared_floor),
                "decision": wanted,
                "authority": False,
            }
            observed = by_id.get(key)
            if observed != expected_row:
                faults.append("row:" + key)
            truth_rows.append({
                "case_id": key,
                "decision": wanted,
                "declared_only_decision": "ROBUST" if declared_floor > 0 else "SENSITIVE",
                "actual_worst_margin": rational(world_floor),
                "reversed": world_floor <= 0,
                "latent_vertices": len(closed_world) if mode == "attested_complete" else len(omitted_world),
            })

    pair = data["pairs"][0]
    graph = {"pair_id": pair["pair_id"], "nominal": pair["nominal"],
             "declared_risk": pair["declared_risk"], "family_id": data["declared_family_id"]}
    graph_hash = hashlib.sha256(canonical(graph)).hexdigest()
    declared_floor = fraction(pair["nominal"]) - fraction(pair["declared_risk"])
    for mode in data["candidate_controls"]:
        key = pair["pair_id"] + ":" + mode
        expected_ids.add(key)
        digest = "0" * 64 if mode == "wrong_scope_digest" else graph_hash
        expected_row = {"case_id": key, "pair_id": pair["pair_id"], "mode": mode,
                        "declared_family_sha256": graph_hash,
                        "declared_worst_margin": rational(declared_floor),
                        "decision": "UNIDENTIFIED", "authority": False}
        if by_id.get(key) != expected_row:
            faults.append("control:" + key)

    if set(by_id) != expected_ids: faults.append("case_set")
    complete = [row for row in truth_rows if row["mode"] == "attested_complete"]
    hidden = [row for row in truth_rows if row["mode"] == "unverified_family"]
    summary = {
        "primary_rows": len(truth_rows),
        "control_rows": len(data["candidate_controls"]),
        "exact_candidate_match": len(faults) == 0,
        "complete_world_robust": sum(row["decision"] == "ROBUST" and Fraction(row["actual_worst_margin"]) > 0 for row in complete),
        "complete_world_count": len(complete),
        "unverified_worlds_unidentified": sum(row["decision"] == "UNIDENTIFIED" for row in hidden),
        "unverified_world_count": len(hidden),
        "declared_only_false_robust_on_reversal": sum(row["declared_only_decision"] == "ROBUST" and row["reversed"] for row in hidden),
        "hidden_world_reversals": sum(row["reversed"] for row in hidden),
        "controls_unidentified": sum(by_id.get(pair["pair_id"] + ":" + mode, {}).get("decision") == "UNIDENTIFIED" for mode in data["candidate_controls"]),
        "authority_grants": raw.get("authority_grants"),
    }
    passed = (
        not faults
        and summary["complete_world_robust"] == 8
        and summary["complete_world_count"] == 8
        and summary["unverified_worlds_unidentified"] == 8
        and summary["unverified_world_count"] == 8
        and summary["declared_only_false_robust_on_reversal"] == 8
        and summary["hidden_world_reversals"] == 8
        and summary["controls_unidentified"] == 4
        and summary["authority_grants"] == 0
    )
    return {
        "schema": "hidden-cause-sensitivity-t2-independent-audit-v2",
        "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "candidate_sha256": hashlib.sha256(candidate_bytes).hexdigest(),
        "input_sha256": hashlib.sha256(input_bytes).hexdigest(),
        "errors": faults,
        "summary": summary,
        "rows": truth_rows,
        "decision": "PASS_T2_SYNTHETIC_SCOPE_GATING" if passed else "FAIL_AUDIT_OR_EXPERIMENT",
        "limits": [
            "The completeness attestation is trusted synthetic fixture data, not cryptographic or real-world proof.",
            "Exact authored rational margins are not calibrated probabilities or causal estimates.",
            "The result establishes no production safety, live effect, or actuation authority.",
        ],
    }


def main():
    root = Path(__file__).parent
    input_bytes = (root / "cases.json").read_bytes()
    candidate_bytes = (root / "candidate.py").read_bytes()
    raw_bytes = Path("/out/raw.json").read_bytes()
    output = inspect(json.loads(raw_bytes), json.loads(input_bytes), input_bytes, candidate_bytes, raw_bytes)
    Path("/out/audit-v2.json").write_text(json.dumps(output, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"decision": output["decision"], "summary": output["summary"], "errors": output["errors"]}, sort_keys=True))
    if output["decision"] != "PASS_T2_SYNTHETIC_SCOPE_GATING":
        sys.exit(1)


if __name__ == "__main__":
    main()
