#!/usr/bin/env python3
"""Independent, strict audit for the Issue #3188 formal-02 truth table.

This successor does not replace either historical independent auditor. It binds
named controls to exact values and rejects non-Boolean JSON field values.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import pathlib
from typing import Any

FIELDS = (
    "physical_task_effect_endpoint",
    "task_effect_contract",
    "matched_arm",
    "arm_bound_audit",
    "terminal_integrity",
)
SCHEMA = "map01-recovery-entry-gate-3008-v2"
RAW_SHA256 = "8460a9ca79611929cbd6d2f6930067a06c6f177e7da3287ad07d1b7f483cb324"
SOURCE_HASHES = {
    "run.py": "e104bf12925ef7878e7972c768cb19ecfdfe699303667bebf0ee6a0276f05822",
    "audit.py": "72a5f6dcffff0e9d3a5e2daa58937bb4ab440ca789d824f183f168abc57e458d",
}
CONTROL_BITS = (
    ("missing_receipt", (True, True, True, True, False)),
    ("stale_binding", (True, True, False, True, True)),
    ("unknown_boundary", (False, True, True, True, True)),
    ("cleanup_failure", (True, True, True, True, False)),
    ("corrupt_recomputation", (True, True, True, False, True)),
)


def classify(row: dict[str, Any]) -> str:
    return "AUTHORIZE" if all(row.get(field) is True for field in FIELDS) else "HOLD"


def expected_vectors() -> list[dict[str, Any]]:
    rows = []
    for bits in itertools.product((False, True), repeat=len(FIELDS)):
        row = dict(zip(FIELDS, bits))
        row["decision"] = classify(row)
        rows.append(row)
    return rows


def expected_controls() -> list[dict[str, Any]]:
    rows = []
    for name, bits in CONTROL_BITS:
        row = dict(zip(FIELDS, bits))
        row["name"] = name
        row["decision"] = classify(row)
        rows.append(row)
    return rows


def structure_errors(data: Any) -> list[str]:
    errors: list[str] = []
    if type(data) is not dict or set(data) != {"schema", "fields", "vectors", "controls"}:
        return ["top-level schema mismatch"]
    if data["schema"] != SCHEMA or data["fields"] != list(FIELDS):
        errors.append("schema identity/order mismatch")

    vectors = data["vectors"]
    expected_v = expected_vectors()
    if type(vectors) is not list or len(vectors) != len(expected_v):
        errors.append("vector count/type mismatch")
    else:
        for index, (row, expected) in enumerate(zip(vectors, expected_v)):
            if type(row) is not dict or set(row) != set(FIELDS) | {"decision"}:
                errors.append(f"vector schema mismatch at {index}")
                continue
            if any(type(row[field]) is not bool for field in FIELDS):
                errors.append(f"vector Boolean type mismatch at {index}")
                continue
            if type(row["decision"]) is not str or row != expected:
                errors.append(f"vector value/decision mismatch at {index}")

    controls = data["controls"]
    expected_c = expected_controls()
    if type(controls) is not list or len(controls) != len(expected_c):
        errors.append("control count/type mismatch")
    else:
        for index, (row, expected) in enumerate(zip(controls, expected_c)):
            if type(row) is not dict or set(row) != set(FIELDS) | {"name", "decision"}:
                errors.append(f"control schema mismatch at {index}")
                continue
            if any(type(row[field]) is not bool for field in FIELDS):
                errors.append(f"control Boolean type mismatch at {index}")
                continue
            if type(row["name"]) is not str or type(row["decision"]) is not str:
                errors.append(f"control identity/decision type mismatch at {index}")
                continue
            # All field values have exact bool types before equality comparison.
            if row != expected:
                errors.append(f"control identity/value/decision mismatch at {index}")

    return errors


def audit(raw_bytes: bytes, source_dir: str | pathlib.Path) -> dict[str, Any]:
    errors: list[str] = []
    raw_digest = hashlib.sha256(raw_bytes).hexdigest()
    if raw_digest != RAW_SHA256:
        errors.append("formal raw SHA-256 mismatch")
    try:
        data = json.loads(raw_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        data = None
        errors.append(f"invalid raw JSON: {type(exc).__name__}")
    errors.extend(structure_errors(data))

    source_dir = pathlib.Path(source_dir)
    source_digests = {}
    for filename, expected in SOURCE_HASHES.items():
        try:
            digest = hashlib.sha256((source_dir / filename).read_bytes()).hexdigest()
        except OSError as exc:
            digest = None
            errors.append(f"candidate source unavailable: {filename}: {type(exc).__name__}")
        source_digests[filename] = digest
        if digest != expected:
            errors.append(f"candidate source SHA-256 mismatch: {filename}")

    vectors = data.get("vectors", []) if type(data) is dict else []
    controls = data.get("controls", []) if type(data) is dict else []
    summary = {
        "rows": len(vectors) + len(controls) if type(vectors) is list and type(controls) is list else None,
        "vectors": len(vectors) if type(vectors) is list else None,
        "authorize": sum(type(row) is dict and row.get("decision") == "AUTHORIZE" for row in vectors)
        if type(vectors) is list else None,
        "current": "HOLD",
        "controls": sum(type(row) is dict and row.get("decision") == "HOLD" for row in controls)
        if type(controls) is list else None,
    }
    if summary != {"rows": 37, "vectors": 32, "authorize": 1, "current": "HOLD", "controls": 5}:
        errors.append("summary mismatch")

    return {
        "status": "PASS_AUDIT_V3" if not errors else "FAIL_AUDIT_V3",
        "errors": errors,
        "raw_sha256": raw_digest,
        "source_sha256": source_digests,
        "summary": summary,
    }
