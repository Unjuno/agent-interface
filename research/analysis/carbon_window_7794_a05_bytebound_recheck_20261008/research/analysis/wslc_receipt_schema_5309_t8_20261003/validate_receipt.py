"""Strict offline validation of the immutable #5309 T7 captured stdout."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


EXPECTED_BYTES = 306
EXPECTED_SHA256 = "604fc18e94e80f6aa941623b8854ffad88043e16e5058db89aa45449ba97489f"
EXPECTED = {
    "authority_grants": 0,
    "errors": [],
    "failed_probe_task_fallback_wrong_target": 27,
    "failed_probe_yield_wrong_target": 0,
    "independent_row_matches": 432,
    "rows": 432,
    "semantic_sha256": "a7bd0adc9485df7161b7ce85c27b1dc58fad71ee2fee9cfe081cc61337b0e193",
    "status": "PASS_T6_INDEPENDENT_FINITE_ORACLE",
    "unique_cases": 432,
}
INTEGER_FIELDS = {
    "authority_grants",
    "failed_probe_task_fallback_wrong_target",
    "failed_probe_yield_wrong_target",
    "independent_row_matches",
    "rows",
    "unique_cases",
}


def validate_document(document: Any) -> dict[str, Any]:
    if type(document) is not dict:
        raise ValueError("receipt_must_be_json_object")
    if set(document) != set(EXPECTED):
        raise ValueError("receipt_key_set_mismatch")
    for key in INTEGER_FIELDS:
        if type(document[key]) is not int:
            raise ValueError(f"receipt_integer_type_mismatch:{key}")
    if type(document["errors"]) is not list:
        raise ValueError("receipt_errors_type_mismatch")
    for key, expected in EXPECTED.items():
        if document[key] != expected or type(document[key]) is not type(expected):
            raise ValueError(f"receipt_value_mismatch:{key}")
    return dict(document)


def validate_bytes(raw: bytes) -> dict[str, Any]:
    if len(raw) != EXPECTED_BYTES:
        raise ValueError("receipt_byte_count_mismatch")
    digest = hashlib.sha256(raw).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError("receipt_sha256_mismatch")
    try:
        document = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("receipt_json_invalid") from exc
    return {
        "input_bytes": len(raw),
        "input_sha256": digest,
        "receipt": validate_document(document),
    }


def build_pass_receipt(raw: bytes) -> dict[str, Any]:
    verified = validate_bytes(raw)
    return {
        "allocation_id": "WSLC-RECEIPT-5309-T8-20261003-01",
        "disposition": "PASS_RETAINED_RECEIPT_SCHEMA_AUDIT",
        "input": {
            "path": "input/audit.stdout.json",
            "bytes": verified["input_bytes"],
            "sha256": verified["input_sha256"],
            "source_pr": 6983,
            "source_git_blob": "588d1816282ab17790faa3a94a939f9fce8d8bc3",
        },
        "observed": verified["receipt"],
        "t7_disposition": "STOP_HOST_RECEIPT_SCHEMA_MISMATCH",
        "t7_schema_note": {
            "frozen_verifier_expected": "failed_probe_yield_fallback_wrong_target",
            "captured_auditor_emitted": "failed_probe_yield_wrong_target",
            "captured_value": 0,
            "t7_verdict_revised": False,
        },
    }


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 2:
        print("usage: validate_receipt.py INPUT OUTPUT", file=sys.stderr)
        return 2
    source, output = (Path(arg) for arg in args)
    try:
        receipt = build_pass_receipt(source.read_bytes())
        encoded = (json.dumps(receipt, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
        with output.open("xb") as stream:
            stream.write(encoded)
    except Exception as exc:
        print(json.dumps({"error": type(exc).__name__, "message": str(exc)}, sort_keys=True), file=sys.stderr)
        return 1
    print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
