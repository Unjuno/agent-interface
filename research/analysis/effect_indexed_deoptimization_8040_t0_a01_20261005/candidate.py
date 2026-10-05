"""Candidate semantic-cursor reconstruction; emits no executable action."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

EXPECTED_MAPPING_SHA256 = "febe115614f020bac5e3d75d95ab4c26fc0b13bd81062b4ee1d35c8dc4137a5d"
KNOWN_OPERATIONS = ("prepare_record", "commit_record", "send_receipt")
VALID_STATES = {"VERIFIED", "NO_EFFECT", "UNKNOWN"}


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def hold(case_id: str, reason: str, verified_prefix: list[str] | None = None) -> dict:
    return {
        "case_id": case_id,
        "disposition": "YIELD_UNKNOWN",
        "generic_cursor": None,
        "verified_prefix": list(verified_prefix or []),
        "reason": reason,
        "execution_authorized": False,
        "authority_extended": False,
        "completion_claim": False,
    }


def classify(public: dict, case: dict) -> dict:
    case_id = case.get("case_id", "<missing>")
    mapping = public.get("mapping")
    if not isinstance(mapping, dict) or hashlib.sha256(canonical_bytes(mapping)).hexdigest() != EXPECTED_MAPPING_SHA256:
        return hold(case_id, "MAP_HASH_OR_SHAPE_INVALID")
    if public.get("mapping_sha256") != EXPECTED_MAPPING_SHA256:
        return hold(case_id, "MAP_BINDING_INVALID")
    if tuple(mapping.get("semantic_operations", ())) != KNOWN_OPERATIONS:
        return hold(case_id, "SEMANTIC_OPERATION_SET_INVALID")
    if case.get("observation_generation") != public.get("current_generation"):
        return hold(case_id, "STALE_OBSERVATION_GENERATION")
    point = mapping.get("safepoints", {}).get(case.get("specialized_pc"))
    if not isinstance(point, dict):
        return hold(case_id, "SAFEPOINT_MISSING")
    if point.get("phase") not in {"between", "inside"}:
        return hold(case_id, "SAFEPOINT_PHASE_INVALID")
    cursor = point.get("semantic_cursor")
    if not isinstance(cursor, int) or cursor < 0 or cursor > len(KNOWN_OPERATIONS):
        return hold(case_id, "GENERIC_CURSOR_INVALID")
    evidence = case.get("effect_receipts")
    if not isinstance(evidence, list) or len(evidence) != cursor:
        return hold(case_id, "PREFIX_RECEIPT_COUNT_INVALID")
    verified = []
    for index, row in enumerate(evidence):
        if not isinstance(row, dict):
            return hold(case_id, "RECEIPT_SHAPE_INVALID", verified)
        operation = KNOWN_OPERATIONS[index]
        if (row.get("operation_id") != operation
                or row.get("observation_generation") != public.get("current_generation")
                or row.get("verifier_role") != "independent_effect_receipt"
                or not isinstance(row.get("receipt_id"), str)
                or not row.get("receipt_id")
                or row.get("state") not in VALID_STATES):
            return hold(case_id, "RECEIPT_BINDING_INVALID", verified)
        state = row["state"]
        if state == "UNKNOWN":
            return hold(case_id, "PREFIX_EFFECT_UNKNOWN", verified)
        if state == "NO_EFFECT":
            if point["phase"] != "between":
                return hold(case_id, "MAP_EFFECT_STATE_CONTRADICTION", verified)
            return {
                "case_id": case_id,
                "disposition": "RESOLUTION_REQUIRED_AT_CURSOR",
                "generic_cursor": index,
                "verified_prefix": verified,
                "reason": "KNOWN_NO_EFFECT_REQUIRES_GENERIC_RESOLUTION",
                "execution_authorized": False,
                "authority_extended": False,
                "completion_claim": False,
            }
        verified.append(operation)
    if point["phase"] != "between":
        return hold(case_id, "PARTIAL_SPECIALIZED_OPERATION", verified)
    disposition = "CURSOR_AT_END_UNVERIFIED" if cursor == len(KNOWN_OPERATIONS) else "READY_AT_CURSOR"
    return {
        "case_id": case_id,
        "disposition": disposition,
        "generic_cursor": cursor,
        "verified_prefix": verified,
        "reason": "ALL_PREFIX_EFFECTS_VERIFIED" if cursor else "NO_PREFIX_EFFECTS",
        "execution_authorized": False,
        "authority_extended": False,
        "completion_claim": False,
    }


def run(public: dict) -> dict:
    return {
        "schema": "unjuno.issue8040.deopt_candidate.v1",
        "allocation": "UNJUNO-8040-EFFECT-INDEXED-DEOPT-T0-A01-20261005",
        "rows": [classify(public, case) for case in public.get("cases", [])],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    public = json.loads(Path(args.input).read_text(encoding="utf-8"))
    result = run(public)
    Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"rows": len(result["rows"]), "disposition": "CANDIDATE_COMPLETE"}, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
