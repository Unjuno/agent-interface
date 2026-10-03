"""Independently validate the immutable WSLc receipt captured by T7."""

import hashlib
import json
import sys


EXPECTED_INPUT_SHA256 = (
    "604fc18e94e80f6aa941623b8854ffad88043e16e5058db89aa45449ba97489f"
)

EXPECTED = {
    "status": "PASS_T6_INDEPENDENT_FINITE_ORACLE",
    "rows": 432,
    "unique_cases": 432,
    "independent_row_matches": 432,
    "semantic_sha256": "a7bd0adc9485df7161b7ce85c27b1dc58fad71ee2fee9cfe081cc61337b0e193",
    "failed_probe_task_fallback_wrong_target": 27,
    "failed_probe_yield_wrong_target": 0,
    "authority_grants": 0,
    "errors": [],
}


def validate_receipt(receipt):
    if not isinstance(receipt, dict):
        raise ValueError("receipt must be a JSON object")
    if set(receipt) != set(EXPECTED):
        raise ValueError("unexpected schema keys")
    for field, expected in EXPECTED.items():
        actual = receipt[field]
        if type(actual) is not type(expected) or actual != expected:
            raise ValueError(f"unexpected {field}: {actual!r}")
    return {
        "status": "PASS_RETAINED_RECEIPT_SCHEMA_AUDIT",
        "input_sha256": EXPECTED_INPUT_SHA256,
        "rows": EXPECTED["rows"],
        "unique_cases": EXPECTED["unique_cases"],
        "independent_row_matches": EXPECTED["independent_row_matches"],
        "semantic_sha256": EXPECTED["semantic_sha256"],
        "failed_probe_task_fallback_wrong_target": EXPECTED[
            "failed_probe_task_fallback_wrong_target"
        ],
        "failed_probe_yield_wrong_target": EXPECTED[
            "failed_probe_yield_wrong_target"
        ],
        "authority_grants": 0,
        "errors": [],
    }


def validate_receipt_bytes(raw_bytes):
    if not isinstance(raw_bytes, bytes):
        raise ValueError("receipt input must be bytes")
    actual_sha256 = hashlib.sha256(raw_bytes).hexdigest()
    if actual_sha256 != EXPECTED_INPUT_SHA256:
        raise ValueError(f"unexpected input SHA-256: {actual_sha256}")
    try:
        receipt = json.loads(raw_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("captured receipt is not UTF-8 JSON") from exc
    return validate_receipt(receipt)


def main(receipt_path):
    with open(receipt_path, "rb") as stream:
        result = validate_receipt_bytes(stream.read())
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: verify_receipt.py AUDIT_STDOUT_JSON")
    main(sys.argv[1])

