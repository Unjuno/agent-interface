#!/usr/bin/env python3
"""Classify allocation lifecycle evidence; deliberately no filesystem access."""
import json
import sys


def classify(row):
    c, a = row["candidate_receipt"], row["auditor_receipt"]
    if not row["frozen"]:
        return "HOLD_NOT_FROZEN"
    if c is None:
        return "STOP_OUTPUT_WITHOUT_INVOCATION_RECEIPT" if row["raw_present"] else "PRE_RUN"
    if c["exit"] != 0 or c["raw_sha256"] != row["raw_sha256"]:
        return "HOLD_CANDIDATE_RECEIPT_MISMATCH"
    if a is None:
        return "CANDIDATE_ONLY"
    if a["candidate_raw_sha256"] != row["raw_sha256"]:
        return "HOLD_AUDIT_INPUT_HASH_MISMATCH"
    if a["exit"] != 0 or a["errors"]:
        return "FAIL_AUDIT"
    return "COMPLETE_AUDITED"


def main(src, dst):
    data = json.load(open(src, encoding="utf-8"))
    result = {"allocation_id": data["allocation_id"], "rows": [
        {"id": row["id"], "candidate_invocations": int(row["candidate_receipt"] is not None),
         "auditor_invocations": int(row["auditor_receipt"] is not None), "status": classify(row)}
        for row in data["states"]]}
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(result, f, sort_keys=True, separators=(",", ":"))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
