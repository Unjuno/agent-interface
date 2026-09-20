"""Read-only evidence-binding audit for Issue #3711 formal allocation 02."""
import hashlib
import json
from pathlib import Path
import sys


def digest(data):
    return hashlib.sha256(data).hexdigest()


def tree_snapshot(root):
    snapshot = {}
    for path in sorted(root.rglob("*")):
        name = path.relative_to(root).as_posix()
        if path.is_file():
            snapshot[name] = {"kind": "file", "sha256": digest(path.read_bytes()),
                              "bytes": path.stat().st_size}
        elif path.is_dir():
            snapshot[name] = {"kind": "directory"}
    return snapshot


def main():
    evidence, output = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
    source = Path("/src").resolve()
    here = Path(__file__).resolve().parent
    base = source / "research/integration/issue_3711_downstream_truncation_v1"
    freeze_path = here / "FREEZE.json"
    freeze = json.loads(freeze_path.read_text())
    formal_freeze_path = base / "successor-02/FREEZE.json"
    formal_freeze_bytes = formal_freeze_path.read_bytes()
    formal_freeze = json.loads(formal_freeze_bytes)
    raw_bytes = (evidence / "raw.json").read_bytes()
    raw = json.loads(raw_bytes)
    errors = []
    if raw.get("allocation") != freeze.get("allocation") or raw.get("base_commit") != freeze.get("base_commit"):
        errors.append("ALLOCATION_OR_BASE_MISMATCH")

    observed = {}
    for name in freeze["sha256"]:
        path = source / name
        observed[name] = digest(path.read_bytes())
    if observed != freeze["sha256"]:
        errors.append("AUDIT_V2_SOURCE_HASH_MISMATCH")
    formal_sources = {}
    for name in formal_freeze["sha256"]:
        path = (source / name) if name.startswith("runtime/") else (base / "successor-02" / name)
        formal_sources[name] = digest(path.read_bytes())
    if formal_sources != formal_freeze["sha256"] or raw.get("source_sha256") != formal_freeze["sha256"]:
        errors.append("FORMAL_SOURCE_HASH_OR_RAW_BINDING_MISMATCH")

    old_audit_bytes = (evidence / "audit.json").read_bytes()
    old_audit = json.loads(old_audit_bytes)
    original_freeze_path = source / "research/integration/issue_3711_downstream_truncation_v1/successor-02/FREEZE.json"
    original_freeze_bytes = original_freeze_path.read_bytes()
    if digest(raw_bytes) != freeze["formal_raw_sha256"]:
        errors.append("FORMAL_RAW_HASH_MISMATCH")
    if digest(old_audit_bytes) != freeze["audit_v1_sha256"]:
        errors.append("AUDIT_V1_HASH_MISMATCH")
    if digest(original_freeze_bytes) != freeze["formal_freeze_sha256"]:
        errors.append("FORMAL_FREEZE_HASH_MISMATCH")
    if old_audit.get("disposition") != "PASS_SCOPED_DOWNSTREAM_REJECTION_AND_READ_ONLY_RECOVERY" or old_audit.get("raw_sha256") != digest(raw_bytes):
        errors.append("AUDIT_V1_RESULT_BINDING_MISMATCH")

    actual_attempt = evidence / "attempt"
    actual_request = (actual_attempt / "request.json").read_bytes()
    actual_report = (actual_attempt / "report.json").read_bytes()
    copied_request = (evidence / "request.json").read_bytes()
    copied_report = (evidence / "report.json").read_bytes()
    if actual_request != copied_request:
        errors.append("REQUEST_COPY_DIFFERS_FROM_ATTEMPT_DIRECTORY")
    if actual_report != copied_report:
        errors.append("REPORT_COPY_DIFFERS_FROM_ATTEMPT_DIRECTORY")
    actual_snapshot = tree_snapshot(actual_attempt)
    if raw.get("attempt_files_before_recovery") != actual_snapshot or raw.get("attempt_files_after_recovery") != actual_snapshot:
        errors.append("RECORDED_SNAPSHOT_DIFFERS_FROM_RETAINED_ATTEMPT")

    recovery = json.loads((evidence / "recovery.stdout").read_bytes())
    if recovery.get("status") != "report_recorded" or recovery.get("replay_allowed") is not False:
        errors.append("RECOVERY_STATUS_OR_REPLAY_POLICY_MISMATCH")
    recovery_files = recovery.get("files", {})
    for name, data in (("request.json", actual_request), ("report.json", actual_report)):
        row = recovery_files.get(name, {})
        if row.get("state") != "recorded" or row.get("sha256") != digest(data):
            errors.append("RECOVERY_FILE_HASH_MISMATCH:" + name)
        if row.get("value") != json.loads(data):
            errors.append("RECOVERY_FILE_VALUE_MISMATCH:" + name)
    if raw.get("request_sha256_before_recovery") != digest(actual_request) or raw.get("request_sha256_after_recovery") != digest(actual_request):
        errors.append("RAW_REQUEST_HASH_MISMATCH")
    if raw.get("report_sha256_before_recovery") != digest(actual_report) or raw.get("report_sha256_after_recovery") != digest(actual_report):
        errors.append("RAW_REPORT_HASH_MISMATCH")

    accepted = (evidence / "accepted.json").read_bytes()
    delivered = (evidence / "delivered-prefix.bin").read_bytes()
    try:
        accepted_value = json.loads(accepted)
    except (UnicodeDecodeError, json.JSONDecodeError):
        accepted_value = None
        errors.append("FULL_ACCEPTED_DOCUMENT_INVALID")
    if accepted_value is not None and (accepted_value.get("status") != "returned"
            or accepted_value.get("result", {}).get("scope") != "synthetic-only"):
        errors.append("FULL_ACCEPTED_DOCUMENT_CONTENT_MISMATCH")
    try:
        json.loads(delivered)
        consumer_error = None
        errors.append("TRUNCATED_DOWNSTREAM_DOCUMENT_ACCEPTED")
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        consumer_error = type(error).__name__
    if not accepted.startswith(delivered) or len(delivered) >= len(accepted):
        errors.append("DELIVERED_BYTES_NOT_STRICT_PREFIX")
    if raw.get("producer", {}).get("write_return_values") != [len(accepted.decode("utf-8"))]:
        errors.append("PRODUCER_FULL_ACCEPT_NOT_BOUND")
    if raw.get("producer", {}).get("accepted_sha256") != digest(accepted):
        errors.append("ACCEPTED_BYTES_HASH_MISMATCH")
    downstream = raw.get("downstream", {})
    consumer = downstream.get("consumer", {})
    if downstream.get("delivered_bytes") != len(delivered) or downstream.get("delivered_sha256") != digest(delivered):
        errors.append("DELIVERED_BYTES_HASH_OR_LENGTH_MISMATCH")
    if consumer.get("accepted") is not False or consumer.get("error_type") != consumer_error:
        errors.append("DOWNSTREAM_REJECTION_RECORD_MISMATCH")
    report_value = json.loads(actual_report)
    if report_value.get("result", {}).get("scope") != "synthetic-only" or raw.get("dispatch_call_count_after_recovery") != 1:
        errors.append("SYNTHETIC_SCOPE_OR_CALL_COUNT_MISMATCH")

    disposition = "PASS_V2_ARTIFACT_BINDING" if not errors else "FAIL_AUDIT_V2"
    result = {"schema": "agent-interface/issue3711-downstream-truncation-audit-v2",
              "allocation": freeze["allocation"], "disposition": disposition,
              "errors": errors, "raw_sha256": digest(raw_bytes),
              "audit_v1_sha256": digest(old_audit_bytes), "formal_freeze_sha256": digest(original_freeze_bytes),
              "source_sha256": observed, "attempt_snapshot": actual_snapshot,
              "request_sha256": digest(actual_request), "report_sha256": digest(actual_report),
              "accepted_bytes": len(accepted), "delivered_prefix_bytes": len(delivered),
              "full_accepted_document": "valid_json" if accepted_value is not None else "invalid_json",
              "downstream_consumer_error": consumer_error}
    output.mkdir(parents=True, exist_ok=True)
    (output / "RESULT.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
