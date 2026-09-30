"""Corrected, read-only evidence binding audit for Issue #3711 allocation 02."""
import hashlib
import json
from pathlib import Path
import sys


def sha(data):
    return hashlib.sha256(data).hexdigest()


def snapshot(root):
    result = {}
    for path in sorted(root.rglob("*")):
        name = path.relative_to(root).as_posix()
        if path.is_file():
            result[name] = {"kind": "file", "bytes": path.stat().st_size,
                            "sha256": sha(path.read_bytes())}
        elif path.is_dir():
            result[name] = {"kind": "directory"}
    return result


def main():
    evidence, output = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
    source = Path("/src").resolve()
    study = source / "research/integration/issue_3711_downstream_truncation_v1"
    audit_root = study / "audit-v2-successor-02"
    freeze_path = audit_root / "FREEZE.json"
    freeze = json.loads(freeze_path.read_text())
    formal_freeze_path = study / "successor-02/FREEZE.json"
    formal_freeze_bytes = formal_freeze_path.read_bytes()
    formal_freeze = json.loads(formal_freeze_bytes)
    raw_bytes = (evidence / "raw.json").read_bytes()
    raw = json.loads(raw_bytes)
    audit_v1_bytes = (evidence / "audit.json").read_bytes()
    audit_v1 = json.loads(audit_v1_bytes)
    prior_v2_bytes = (study / "audit-v2/formal-02-recheck/RESULT.json").read_bytes()
    prior_v2 = json.loads(prior_v2_bytes)
    errors = []

    current_sources = {
        "research/integration/issue_3711_downstream_truncation_v1/audit-v2-successor-02/PLAN.md":
            sha((audit_root / "PLAN.md").read_bytes()),
        "research/integration/issue_3711_downstream_truncation_v1/audit-v2-successor-02/audit.py":
            sha((audit_root / "audit.py").read_bytes()),
    }
    if current_sources != freeze["sha256"]:
        errors.append("AUDIT_SUCCESSOR_SOURCE_HASH_MISMATCH")
    formal_sources = {}
    for name in formal_freeze["sha256"]:
        path = source / name if name.startswith("runtime/") else study / "successor-02" / name
        formal_sources[name] = sha(path.read_bytes())
    if formal_sources != formal_freeze["sha256"] or raw.get("source_sha256") != formal_freeze["sha256"]:
        errors.append("FORMAL_SOURCE_HASH_MISMATCH")
    if (raw.get("base_commit") != freeze["formal_base_commit"]
            or formal_freeze.get("base_commit") != freeze["formal_base_commit"]
            or freeze["audit_source_commit"] != freeze["audit_code_base_commit"]):
        errors.append("FORMAL_AND_AUDIT_BASES_NOT_SEPARATED")
    if sha(formal_freeze_bytes) != freeze["formal_freeze_sha256"]:
        errors.append("FORMAL_FREEZE_HASH_MISMATCH")
    if sha(raw_bytes) != freeze["formal_raw_sha256"]:
        errors.append("FORMAL_RAW_HASH_MISMATCH")
    if sha(audit_v1_bytes) != freeze["audit_v1_sha256"]:
        errors.append("AUDIT_V1_HASH_MISMATCH")
    if (audit_v1.get("disposition") != "PASS_SCOPED_DOWNSTREAM_REJECTION_AND_READ_ONLY_RECOVERY"
            or audit_v1.get("raw_sha256") != sha(raw_bytes)):
        errors.append("AUDIT_V1_BINDING_MISMATCH")
    if sha(prior_v2_bytes) != freeze["audit_v2_01_failure_sha256"]:
        errors.append("PRIOR_V2_FAILURE_HASH_MISMATCH")
    if prior_v2.get("disposition") != "FAIL_AUDIT_V2" or prior_v2.get("errors") != ["ALLOCATION_OR_BASE_MISMATCH"]:
        errors.append("PRIOR_V2_FAILURE_NOT_AS_RECORDED")

    attempt = evidence / "attempt"
    request = (attempt / "request.json").read_bytes()
    report = (attempt / "report.json").read_bytes()
    if request != (evidence / "request.json").read_bytes():
        errors.append("REQUEST_COPY_MISMATCH")
    if report != (evidence / "report.json").read_bytes():
        errors.append("REPORT_COPY_MISMATCH")
    actual_snapshot = snapshot(attempt)
    if raw.get("attempt_files_before_recovery") != actual_snapshot or raw.get("attempt_files_after_recovery") != actual_snapshot:
        errors.append("ACTUAL_ATTEMPT_SNAPSHOT_MISMATCH")
    recovery = json.loads((evidence / "recovery.stdout").read_bytes())
    if recovery.get("status") != "report_recorded" or recovery.get("replay_allowed") is not False:
        errors.append("RECOVERY_STATUS_OR_REPLAY_POLICY_MISMATCH")
    for name, data in (("request.json", request), ("report.json", report)):
        row = recovery.get("files", {}).get(name, {})
        if row.get("state") != "recorded" or row.get("sha256") != sha(data) or row.get("value") != json.loads(data):
            errors.append("RECOVERY_VALUE_HASH_BINDING_MISMATCH:" + name)
    if raw.get("request_sha256_before_recovery") != sha(request) or raw.get("request_sha256_after_recovery") != sha(request):
        errors.append("REQUEST_BEFORE_AFTER_MISMATCH")
    if raw.get("report_sha256_before_recovery") != sha(report) or raw.get("report_sha256_after_recovery") != sha(report):
        errors.append("REPORT_BEFORE_AFTER_MISMATCH")
    if raw.get("dispatch_call_count_after_recovery") != 1:
        errors.append("DISPATCH_CALL_COUNT_MISMATCH")

    accepted = (evidence / "accepted.json").read_bytes()
    delivered = (evidence / "delivered-prefix.bin").read_bytes()
    try:
        full_value = json.loads(accepted)
        if full_value.get("status") != "returned" or full_value.get("result", {}).get("scope") != "synthetic-only":
            errors.append("FULL_DOCUMENT_CONTENT_MISMATCH")
    except (UnicodeDecodeError, json.JSONDecodeError):
        full_value = None
        errors.append("FULL_ACCEPTED_JSON_INVALID")
    try:
        json.loads(delivered)
        consumer_error = None
        errors.append("TRUNCATED_PREFIX_ACCEPTED")
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        consumer_error = type(error).__name__
    if not accepted.startswith(delivered) or len(delivered) >= len(accepted):
        errors.append("DELIVERED_DATA_NOT_STRICT_PREFIX")
    if raw.get("producer", {}).get("write_return_values") != [len(accepted.decode("utf-8"))]:
        errors.append("PRODUCER_FULL_ACCEPTANCE_MISMATCH")
    if raw.get("downstream", {}).get("consumer", {}).get("error_type") != consumer_error:
        errors.append("CONSUMER_ERROR_RECORD_MISMATCH")

    disposition = "PASS_V2_ARTIFACT_BINDING" if not errors else "FAIL_AUDIT_V2_SUCCESSOR"
    result = {
        "schema": "agent-interface/issue3711-downstream-truncation-audit-v2-successor-v1",
        "allocation": freeze["allocation"], "disposition": disposition, "errors": errors,
        "formal_base_commit": freeze["formal_base_commit"],
        "audit_code_base_commit": freeze["audit_code_base_commit"],
        "formal_raw_sha256": sha(raw_bytes), "audit_v1_sha256": sha(audit_v1_bytes),
        "prior_v2_01_sha256": sha(prior_v2_bytes), "formal_freeze_sha256": sha(formal_freeze_bytes),
        "source_sha256": current_sources, "formal_source_sha256": formal_sources,
        "attempt_snapshot": actual_snapshot, "request_sha256": sha(request), "report_sha256": sha(report),
        "accepted_bytes": len(accepted), "delivered_prefix_bytes": len(delivered),
        "full_document": "valid_json" if full_value is not None else "invalid_json",
        "downstream_consumer_error": consumer_error,
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "RESULT.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
