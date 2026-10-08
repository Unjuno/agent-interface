#!/usr/bin/env python3
"""Independent raw-only auditor for Issue #3834."""

import base64
import hashlib
import json
import sys


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def audit(raw):
    rows = {row["case"]: row for row in raw["rows"]}
    errors = []
    if raw.get("allocation") != "issue-3834-jsonl-terminal-lf-orbstack-v1":
        errors.append("allocation")
    if raw.get("base_commit") != "c215b11fc9609ec02810a22317c926374f399858":
        errors.append("base_commit")
    if set(rows) != {"complete_delivery", "terminal_lf_removed", "invalid_prefix",
                     "request_only_unknown", "occupied_destination"}:
        errors.append("case_set")
    full = rows.get("complete_delivery", {})
    edge = rows.get("terminal_lf_removed", {})
    invalid = rows.get("invalid_prefix", {})
    complete_bytes = base64.b64decode(full.get("accepted_b64", ""), validate=True)
    accepted = base64.b64decode(edge.get("accepted_b64", ""), validate=True)
    delivered = base64.b64decode(edge.get("delivered_b64", ""), validate=True)
    report = base64.b64decode(edge.get("report_b64", ""), validate=True)
    if (not complete_bytes.endswith(b"\n") or sha256(complete_bytes) != full.get("accepted_sha256")
            or full.get("producer_exit") != 0 or full.get("dispatch_calls") != 1
            or full.get("delivered_sha256") != full.get("accepted_sha256")):
        errors.append("complete_bytes")
    if (not accepted.endswith(b"\n") or delivered != accepted[:-1]
            or edge.get("removed_bytes") != 1
            or edge.get("producer_exit") != 0
            or sha256(accepted) != edge.get("accepted_sha256")
            or sha256(delivered) != edge.get("delivered_sha256")):
        errors.append("terminal_lf_binding")
    try:
        parsed = json.loads(delivered)
        if parsed.get("result", {}).get("status") != "completed":
            errors.append("parser_control_payload")
    except (UnicodeDecodeError, json.JSONDecodeError):
        errors.append("parser_control_invalid")
    if edge.get("parser_only") != "valid_json_false_completion_risk":
        errors.append("parser_only_control")
    if edge.get("framing_aware_complete") is not False:
        errors.append("framing_gate")
    if edge.get("dispatch_calls") != 1:
        errors.append("dispatch_count")
    if edge.get("attempt_status", {}).get("replay_allowed") is not False:
        errors.append("replay_disabled")
    if (edge.get("attempt_status_exit") != 0
            or edge.get("attempt_status", {}).get("status") != "report_recorded"):
        errors.append("attempt_status")
    if edge.get("review", {}).get("outcome_summary", {}).get("execution_status") != "completed":
        errors.append("review_recovery")
    report_status = edge.get("attempt_status", {}).get("files", {}).get("report.json", {})
    if report_status.get("sha256") != edge.get("report_sha256"):
        errors.append("status_report_binding")
    if (report_status.get("state") != "recorded"
            or edge.get("review", {}).get("receipt", {}).get("report") != report_status.get("value")):
        errors.append("recovered_report_content")
    if edge.get("review_exit") != 0:
        errors.append("review_exit")
    if edge.get("snapshot_before") != edge.get("snapshot_after"):
        errors.append("recovery_mutated_attempt")
    if sha256(report) != edge.get("report_sha256"):
        errors.append("retained_report_hash")
    if full.get("dispatch_calls") != 1 or full.get("json_status") != "valid_json":
        errors.append("complete_control")
    bad = base64.b64decode(invalid.get("delivered_b64", ""), validate=True)
    if (invalid.get("json_status") != "invalid_json" or invalid.get("dispatch_calls") != 1
            or invalid.get("producer_exit") != 0):
        errors.append("invalid_prefix_control")
    try:
        json.loads(bad)
        errors.append("invalid_prefix_parsed")
    except (UnicodeDecodeError, json.JSONDecodeError):
        pass
    unknown = rows.get("request_only_unknown", {})
    if unknown.get("status_exit") != 2 or unknown.get("status", {}).get("replay_allowed") is not False:
        errors.append("unknown_control")
    occupied = rows.get("occupied_destination", {})
    if occupied.get("exit") != 2 or occupied.get("dispatch_calls") != 0:
        errors.append("occupied_control")
    return {"decision": "PASS_FRAMING_GUARD_SCOPED" if not errors else "HOLD_EVIDENCE_INCOMPLETE",
            "rows": len(raw["rows"]), "errors": errors,
            "accepted_bytes": len(accepted), "delivered_bytes": len(delivered),
            "accepted_sha256": sha256(accepted), "delivered_sha256": sha256(delivered),
            "report_sha256": sha256(report)}


if __name__ == "__main__":
    result = audit(json.load(sys.stdin))
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
