"""Validate the structured receipt emitted by the retained T6 auditor."""

import json
import sys


EXPECTED = {
    "status": "PASS_T6_INDEPENDENT_FINITE_ORACLE",
    "rows": 432,
    "unique_cases": 432,
    "independent_row_matches": 432,
    "semantic_sha256": "a7bd0adc9485df7161b7ce85c27b1dc58fad71ee2fee9cfe081cc61337b0e193",
    "failed_probe_task_fallback_wrong_target": 27,
    "failed_probe_yield_fallback_wrong_target": 0,
    "authority_grants": 0,
    "errors": [],
}


def validate_receipt(receipt):
    if not isinstance(receipt, dict):
        raise ValueError("receipt must be a JSON object")
    for field, expected in EXPECTED.items():
        actual = receipt.get(field)
        if type(actual) is not type(expected) or actual != expected:
            raise ValueError(f"unexpected {field}: {actual!r}")
    return {
        "status": "PASS_HOST_RECEIPT_AUDIT",
        "rows": EXPECTED["rows"],
        "unique_cases": EXPECTED["unique_cases"],
        "independent_row_matches": EXPECTED["independent_row_matches"],
        "semantic_sha256": EXPECTED["semantic_sha256"],
        "failed_probe_task_fallback_wrong_target": EXPECTED[
            "failed_probe_task_fallback_wrong_target"
        ],
        "failed_probe_yield_fallback_wrong_target": EXPECTED[
            "failed_probe_yield_fallback_wrong_target"
        ],
        "authority_grants": 0,
        "errors": [],
    }


def main(receipt_path):
    with open(receipt_path, "r", encoding="utf-8") as stream:
        receipt = json.load(stream)
    print(json.dumps(validate_receipt(receipt), sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: verify_receipt.py AUDITOR_STDOUT_JSON")
    main(sys.argv[1])

