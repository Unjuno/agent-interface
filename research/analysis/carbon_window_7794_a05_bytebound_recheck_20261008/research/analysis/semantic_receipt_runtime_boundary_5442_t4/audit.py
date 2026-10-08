#!/usr/bin/env python3
"""Raw-only audit of the retained mechanical receipt contract probe."""
from __future__ import annotations

import json
import sys
from pathlib import Path


EXPECTED_REQUEST_FIELDS = [
    "command_id", "invariant_manifest_id", "binding", "lease", "actions",
]
EXPECTED_EFFECT_FIELDS = [
    "command_id", "invariant_manifest_id", "observed_ns", "status", "evidence_digest",
]
EXPECTED_ABSENT = [
    "intent_hash", "goal_predicate_hash", "target_namespace", "pre_state_version",
    "post_state_version", "observer_id", "dependency_provenance", "freshness",
    "execution_receipt_ref",
]
EXPECTED_BLOBS = {
    "runtime/kernel/contracts.py": "3d24fb5b28ae7812c71c6c1fedd3439d1473f0b8",
    "runtime/kernel/lifecycle.py": "0735f1b2bc4f8c8c66a16cd0687a8b631c99f0b3",
}


def main(path: str) -> None:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    errors = []
    if raw.get("schema") != "semantic_receipt_runtime_boundary_probe_v1":
        errors.append("schema")
    if raw.get("freeze_commit") != "d00ffdd74cde6c7f113cb03382be853879d5cb65":
        errors.append("freeze_commit")
    if raw.get("source_blobs") != EXPECTED_BLOBS:
        errors.append("source_blobs")
    if raw.get("request_fields") != EXPECTED_REQUEST_FIELDS:
        errors.append("request_fields")
    if raw.get("effect_receipt_fields") != EXPECTED_EFFECT_FIELDS:
        errors.append("effect_receipt_fields")
    if raw.get("semantic_fields_absent") != EXPECTED_ABSENT:
        errors.append("semantic_fields_absent")
    if raw.get("outcome") != {
        "stage": "verified", "effect_verified": True, "release_verified": True,
    }:
        errors.append("outcome")
    if raw.get("scope") != (
        "mechanical contract only; no application effect or semantic success asserted"
    ):
        errors.append("scope")
    print(json.dumps({
        "status": "PASS_SCOPED_MECHANICAL_BOUNDARY" if not errors else "FAIL_AUDIT",
        "errors": errors,
        "raw_file": str(Path(path)),
    }, sort_keys=True, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: audit.py RAW_JSON")
    main(sys.argv[1])
