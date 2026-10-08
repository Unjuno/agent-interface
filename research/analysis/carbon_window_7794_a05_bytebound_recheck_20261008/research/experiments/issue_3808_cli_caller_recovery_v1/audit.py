#!/usr/bin/env python3
"""Independent raw-only audit for Issue #3808; does not import runner/runtime."""
import base64
import hashlib
import json
import os
from pathlib import Path


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    evidence = Path(os.environ.get("EVIDENCE", "/evidence/raw.json")).resolve()
    out = Path(os.environ.get("OUT", "/out")).resolve()
    if not evidence.is_file() or not out.is_dir() or any(out.iterdir()):
        raise SystemExit("STOP_AUDIT_INPUT_OR_OUTPUT")
    raw_bytes = evidence.read_bytes()
    doc = json.loads(raw_bytes)
    errors = []
    rows = doc.get("rows")
    expected = {"complete_delivery", "downstream_truncation_recovery", "request_only_unknown", "occupied_destination"}
    if not isinstance(rows, list) or {r.get("case") for r in rows if isinstance(r, dict)} != expected or len(rows) != 4:
        errors.append("row_inventory")
    indexed = {r.get("case"): r for r in rows if isinstance(r, dict)}
    complete = indexed.get("complete_delivery", {})
    try:
        accepted_full = base64.b64decode(complete["accepted_b64"], validate=True)
        delivered_full = base64.b64decode(complete["delivered_b64"], validate=True)
        parsed_full = json.loads(delivered_full)
        if complete.get("producer_exit") != 0 or accepted_full != delivered_full or parsed_full["result"]["status"] != "completed" or complete.get("dispatch_calls") != 1:
            errors.append("complete_delivery_contract")
    except Exception:
        errors.append("complete_delivery_decode")
    trunc = indexed.get("downstream_truncation_recovery", {})
    try:
        accepted = base64.b64decode(trunc["accepted_b64"], validate=True)
        delivered = base64.b64decode(trunc["delivered_b64"], validate=True)
        report = base64.b64decode(trunc["report_b64"], validate=True)
        if (trunc.get("producer_exit") != 0 or trunc.get("caller_parse") != "invalid_or_incomplete"
                or len(delivered) >= len(accepted) or accepted[:len(delivered)] != delivered
                or sha(accepted) != trunc.get("accepted_sha256") or sha(delivered) != trunc.get("delivered_sha256")
                or sha(report) != trunc.get("report_sha256") or trunc.get("dispatch_calls") != 1
                or trunc.get("attempt_status_exit") != 0 or trunc.get("attempt_status", {}).get("status") != "report_recorded"
                or trunc.get("attempt_status", {}).get("replay_allowed") is not False
                or trunc.get("review_exit") != 0 or trunc.get("review", {}).get("outcome_summary", {}).get("execution_status") != "completed"
                or trunc.get("snapshot_before_recovery") != trunc.get("snapshot_after_recovery")):
            errors.append("truncation_recovery_contract")
        parsed_report = json.loads(report)
        if parsed_report.get("status") != "returned" or parsed_report.get("result", {}).get("status") != "completed":
            errors.append("retained_report_semantics")
        try:
            json.loads(delivered)
            errors.append("truncated_response_parsed")
        except (UnicodeDecodeError, json.JSONDecodeError):
            pass
    except Exception:
        errors.append("truncation_recovery_decode")
    unknown = indexed.get("request_only_unknown", {})
    ustatus = unknown.get("attempt_status", {})
    if unknown.get("attempt_status_exit") != 2 or ustatus.get("status") != "unknown_or_incomplete" or ustatus.get("replay_allowed") is not False:
        errors.append("unknown_attempt_contract")
    occupied = indexed.get("occupied_destination", {})
    if occupied.get("producer_exit") != 2 or occupied.get("dispatch_calls") != 0 or occupied.get("response", {}).get("error") != "REQUEST_PERSISTENCE_FAILED":
        errors.append("occupied_destination_contract")
    result = {"schema": "issue-3808/independent-audit-v1", "raw_sha256": sha(raw_bytes),
              "decision": "PASS_AUDIT_CALLER_RECOVERY_SCOPED" if not errors else "FAIL_AUDIT_CALLER_RECOVERY",
              "errors": errors, "rows": len(rows) if isinstance(rows, list) else None}
    encoded = json.dumps(result, sort_keys=True, separators=(",", ":")).encode() + b"\n"
    (out / "audit.json").write_bytes(encoded)
    print(encoded.decode(), end="")
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
