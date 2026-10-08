#!/usr/bin/env python3
"""Independent reconstruction using explicit branches, not candidate imports."""
import json
import sys


def expected(row):
    candidate, auditor = row.get("candidate_receipt"), row.get("auditor_receipt")
    if row.get("frozen") is not True:
        status = "HOLD_NOT_FROZEN"
    elif candidate is None:
        status = "STOP_OUTPUT_WITHOUT_INVOCATION_RECEIPT" if row.get("raw_present") else "PRE_RUN"
    elif not isinstance(candidate, dict) or candidate.get("exit") != 0 or candidate.get("raw_sha256") != row.get("raw_sha256"):
        status = "HOLD_CANDIDATE_RECEIPT_MISMATCH"
    elif auditor is None:
        status = "CANDIDATE_ONLY"
    elif not isinstance(auditor, dict) or auditor.get("candidate_raw_sha256") != row.get("raw_sha256"):
        status = "HOLD_AUDIT_INPUT_HASH_MISMATCH"
    elif auditor.get("exit") != 0 or auditor.get("errors") != []:
        status = "FAIL_AUDIT"
    else:
        status = "COMPLETE_AUDITED"
    return status


def main(fixture_path, candidate_path, out_path):
    fixture = json.load(open(fixture_path, encoding="utf-8"))
    output = json.load(open(candidate_path, encoding="utf-8"))
    errors = []
    if output.get("allocation_id") != fixture.get("allocation_id"):
        errors.append("allocation_id")
    expected_ids = [row["id"] for row in fixture["states"]]
    got = output.get("rows", [])
    if [item.get("id") for item in got] != expected_ids:
        errors.append("row_identity_or_order")
    for row, item in zip(fixture["states"], got):
        if item.get("candidate_invocations") != (1 if row.get("candidate_receipt") is not None else 0):
            errors.append(row["id"] + ":candidate_count")
        if item.get("auditor_invocations") != (1 if row.get("auditor_receipt") is not None else 0):
            errors.append(row["id"] + ":auditor_count")
        if item.get("status") != expected(row):
            errors.append(row["id"] + ":status")
    result = {"status": "PASS_METHOD_SCOPED" if not errors else "FAIL_AUDIT", "rows_checked": len(got), "errors": errors}
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, sort_keys=True, separators=(",", ":"))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main(*sys.argv[1:]))
