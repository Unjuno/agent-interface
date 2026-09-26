#!/usr/bin/env python3
"""Independent cross-check of immutable Issue #3840 raw.json; stdlib only."""
import base64
import hashlib
import json
import os
from pathlib import Path


def digest(value):
    return hashlib.sha256(value).hexdigest()


def main():
    evidence_path = Path(os.environ["EVIDENCE"])
    out = Path(os.environ["OUT"])
    if not evidence_path.is_file() or not out.is_dir() or any(out.iterdir()):
        raise SystemExit("STOP_INPUT_OR_OUTPUT")
    raw_bytes = evidence_path.read_bytes()
    doc = json.loads(raw_bytes)
    problems = []
    if doc.get("schema") != "issue-3840/newline-frame-raw-v2":
        problems.append("schema")
    if doc.get("base_commit") != os.environ["EXPECTED_COMMIT"]:
        problems.append("base_commit")
    if doc.get("image_ref") != os.environ["EXPECTED_IMAGE"]:
        problems.append("image_ref")
    if doc.get("container_platform") != "linux/amd64":
        problems.append("platform")
    rows = {row.get("case"): row for row in doc.get("rows", [])}
    if set(rows) != {"complete_delivery", "terminal_lf_lost", "request_only_unknown", "occupied_destination"}:
        problems.append("case_set")

    complete = rows.get("complete_delivery", {})
    try:
        accepted = base64.b64decode(complete["accepted_b64"], validate=True)
        delivered = base64.b64decode(complete["delivered_b64"], validate=True)
        parsed = json.loads(delivered)
        if (accepted != delivered or not delivered.endswith(b"\n")
                or complete.get("producer_exit") != 0 or complete.get("dispatch_calls") != 1
                or parsed.get("result", {}).get("status") != "completed"):
            problems.append("complete_control")
    except Exception:
        problems.append("complete_decode")

    trunc = rows.get("terminal_lf_lost", {})
    try:
        accepted = base64.b64decode(trunc["accepted_b64"], validate=True)
        delivered = base64.b64decode(trunc["delivered_b64"], validate=True)
        report_bytes = base64.b64decode(trunc["report_b64"], validate=True)
        report = json.loads(report_bytes)
        naive = json.loads(delivered)
        status = trunc["attempt_status"]
        report_entry = status["files"]["report.json"]
        review = trunc["review"]
        if (accepted[-1:] != b"\n" or delivered != accepted[:-1]
                or delivered.endswith(b"\n") or len(delivered) + 1 != len(accepted)
                or digest(accepted) != trunc.get("accepted_sha256")
                or digest(delivered) != trunc.get("delivered_sha256")
                or digest(report_bytes) != trunc.get("report_sha256")
                or naive.get("result", {}).get("status") != "completed"
                or trunc.get("naive_parse") != "valid_json"
                or trunc.get("naive_claims_completed") is not True
                or trunc.get("frame_valid") is not False
                or trunc.get("producer_exit") != 0 or trunc.get("dispatch_calls") != 1
                or trunc.get("guard_and_recovery_pass") is not True
                or trunc.get("attempt_status_exit") != 0
                or status.get("status") != "report_recorded"
                or status.get("replay_allowed") is not False
                or report_entry.get("state") != "recorded"
                or report_entry.get("sha256") != digest(report_bytes)
                or report_entry.get("value") != report
                or trunc.get("review_exit") != 0
                or review.get("receipt", {}).get("report") != report
                or review.get("receipt", {}).get("source", {}).get("sha256") != digest(report_bytes)
                or review.get("outcome_summary", {}).get("execution_status") != "completed"
                or trunc.get("snapshot_before") != trunc.get("snapshot_after")):
            problems.append("terminal_lf_recovery")
        if not isinstance(trunc.get("snapshot_before"), list):
            problems.append("snapshot_schema")
    except Exception:
        problems.append("terminal_decode")

    unknown = rows.get("request_only_unknown", {})
    status = unknown.get("attempt_status", {})
    if (unknown.get("attempt_status_exit") != 2 or unknown.get("dispatch_calls") != 0
            or status.get("status") != "unknown_or_incomplete"
            or status.get("replay_allowed") is not False):
        problems.append("request_only_control")
    occupied = rows.get("occupied_destination", {})
    sentinels = [f for f in occupied.get("files", []) if f.get("path") == "sentinel"]
    if (occupied.get("producer_exit") != 2 or occupied.get("dispatch_calls") != 0
            or occupied.get("response", {}).get("error") != "REQUEST_PERSISTENCE_FAILED"
            or len(sentinels) != 1 or sentinels[0].get("bytes") != len(b"preserve-me")
            or sentinels[0].get("sha256") != digest(b"preserve-me")):
        problems.append("occupied_control")

    result = {
        "schema": "issue-3840/independent-crosscheck-v2",
        "raw_sha256": digest(raw_bytes),
        "raw_runner_sha256": doc.get("runner_sha256"),
        "raw_auditor_sha256": doc.get("auditor_sha256"),
        "expected_frozen_auditor_sha256": os.environ["EXPECTED_FROZEN_AUDITOR"],
        "frozen_auditor_match": doc.get("auditor_sha256") == os.environ["EXPECTED_FROZEN_AUDITOR"],
        "checks_passed": not problems,
        "problems": problems,
        "formal_decision_recorded": doc.get("formal_decision"),
        "secondary_decision_recorded": doc.get("secondary_decision"),
        "evidence_gate": "HOLD_EVIDENCE_INCOMPLETE",
        "rows": len(rows),
    }
    encoded = json.dumps(result, sort_keys=True, separators=(",", ":")).encode() + b"\n"
    (out / "crosscheck.json").write_bytes(encoded)
    print(encoded.decode(), end="")
    if problems:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
