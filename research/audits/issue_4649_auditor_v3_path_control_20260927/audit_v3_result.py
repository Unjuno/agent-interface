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
    if sha(root / "audit_v3_result.py") != audit_freeze.get("audit_source_sha256"):
        errors.append("INDEPENDENT_AUDITOR_HASH_MISMATCH")
    checks.append("independent_auditor_hash")
    freeze_path = root / "FREEZE.json"
    freeze = json.loads(freeze_path.read_bytes())
    sidecar = (root / "FREEZE.sha256").read_text(encoding="ascii").split()[0]
    if sha(freeze_path) != sidecar:
        errors.append("FREEZE_HASH_MISMATCH")
    if sha(freeze_path) != audit_freeze.get("candidate_freeze_sha256"):
        errors.append("FROZEN_CANDIDATE_FREEZE_HASH_MISMATCH")
    checks.append("freeze_sidecar")
    for path, field in (("PLAN.md", "plan_sha256"), ("audit_v3.py", "candidate_source_sha256"), ("probe_v3.py", "probe_sha256")):
        if sha(root / path) != freeze.get(field):
            errors.append("SOURCE_HASH_MISMATCH:" + path)
    checks.append("frozen_source_hashes")

    result_path = evidence / "RESULT.json"
    invocation_path = root / "INVOCATION.json"
    result = json.loads(result_path.read_bytes())
    invocation = json.loads(invocation_path.read_bytes())
    result_sha = sha(result_path)
    if result_sha != invocation.get("stdout_result_sha256"):
        errors.append("RESULT_HASH_MISMATCH")
    if result_sha != audit_freeze.get("result_sha256"):
        errors.append("FROZEN_RESULT_HASH_MISMATCH")
    if sha(invocation_path) != audit_freeze.get("invocation_receipt_sha256"):
        errors.append("INVOCATION_RECEIPT_HASH_MISMATCH")
    if invocation.get("container_invocations") != 1:
        errors.append("CONTAINER_INVOCATION_COUNT_MISMATCH")
    if invocation.get("docker_exit_code") != 1 or invocation.get("docker_stderr") != "":
        errors.append("INVOCATION_RECEIPT_MISMATCH")
    if result.get("decision") != "FAIL_PATH_CONFINEMENT_OR_COMPATIBILITY" or result.get("checks_pass") is not False:
        errors.append("ORIGINAL_GATE_DISPOSITION_MISMATCH")
    if result.get("source_sha256") != freeze.get("candidate_source_sha256"):
        errors.append("RESULT_SOURCE_HASH_MISMATCH")
    if result.get("image_id") != freeze.get("image_id"):
        errors.append("IMAGE_ID_MISMATCH")
    if result.get("formal_runner_invocations") != 0 or result.get("prior_eight_control_harness_invocations") != 0:
        errors.append("SCOPE_COUNT_MISMATCH")
    rows = {row.get("name"): row for row in result.get("rows", [])}
    expected_names = {"contained_file", "contained_symlink", "dotdot", "input_symlink_escape", "manifest_symlink_escape"}
    if set(rows) != expected_names:
        errors.append("CONTROL_SET_MISMATCH")
    else:
        for name in ("contained_file", "contained_symlink"):
            row = rows[name]
            if row.get("decision") != "PASS_INDEPENDENT" or row.get("errors") != [] or row.get("stderr") != "":
                errors.append("IN_ROOT_COMPATIBILITY_OUTCOME_MISMATCH:" + name)
        checks.append("in_root_compatibility")
        for name, marker in (
            ("dotdot", "V2_UNSAFE_INPUT_PATH:sentinel"),
            ("input_symlink_escape", "V3_UNSAFE_INPUT_PATH:sentinel"),
            ("manifest_symlink_escape", "V3_UNSAFE_MANIFEST_PATH"),
        ):
            row = rows[name]
            if row.get("decision") != "FAIL" or marker not in (row.get("errors") or []) or row.get("stderr") != "":
                errors.append("ESCAPE_NOT_REJECTED:" + name)
        checks.append("escape_controls_rejected")
        if rows["input_symlink_escape"].get("errors") != ["V3_UNSAFE_INPUT_PATH:sentinel"]:
            checks.append("probe_gate_exact_error_list_mismatch_observed")

    audit = {
        "schema": "issue4649-auditor-v3-path-control-independent-audit-v1",
        "decision": "PASS_INDEPENDENT_AUDIT_OF_RETAINED_GATE_FAIL" if not errors else "FAIL_AUDIT",
        "checks": checks,
        "errors": errors,
        "original_allocation_disposition": result.get("decision"),
        "per_case_path_safety_observation": "all escape controls rejected; both in-root controls passed" if not errors else "unverified",
        "interpretation": "The original frozen gate remains FAIL. Its harness expected exact equality for one symlink error list, while the candidate correctly added independent result-ledger mismatch errors; this independent posthoc audit does not rewrite or upgrade the original allocation.",
        "result_sha256": result_sha,
        "formal_runner_invocations": 0,
    }
    encoded = json.dumps(audit, sort_keys=True) + "\n"
    (Path("/out") / "INDEPENDENT_AUDIT.json").write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
