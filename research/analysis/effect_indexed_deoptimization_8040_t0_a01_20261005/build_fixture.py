"""Deterministically build the public trace and independent truth sidecar."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OPERATIONS = ["prepare_record", "commit_record", "send_receipt"]
GENERATION = "surface-g7"


def expected_mapping() -> dict:
    return {
        "macro_id": "macro-three-effect-v1",
        "semantic_operations": OPERATIONS,
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


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def receipt(operation: str, state: str, suffix: str, generation: str = GENERATION) -> dict:
    return {
        "operation_id": operation,
        "state": state,
        "observation_generation": generation,
        "verifier_role": "independent_effect_receipt",
        "receipt_id": f"receipt-{suffix}",
    }


def build() -> tuple[dict, dict]:
    mapping = expected_mapping()
    mapping_sha = hashlib.sha256(canonical_bytes(mapping)).hexdigest()
    rows = [
        ("start_before_effects", "pc0", GENERATION, []),
        ("one_verified_prefix", "pc1", GENERATION, [receipt(OPERATIONS[0], "VERIFIED", "01")]),
        ("known_no_effect_pending", "pc1", GENERATION, [receipt(OPERATIONS[0], "NO_EFFECT", "02")]),
        ("unknown_first_effect", "pc1", GENERATION, [receipt(OPERATIONS[0], "UNKNOWN", "03")]),
        ("unknown_after_verified_prefix", "pc2", GENERATION, [receipt(OPERATIONS[0], "VERIFIED", "04"), receipt(OPERATIONS[1], "UNKNOWN", "05")]),
        ("two_verified_prefix", "pc2", GENERATION, [receipt(OPERATIONS[0], "VERIFIED", "06"), receipt(OPERATIONS[1], "VERIFIED", "07")]),
        ("stale_generation", "pc1", "surface-g6", [receipt(OPERATIONS[0], "VERIFIED", "08")]),
        ("missing_map_entry", "pc99", GENERATION, []),
        ("inside_one_to_many_lowering", "pc1_mid", GENERATION, [receipt(OPERATIONS[0], "VERIFIED", "09")]),
        ("misbound_receipt", "pc1", GENERATION, [receipt(OPERATIONS[1], "VERIFIED", "10")]),
        ("end_of_program_is_not_success", "pc3", GENERATION, [receipt(OPERATIONS[0], "VERIFIED", "11"), receipt(OPERATIONS[1], "VERIFIED", "12"), receipt(OPERATIONS[2], "VERIFIED", "13")]),
        ("extra_unreached_receipt", "pc1", GENERATION, [receipt(OPERATIONS[0], "VERIFIED", "14"), receipt(OPERATIONS[1], "VERIFIED", "15")]),
    ]
    cases = []
    truths = {}
    for case_id, pc, observed_generation, evidence in rows:
        cases.append({
            "case_id": case_id,
            "specialized_pc": pc,
            "observation_generation": observed_generation,
            "effect_receipts": evidence,
        })
        truths[case_id] = {
            "actual_effect_states": {r["operation_id"]: r["state"] for r in evidence},
            "current_generation": GENERATION,
        }
    public = {
        "schema": "unjuno.issue8040.deopt_public.v1",
        "macro_id": mapping["macro_id"],
        "current_generation": GENERATION,
        "mapping": mapping,
        "mapping_sha256": mapping_sha,
        "cases": cases,
    }
    truth = {
        "schema": "unjuno.issue8040.deopt_truth.v1",
        "allocation": "UNJUNO-8040-EFFECT-INDEXED-DEOPT-T0-A01-20261005",
        "expected_mapping_sha256": mapping_sha,
        "cases": truths,
        "expected_case_count": len(cases),
    }
    return public, truth


def main() -> None:
    public, truth = build()
    (ROOT / "public_trace.json").write_bytes(canonical_bytes(public) + b"\n")
    (ROOT / "truth_sidecar.json").write_bytes(canonical_bytes(truth) + b"\n")
    print(json.dumps({"cases": len(public["cases"]), "mapping_sha256": public["mapping_sha256"]}, sort_keys=True))

if __name__ == "__main__":
    main()
