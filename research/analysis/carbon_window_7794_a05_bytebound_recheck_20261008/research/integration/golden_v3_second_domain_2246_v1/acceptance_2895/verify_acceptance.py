"""Acceptance-scoped verifier for immutable GTK allocation evidence.

This verifier never upgrades preflight evidence to formal acceptance. It fails
closed when raw event traces are referenced only by path names.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

CASES = (
    "USEFUL_EFFECT",
    "UNAVAILABLE_BEFORE_INPUT",
    "GUARDED_REFUSAL",
    "ACCEPTED_NO_EFFECT",
    "PARTIAL_COLLATERAL",
    "STALE_REPAIR",
    "AMBIGUOUS_DELIVERY",
    "TERMINAL_CLEANUP_FAILURE",
)


def verify(summary: dict) -> dict:
    rows = summary.get("rows", [])
    errors = []
    if [r.get("formal_receipt", {}).get("case") for r in rows] != list(CASES):
        errors.append("fixed_order")
    if summary.get("scorer_matches") is not True:
        errors.append("scorer")
    if summary.get("formal_receipt_order_ok") is not True:
        errors.append("receipt_order")
    for row in rows:
        receipt = row.get("formal_receipt", {})
        if not isinstance(row.get("raw_events"), list):
            errors.append(f"raw_event_trace_missing:{row.get('case')}")
        if not isinstance(receipt.get("input_ledger"), list):
            errors.append(f"input_ledger:{row.get('case')}")
        if not isinstance(receipt.get("cleanup"), dict):
            errors.append(f"cleanup:{row.get('case')}")
    decision = "PASS_FORMAL_2606_ACCEPTANCE" if not errors else "STOP_MISSING_RAW_RECEIPT_BUNDLE"
    return {"decision": decision, "errors": errors, "scope": "acceptance-scoped immutable evidence verification"}


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: verify_acceptance.py SUMMARY_JSON")
    result = verify(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["decision"] == "PASS_FORMAL_2606_ACCEPTANCE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
