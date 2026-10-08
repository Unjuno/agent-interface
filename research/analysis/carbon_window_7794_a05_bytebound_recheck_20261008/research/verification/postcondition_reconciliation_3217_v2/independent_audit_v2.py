from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import types


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def byte_binding_errors(raw: bytes, audit: bytes, binding: dict) -> list[str]:
    errors = []
    raw_expected = binding.get("artifact_raw_sha256")
    audit_expected = binding.get("artifact_audit_sha256")
    if not isinstance(raw_expected, str) or sha256(raw) != raw_expected:
        errors.append("artifact_raw_sha256_mismatch")
    if not isinstance(audit_expected, str) or sha256(audit) != audit_expected:
        errors.append("artifact_audit_sha256_mismatch")
    return errors


def load_legacy_auditor(source: bytes):
    module = types.ModuleType("_retained_independent_audit_v1")
    exec(compile(source, "independent_audit.py", "exec"), module.__dict__)
    return module


def reproduce(raw: bytes, audit: bytes, binding_bytes: bytes,
              expected_report: bytes, auditor_source: bytes) -> dict:
    binding = json.loads(binding_bytes)
    raw_hash, audit_hash = sha256(raw), sha256(audit)
    errors = byte_binding_errors(raw, audit, binding)
    result = {
        "schema": "agent-interface/postcondition-reconciliation-byte-audit-v2",
        "artifact_raw_sha256": raw_hash,
        "artifact_audit_sha256": audit_hash,
        "raw_hash_matches_binding": raw_hash == binding.get("artifact_raw_sha256"),
        "audit_hash_matches_binding": audit_hash == binding.get("artifact_audit_sha256"),
        "legacy_auditor_sha256": sha256(auditor_source),
        "legacy_report_sha256": sha256(expected_report),
        "legacy_report_reproduced_exactly": False,
        "v1_raw_newline_mutation_status": None,
        "v1_audit_newline_mutation_status": None,
        "v1_raw_newline_mutation_hash_mismatch": False,
        "v1_audit_newline_mutation_hash_mismatch": False,
        "rows": 0,
        "unique_identities": 0,
        "legacy_corruptions_rejected": 0,
        "byte_corruption_controls": [],
        "errors": errors,
    }
    result["v1_raw_newline_mutation_hash_mismatch"] = (
        sha256(raw + b"\n") != binding.get("artifact_raw_sha256")
    )
    result["v1_audit_newline_mutation_hash_mismatch"] = (
        sha256(audit + b"\n") != binding.get("artifact_audit_sha256")
    )
    if errors:
        result["status"] = "FAIL_ARTIFACT_BYTE_BINDING"
        return result

    legacy = load_legacy_auditor(auditor_source)
    rows = json.loads(raw)
    historical_audit = json.loads(audit)
    legacy_result = legacy.audit(rows, binding, historical_audit)
    controls = legacy.controls(rows, binding, historical_audit)
    legacy_result["corruption_controls"] = controls
    legacy_result["corruptions_rejected"] = sum(item["rejected"] for item in controls)
    legacy_result["artifact_raw_sha256"] = raw_hash
    legacy_result["artifact_audit_sha256"] = audit_hash
    reproduced = (json.dumps(legacy_result, indent=2, sort_keys=True) + "\n").encode()
    result["legacy_report_reproduced_exactly"] = reproduced == expected_report
    result["v1_raw_newline_mutation_status"] = legacy.audit(
        json.loads(raw + b"\n"), binding, historical_audit
    )["status"]
    result["v1_audit_newline_mutation_status"] = legacy.audit(
        rows, binding, json.loads(audit + b"\n")
    )["status"]
    result["rows"] = legacy_result["rows"]
    result["unique_identities"] = legacy_result["unique_identities"]
    result["legacy_corruptions_rejected"] = legacy_result["corruptions_rejected"]

    mutations = (
        ("raw_trailing_newline", raw + b"\n", audit),
        ("audit_trailing_newline", raw, audit + b"\n"),
    )
    for name, mutated_raw, mutated_audit in mutations:
        mutation_errors = byte_binding_errors(mutated_raw, mutated_audit, binding)
        result["byte_corruption_controls"].append({
            "name": name,
            "rejected": bool(mutation_errors),
            "errors": mutation_errors,
        })
    if not result["legacy_report_reproduced_exactly"]:
        result["errors"].append("legacy_report_not_reproduced")
    if result["v1_raw_newline_mutation_status"] != legacy_result["status"]:
        result["errors"].append("v1_raw_newline_mutation_did_not_reproduce")
    if result["v1_audit_newline_mutation_status"] != legacy_result["status"]:
        result["errors"].append("v1_audit_newline_mutation_did_not_reproduce")
    if not result["v1_raw_newline_mutation_hash_mismatch"]:
        result["errors"].append("raw_newline_mutation_hash_not_changed")
    if not result["v1_audit_newline_mutation_hash_mismatch"]:
        result["errors"].append("audit_newline_mutation_hash_not_changed")
    if result["legacy_corruptions_rejected"] != len(controls):
        result["errors"].append("legacy_corruption_control_failed")
    if any(not item["rejected"] for item in result["byte_corruption_controls"]):
        result["errors"].append("byte_corruption_control_accepted")
    result["status"] = "PASS_BYTE_BOUND_RAW_ONLY_REPRODUCTION" if not result["errors"] else "FAIL_RECONCILIATION"
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--binding", type=Path, required=True)
    parser.add_argument("--expected-report", type=Path, required=True)
    parser.add_argument("--legacy-auditor", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = reproduce(
        args.raw.read_bytes(), args.audit.read_bytes(), args.binding.read_bytes(),
        args.expected_report.read_bytes(), args.legacy_auditor.read_bytes(),
    )
    serialized = json.dumps(result, indent=2, sort_keys=True) + "\n"
    args.out.write_text(serialized, encoding="utf-8", newline="\n")
    print(serialized, end="")
    return 0 if result["status"] == "PASS_BYTE_BOUND_RAW_ONLY_REPRODUCTION" else 2


if __name__ == "__main__":
    raise SystemExit(main())
