import hashlib
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    root = Path("/study")
    evidence = Path("/evidence")
    errors = []
    checks = []
    audit_freeze = json.loads((root / "AUDIT_FREEZE.json").read_bytes())
    if sha(root / "audit_v3_result02.py") != audit_freeze.get("audit_source_sha256"):
        errors.append("INDEPENDENT_AUDITOR_HASH_MISMATCH")
    checks.append("independent_auditor_hash")

    freeze_path = root / "FREEZE.json"
    freeze = json.loads(freeze_path.read_bytes())
    sidecar = (root / "FREEZE.sha256").read_text(encoding="ascii").split()[0]
    if sha(freeze_path) != sidecar or sha(freeze_path) != audit_freeze.get("candidate_freeze_sha256"):
        errors.append("FREEZE_HASH_MISMATCH")
    for path, field in (("PLAN.md", "plan_sha256"), ("audit_v3.py", "candidate_source_sha256"), ("probe_v3_gatefix.py", "probe_sha256")):
        if sha(root / path) != freeze.get(field):
            errors.append("SOURCE_HASH_MISMATCH:" + path)
    checks.append("frozen_source_hashes")

    result_path = evidence / "RESULT.json"
    invocation_path = root / "INVOCATION.json"
    result = json.loads(result_path.read_bytes())
    invocation = json.loads(invocation_path.read_bytes())
    result_hash = sha(result_path)
    if result_hash != invocation.get("stdout_result_sha256") or result_hash != audit_freeze.get("result_sha256"):
        errors.append("RESULT_HASH_MISMATCH")
    if sha(invocation_path) != audit_freeze.get("invocation_receipt_sha256"):
        errors.append("INVOCATION_RECEIPT_HASH_MISMATCH")
    if invocation.get("docker_exit_code") != 0 or invocation.get("docker_stderr") != "" or invocation.get("container_invocations") != 1:
        errors.append("INVOCATION_RECEIPT_MISMATCH")
    if result.get("source_sha256") != freeze.get("candidate_source_sha256") or result.get("image_id") != freeze.get("image_id"):
        errors.append("EXECUTION_IDENTITY_MISMATCH")
    if result.get("checks_pass") is not True or result.get("decision") != "PASS_PATH_CONFINEMENT_V3":
        errors.append("ALLOCATION_GATE_MISMATCH")
    if result.get("formal_runner_invocations") != 0 or result.get("prior_eight_control_harness_invocations") != 0:
        errors.append("SCOPE_COUNT_MISMATCH")
    checks.append("invocation_and_result_binding")

    rows = {row.get("name"): row for row in result.get("rows", [])}
    expected = {
        "contained_file": ("PASS_INDEPENDENT", []),
        "contained_symlink": ("PASS_INDEPENDENT", []),
        "dotdot": ("FAIL", "V2_UNSAFE_INPUT_PATH:sentinel"),
        "input_symlink_escape": ("FAIL", "V3_UNSAFE_INPUT_PATH:sentinel"),
        "manifest_symlink_escape": ("FAIL", "V3_UNSAFE_MANIFEST_PATH"),
    }
    if set(rows) != set(expected):
        errors.append("CONTROL_SET_MISMATCH")
    else:
        for name, (decision, expected_errors) in expected.items():
            row = rows[name]
            if row.get("decision") != decision or row.get("stderr") != "":
                errors.append("CONTROL_OUTCOME_MISMATCH:" + name)
            if isinstance(expected_errors, list) and row.get("errors") != expected_errors:
                errors.append("POSITIVE_CONTROL_ERRORS:" + name)
            if isinstance(expected_errors, str) and expected_errors not in (row.get("errors") or []):
                errors.append("REQUIRED_REJECTION_MISSING:" + name)
    checks.append("control_outcomes")

    audit = {
        "schema": "issue4649-auditor-v3-path-control-independent-audit-v2",
        "decision": "PASS_INDEPENDENT_AUDIT_OF_SCOPED_PASS" if not errors else "FAIL_AUDIT",
        "checks": checks,
        "errors": errors,
        "result_sha256": result_hash,
        "predecessor_allocation_01_disposition": "FAIL_PATH_CONFINEMENT_OR_COMPATIBILITY; preserved unchanged",
        "formal_runner_invocations": 0,
    }
    encoded = json.dumps(audit, sort_keys=True) + "\n"
    (Path("/out") / "INDEPENDENT_AUDIT.json").write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
