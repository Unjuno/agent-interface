"""Independent audit v3 of the preserved T2 raw; candidate is never imported."""
import hashlib
import itertools
import json
import sys
from fractions import Fraction
from pathlib import Path

BASE = "a2469a821f4d27d2ec9a1d5d63ed8b81e57f81c3"
IMAGE = "python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9"
FROZEN_INPUT = "724dad606aa4bcea0b8ec47a4d0e45abbb11cc5226843f8ea62304042d691d66"
FROZEN_CANDIDATE = "5610c1aefb0a43f57c880ef08477d57eb4e97111c650c83a350e70979feadf01"


def digest(value):
    wire = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(wire).hexdigest()


def rational(value):
    number = Fraction(value)
    return f"{number.numerator}/{number.denominator}"


def expected_rows(spec):
    result = {}
    evidence = []
    for pair in spec["pairs"]:
        graph = {"pair_id": pair["pair_id"], "nominal": pair["nominal"],
                 "declared_risk": pair["declared_risk"], "family_id": spec["declared_family_id"]}
        graph_digest = digest(graph)
        nominal, declared_loss = Fraction(pair["nominal"]), Fraction(pair["declared_risk"])
        declared_floor = nominal - declared_loss
        hidden_loss = declared_floor + Fraction(spec["hidden_risk_delta"])
        for world, mode in (("complete", "attested_complete"), ("omitted", "unverified_family")):
            latent_losses = [
                declared_bit * declared_loss + hidden_bit * hidden_loss
                for declared_bit, hidden_bit in itertools.product((0, 1), (0, 1))
                if world == "omitted" or hidden_bit == 0
            ]
            true_floor = min(nominal - loss for loss in latent_losses)
            status = ("ROBUST" if declared_floor > 0 else "SENSITIVE") if world == "complete" else "UNIDENTIFIED"
            key = pair["pair_id"] + ":" + mode
            result[key] = {
                "case_id": key,
                "pair_id": pair["pair_id"],
                "mode": mode,
                "declared_family_sha256": graph_digest,
                "declared_worst_margin": rational(declared_floor),
                "decision": status,
                "authority": False,
            }
            evidence.append({
                "case_id": key,
                "world": world,
                "decision": status,
                "declared_only_robust": declared_floor > 0,
                "true_worst_margin": rational(true_floor),
                "reversal": true_floor <= 0,
                "latent_vertex_count": len(latent_losses),
            })

    first = spec["pairs"][0]
    graph = {"pair_id": first["pair_id"], "nominal": first["nominal"],
             "declared_risk": first["declared_risk"], "family_id": spec["declared_family_id"]}
    graph_digest = digest(graph)
    floor = Fraction(first["nominal"]) - Fraction(first["declared_risk"])
    for control in spec["candidate_controls"]:
        key = first["pair_id"] + ":" + control
        result[key] = {
            "case_id": key,
            "pair_id": first["pair_id"],
            "mode": control,
            "declared_family_sha256": graph_digest,
            "declared_worst_margin": rational(floor),
            "decision": "UNIDENTIFIED",
            "authority": False,
        }
    return result, evidence


def audit(spec, raw, input_bytes, candidate_bytes, raw_bytes):
    errors = []
    expected, truth = expected_rows(spec)
    seen = {}
    for row in raw.get("rows", []):
        key = row.get("case_id") if isinstance(row, dict) else None
        if not isinstance(key, str) or key in seen:
            errors.append("invalid_or_duplicate_case_id")
        else:
            seen[key] = row
    if raw.get("schema") != "hidden-cause-sensitivity-t2-raw-v1": errors.append("raw_schema")
    if raw.get("base_main_sha") != BASE: errors.append("base_main_sha")
    if raw.get("input_sha256") != hashlib.sha256(input_bytes).hexdigest() or raw.get("input_sha256") != FROZEN_INPUT: errors.append("input_digest")
    if raw.get("candidate_sha256") != hashlib.sha256(candidate_bytes).hexdigest() or raw.get("candidate_sha256") != FROZEN_CANDIDATE: errors.append("candidate_digest")
    if raw.get("container") != {"image": IMAGE, "platform": "linux/amd64", "network": "none"}: errors.append("container")
    if set(seen) != set(expected): errors.append("case_set")
    for case_id, wanted in expected.items():
        if seen.get(case_id) != wanted: errors.append("row:" + case_id)
    if any(raw.get(name) != 0 for name in ("authority_grants", "network_calls", "model_calls", "gui_input_calls")):
        errors.append("forbidden_activity")

    complete = [row for row in truth if row["world"] == "complete"]
    omitted = [row for row in truth if row["world"] == "omitted"]
    summary = {
        "primary_pairs": len(spec["pairs"]),
        "primary_world_rows": len(truth),
        "control_rows": len(spec["candidate_controls"]),
        "complete_world_robust": sum(row["decision"] == "ROBUST" and Fraction(row["true_worst_margin"]) > 0 for row in complete),
        "unverified_world_unidentified": sum(row["decision"] == "UNIDENTIFIED" for row in omitted),
        "declared_only_false_robust_on_reversal": sum(row["declared_only_robust"] and row["reversal"] for row in omitted),
        "hidden_world_reversals": sum(row["reversal"] for row in omitted),
        "controls_unidentified": sum(seen.get(spec["pairs"][0]["pair_id"] + ":" + mode, {}).get("decision") == "UNIDENTIFIED" for mode in spec["candidate_controls"]),
        "authority_grants": raw.get("authority_grants"),
        "candidate_rows_exact": not errors,
    }
    passed = (
        not errors and summary["complete_world_robust"] == 8
        and summary["unverified_world_unidentified"] == 8
        and summary["declared_only_false_robust_on_reversal"] == 8
        and summary["hidden_world_reversals"] == 8
        and summary["controls_unidentified"] == 4
        and summary["authority_grants"] == 0
    )
    return {
        "schema": "hidden-cause-sensitivity-t2-independent-audit-v3",
        "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "candidate_sha256": hashlib.sha256(candidate_bytes).hexdigest(),
        "input_sha256": hashlib.sha256(input_bytes).hexdigest(),
        "errors": errors,
        "summary": summary,
        "truth_rows": truth,
        "decision": "PASS_T2_SYNTHETIC_SCOPE_GATING" if passed else "FAIL_AUDIT_OR_EXPERIMENT",
        "limits": [
            "Completeness verification is trusted synthetic fixture data only.",
            "Authored rational margins are not probabilities or real causal estimates.",
            "No production safety, live effect, or actuation authority is established.",
        ],
    }


def main():
    root = Path(__file__).parent
    input_bytes = (root / "cases.json").read_bytes()
    candidate_bytes = (root / "candidate.py").read_bytes()
    raw_bytes = Path("/out/raw.json").read_bytes()
    result = audit(json.loads(input_bytes), json.loads(raw_bytes), input_bytes, candidate_bytes, raw_bytes)
    Path("/out/audit-v3.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"decision": result["decision"], "summary": result["summary"], "errors": result["errors"]}, sort_keys=True))
    if result["decision"] != "PASS_T2_SYNTHETIC_SCOPE_GATING":
        sys.exit(1)


if __name__ == "__main__":
    main()
