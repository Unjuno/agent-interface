#!/usr/bin/env python3
"""Independent raw-only auditor for Issue #3840; imports no project modules."""
import base64
import hashlib
import json
import os
from pathlib import Path


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    source = Path(os.environ.get("SOURCE", "/source")).resolve()
    evidence = Path(os.environ.get("EVIDENCE", "/evidence/raw.json")).resolve()
    out = Path(os.environ.get("OUT", "/out")).resolve()
    if not evidence.is_file() or not out.is_dir() or any(out.iterdir()):
        raise SystemExit("STOP_AUDIT_INPUT_OR_OUTPUT")
    raw_bytes = evidence.read_bytes()
    doc = json.loads(raw_bytes)
    errors = []
    if doc.get("schema") != "issue-3840/newline-frame-raw-v2":
        errors.append("schema")
    if doc.get("allocation") != "issue3814-jsonl-frame-02":
        errors.append("allocation")
    if doc.get("base_commit") != os.environ.get("EXPECTED_COMMIT"):
        errors.append("base_commit")
    if doc.get("runner_sha256") != os.environ.get("EXPECTED_RUNNER_SHA256"):
        errors.append("runner_sha256")
    if doc.get("auditor_sha256") != os.environ.get("EXPECTED_AUDITOR_SHA256"):
        errors.append("auditor_sha256")
    if doc.get("runner_sha256") != os.environ.get("EXPECTED_RUNNER_SHA256"):
        errors.append("runner_sha256")
    if doc.get("image_ref") != os.environ.get("IMAGE_REF") or doc.get("container_platform") != "linux/amd64":
        errors.append("image_or_platform")

    recorded_sources = doc.get("source_sha256")
    if not isinstance(recorded_sources, list) or not recorded_sources:
        errors.append("source_inventory")
    else:
        expected_paths = {
            path.relative_to(source).as_posix()
            for root_name in ("runtime/cli_v1", "runtime/motor_state_v1", "runtime/selector_v1")
            for path in (source / root_name).rglob("*.py")
        }
        recorded_paths = [row.get("path") for row in recorded_sources if isinstance(row, dict)]
        if len(recorded_paths) != len(recorded_sources) or set(recorded_paths) != expected_paths:
            errors.append("source_inventory_mismatch")
        seen = set()
        for row in recorded_sources:
            try:
                rel = row["path"]
                if (rel in seen or rel not in expected_paths or Path(rel).is_absolute()
                        or ".." in Path(rel).parts):
                    errors.append("source_path_inventory")
                    continue
                seen.add(rel)
                data = (source / rel).read_bytes()
                canonical = data.replace(b"\r\n", b"\n")
                if len(canonical) != row.get("bytes") or sha(canonical) != row.get("sha256"):
                    errors.append("source_hash:" + rel)
                runtime_hash = row.get("runtime_sha256")
                if (not isinstance(runtime_hash, str) or len(runtime_hash) != 64
                        or any(char not in "0123456789abcdef" for char in runtime_hash.lower())):
                    errors.append("source_runtime_hash_format:" + rel)
            except Exception:
                errors.append("source_read")
    experiment = source / "research/experiments/issue_3840_newline_frame_v2"
    if sha((experiment / "runner.py").read_bytes()) != doc.get("runner_sha256"):
        errors.append("runner_hash")
    if sha((experiment / "audit.py").read_bytes()) != doc.get("auditor_sha256"):
        errors.append("auditor_hash")
    if sha((experiment / "PLAN.md").read_bytes()) != os.environ.get("EXPECTED_PLAN_SHA256"):
        errors.append("plan_hash")
    if sha((experiment / "CONTAINER_RUN.md").read_bytes()) != os.environ.get("EXPECTED_RUNBOOK_SHA256"):
        errors.append("runbook_hash")

    rows = doc.get("rows")
    expected = {"complete_delivery", "terminal_lf_lost", "request_only_unknown", "occupied_destination"}
    if not isinstance(rows, list) or len(rows) != 4 or {row.get("case") for row in rows if isinstance(row, dict)} != expected:
        errors.append("row_inventory")
        rows = rows if isinstance(rows, list) else []
    indexed = {row.get("case"): row for row in rows if isinstance(row, dict)}

    complete = indexed.get("complete_delivery", {})
    try:
        accepted = base64.b64decode(complete["accepted_b64"], validate=True)
        delivered = base64.b64decode(complete["delivered_b64"], validate=True)
        parsed = json.loads(delivered)
        if (complete.get("producer_exit") != 0 or complete.get("dispatch_calls") != 1
                or accepted != delivered or not delivered.endswith(b"\n")
                or parsed.get("result", {}).get("status") != "completed"):
            errors.append("complete_delivery")
    except Exception:
        errors.append("complete_decode")

    trunc = indexed.get("terminal_lf_lost", {})
    try:
        accepted = base64.b64decode(trunc["accepted_b64"], validate=True)
        delivered = base64.b64decode(trunc["delivered_b64"], validate=True)
        report_bytes = base64.b64decode(trunc["report_b64"], validate=True)
        report = json.loads(report_bytes)
        naive = json.loads(delivered)
        status = trunc.get("attempt_status", {})
        report_record = status.get("files", {}).get("report.json", {})
        review = trunc.get("review", {})
        if (trunc.get("producer_exit") != 0 or trunc.get("dispatch_calls") != 1
                or not accepted.endswith(b"\n") or delivered != accepted[:-1]
                or len(delivered) >= len(accepted) or delivered.endswith(b"\n")
                or sha(accepted) != trunc.get("accepted_sha256")
                or sha(delivered) != trunc.get("delivered_sha256")
                or sha(report_bytes) != trunc.get("report_sha256")
                or naive.get("result", {}).get("status") != "completed"
                or trunc.get("naive_parse") != "valid_json" or trunc.get("naive_claims_completed") is not True
                or trunc.get("frame_valid") is not False
                or trunc.get("frame_guard") != "reject_missing_terminal_lf"
                or trunc.get("guard_and_recovery_pass") is not True
                or trunc.get("attempt_status_exit") != 0 or status.get("status") != "report_recorded"
                or status.get("replay_allowed") is not False or report_record.get("state") != "recorded"
                or report_record.get("sha256") != sha(report_bytes) or report_record.get("value") != report
                or trunc.get("review_exit") != 0 or review.get("receipt", {}).get("report") != report
                or review.get("receipt", {}).get("source", {}).get("sha256") != sha(report_bytes)
                or review.get("outcome_summary", {}).get("execution_status") != "completed"
                or trunc.get("snapshot_before") != trunc.get("snapshot_after")):
            errors.append("terminal_lf_contract")
    except Exception:
        errors.append("terminal_lf_decode")

    unknown = indexed.get("request_only_unknown", {})
    status = unknown.get("attempt_status", {})
    if (unknown.get("attempt_status_exit") != 2 or unknown.get("dispatch_calls") != 0
            or status.get("status") != "unknown_or_incomplete" or status.get("replay_allowed") is not False):
        errors.append("request_only_control")
    occupied = indexed.get("occupied_destination", {})
    sentinel = next((row for row in occupied.get("files", [])
                     if row.get("path") == "sentinel"), {})
    if (occupied.get("producer_exit") != 2 or occupied.get("dispatch_calls") != 0
            or occupied.get("response", {}).get("error") != "REQUEST_PERSISTENCE_FAILED"
            or sentinel.get("bytes") != len(b"preserve-me")
            or sentinel.get("sha256") != sha(b"preserve-me")):
        errors.append("occupied_destination_control")

    formal = doc.get("formal_decision")
    secondary = doc.get("secondary_decision")
    if formal != "FAIL_FALSE_SUCCESS" or secondary != "PASS_FRAMING_GUARD_RECOVERY_SCOPED":
        errors.append("decision_labels")
    result = {"schema": "issue-3840/independent-audit-v2", "raw_sha256": sha(raw_bytes),
              "decision": "PASS_AUDIT_NEWLINE_FALSE_SUCCESS_SCOPED" if not errors else "FAIL_AUDIT_NEWLINE_FALSE_SUCCESS",
              "formal_decision": formal, "secondary_decision": secondary,
              "errors": errors, "rows": len(rows)}
    encoded = json.dumps(result, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"
    (out / "audit.json").write_bytes(encoded)
    print(encoded.decode("utf-8"), end="")
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
