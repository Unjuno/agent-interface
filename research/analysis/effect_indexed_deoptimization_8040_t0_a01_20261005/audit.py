"""Independent raw-only audit of Issue #8040 T0 A01."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

OPS = ("prepare_record", "commit_record", "send_receipt")
EXPECTED_MAP = {
    "macro_id": "macro-three-effect-v1",
    "semantic_operations": list(OPS),
    "specialized_instructions": [
        {"pc": "pc0", "operation": None, "phase": "between"},
        {"pc": "pc1", "operation": "prepare_record", "phase": "after"},
        {"pc": "pc1_mid", "operation": "commit_record", "phase": "inside"},
        {"pc": "pc2", "operation": "commit_record", "phase": "after"},
        {"pc": "pc2_mid", "operation": "send_receipt", "phase": "inside"},
        {"pc": "pc3", "operation": "send_receipt", "phase": "after"},
    ],
    "safepoints": {
        "pc0": {"semantic_cursor": 0, "phase": "between"},
        "pc1": {"semantic_cursor": 1, "phase": "between"},
        "pc1_mid": {"semantic_cursor": 1, "phase": "inside", "operation": "commit_record"},
        "pc2": {"semantic_cursor": 2, "phase": "between"},
        "pc2_mid": {"semantic_cursor": 2, "phase": "inside", "operation": "send_receipt"},
        "pc3": {"semantic_cursor": 3, "phase": "between"},
    },
}


def canon(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def digest(value: object) -> str:
    return hashlib.sha256(canon(value)).hexdigest()


def expected_for(public: dict, truth: dict, case: dict) -> dict:
    case_id = case.get("case_id", "<missing>")
    def yield_row(reason: str, verified_prefix: list[str] | None = None) -> dict:
        return {"case_id": case_id, "disposition": "YIELD_UNKNOWN", "generic_cursor": None,
                "verified_prefix": list(verified_prefix or []), "reason": reason, "execution_authorized": False,
                "authority_extended": False, "completion_claim": False}
    mapping = public.get("mapping")
    truth_case = truth.get("cases", {}).get(case_id)
    if mapping != EXPECTED_MAP or digest(mapping) != truth.get("expected_mapping_sha256"):
        return yield_row("MAP_HASH_OR_SHAPE_INVALID")
    if public.get("mapping_sha256") != truth.get("expected_mapping_sha256"):
        return yield_row("MAP_BINDING_INVALID")
    if not isinstance(truth_case, dict):
        return yield_row("TRUTH_ROW_MISSING")
    if case.get("observation_generation") != truth_case.get("current_generation"):
        return yield_row("STALE_OBSERVATION_GENERATION")
    point = EXPECTED_MAP["safepoints"].get(case.get("specialized_pc"))
    if point is None:
        return yield_row("SAFEPOINT_MISSING")
    if point["phase"] not in {"between", "inside"}:
        return yield_row("SAFEPOINT_PHASE_INVALID")
    cursor = point["semantic_cursor"]
    receipts = case.get("effect_receipts")
    if not isinstance(receipts, list) or len(receipts) != cursor:
        return yield_row("PREFIX_RECEIPT_COUNT_INVALID")
    actual = truth_case.get("actual_effect_states", {})
    verified = []
    for index, receipt in enumerate(receipts):
        op = OPS[index]
        if not isinstance(receipt, dict):
            return yield_row("RECEIPT_SHAPE_INVALID", verified)
        state = receipt.get("state")
        if (receipt.get("operation_id") != op
                or receipt.get("observation_generation") != truth_case.get("current_generation")
                or receipt.get("verifier_role") != "independent_effect_receipt"
                or not receipt.get("receipt_id")
                or state not in {"VERIFIED", "NO_EFFECT", "UNKNOWN"}
                or actual.get(op) != state):
            return yield_row("RECEIPT_BINDING_INVALID", verified)
        if state == "UNKNOWN":
            return yield_row("PREFIX_EFFECT_UNKNOWN", verified)
        if state == "NO_EFFECT":
            if point["phase"] != "between":
                return yield_row("MAP_EFFECT_STATE_CONTRADICTION", verified)
            return {"case_id": case_id, "disposition": "RESOLUTION_REQUIRED_AT_CURSOR",
                    "generic_cursor": index, "verified_prefix": verified,
                    "reason": "KNOWN_NO_EFFECT_REQUIRES_GENERIC_RESOLUTION", "execution_authorized": False,
                    "authority_extended": False, "completion_claim": False}
        verified.append(op)
    if point["phase"] != "between":
        return yield_row("PARTIAL_SPECIALIZED_OPERATION", verified)
    return {"case_id": case_id,
            "disposition": "CURSOR_AT_END_UNVERIFIED" if cursor == len(OPS) else "READY_AT_CURSOR",
            "generic_cursor": cursor, "verified_prefix": verified,
            "reason": "ALL_PREFIX_EFFECTS_VERIFIED" if cursor else "NO_PREFIX_EFFECTS",
            "execution_authorized": False, "authority_extended": False,
            "completion_claim": False}


def reconstruct(public: dict, truth: dict) -> list[dict]:
    return [expected_for(public, truth, case) for case in public.get("cases", [])]


def audit_document(public: dict, truth: dict, output: dict) -> dict:
    expected = reconstruct(public, truth)
    observed = output.get("rows", []) if isinstance(output, dict) else []
    errors = []
    if output.get("schema") != "unjuno.issue8040.deopt_candidate.v1":
        errors.append("candidate schema mismatch")
    if output.get("allocation") != truth.get("allocation"):
        errors.append("allocation mismatch")
    if observed != expected:
        errors.append("candidate rows differ from independent raw reconstruction")
    if len(observed) != len(public.get("cases", [])):
        errors.append("candidate row count mismatch")
    for row in observed:
        if row.get("execution_authorized") is not False or row.get("authority_extended") is not False:
            errors.append("candidate emits or extends authority")
        if row.get("completion_claim") is not False:
            errors.append("candidate claims task completion")
    mutation_controls = {}
    mutations = {}
    dropped = copy.deepcopy(output)
    dropped["rows"] = dropped["rows"][:-1]
    mutations["drop_case"] = dropped
    changed_cursor = copy.deepcopy(output)
    for row in changed_cursor["rows"]:
        if row["disposition"] == "READY_AT_CURSOR" and row["generic_cursor"]:
            row["generic_cursor"] = 0
            break
    mutations["change_cursor"] = changed_cursor
    authorize = copy.deepcopy(output)
    authorize["rows"][0]["execution_authorized"] = True
    mutations["authorize_action"] = authorize
    complete = copy.deepcopy(output)
    complete["rows"][-1]["completion_claim"] = True
    mutations["claim_completion"] = complete
    inject = copy.deepcopy(output)
    inject["rows"][0]["verified_prefix"] = [OPS[0]]
    mutations["inject_verified_prefix"] = inject
    unyield = copy.deepcopy(output)
    for row in unyield["rows"]:
        if row["disposition"] == "YIELD_UNKNOWN":
            row["disposition"] = "READY_AT_CURSOR"
            row["generic_cursor"] = 0
            break
    mutations["continue_unknown"] = unyield
    for name, mutation in mutations.items():
        mutation_errors = []
        mutation_rows = mutation.get("rows", [])
        if mutation_rows != expected or len(mutation_rows) != len(public.get("cases", [])):
            mutation_errors.append("does not match independent reconstruction")
        if any(row.get("execution_authorized") is not False for row in mutation_rows):
            mutation_errors.append("execution authority mutation detected")
        if any(row.get("completion_claim") is not False for row in mutation_rows):
            mutation_errors.append("completion mutation detected")
        mutation_controls[name] = {"rejected": bool(mutation_errors), "errors": mutation_errors}
    disposition = "PASS_METHOD_SCOPED" if not errors and all(x["rejected"] for x in mutation_controls.values()) else "FAIL_METHOD"
    return {
        "schema": "unjuno.issue8040.deopt_audit.v1",
        "disposition": disposition,
        "scope": "finite authored semantic-deoptimization model only",
        "case_count": len(expected),
        "reconstructed_rows": expected,
        "independent_errors": errors,
        "mutation_controls": mutation_controls,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--truth", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    public = json.loads(Path(args.input).read_text(encoding="utf-8"))
    truth = json.loads(Path(args.truth).read_text(encoding="utf-8"))
    candidate = json.loads(Path(args.candidate).read_text(encoding="utf-8"))
    result = audit_document(public, truth, candidate)
    Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"disposition": result["disposition"], "cases": result["case_count"], "errors": len(result["independent_errors"])}, sort_keys=True))
    return 0 if result["disposition"] == "PASS_METHOD_SCOPED" else 1

if __name__ == "__main__":
    raise SystemExit(main())
