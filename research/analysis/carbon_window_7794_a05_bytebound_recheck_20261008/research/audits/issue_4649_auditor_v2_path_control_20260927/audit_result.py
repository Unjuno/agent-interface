import hashlib
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    root = Path("/study")
    evidence = Path("/evidence")
    checks = []
    errors = []
    audit_freeze = json.loads((root / "AUDIT_FREEZE.json").read_bytes())
    if sha(root / "audit_result.py") != audit_freeze.get("audit_source_sha256"):
        errors.append("INDEPENDENT_AUDITOR_HASH_MISMATCH")
    checks.append("independent_auditor_hash")
    freeze_path = root / "FREEZE.json"
    freeze = json.loads(freeze_path.read_bytes())
    sidecar = (root / "FREEZE.sha256").read_text(encoding="ascii").split()[0]
    if sha(freeze_path) != sidecar:
        errors.append("FREEZE_HASH_MISMATCH")
    checks.append("freeze_sidecar")
    if sha(root / "PLAN.md") != freeze.get("plan_sha256"):
        errors.append("PLAN_HASH_MISMATCH")
    if sha(root / "probe.py") != freeze.get("probe_sha256"):
        errors.append("PROBE_HASH_MISMATCH")
    checks.append("frozen_sources")

    result_path = evidence / "RESULT.json"
    invocation_path = root / "INVOCATION.json"
    result = json.loads(result_path.read_bytes())
    invocation = json.loads(invocation_path.read_bytes())
    result_hash = sha(result_path)
    if result_hash != invocation.get("stdout_result_sha256"):
        errors.append("RESULT_HASH_MISMATCH")
    if result_hash != audit_freeze.get("result_sha256"):
        errors.append("FROZEN_RESULT_HASH_MISMATCH")
    if sha(invocation_path) != audit_freeze.get("invocation_receipt_sha256"):
        errors.append("INVOCATION_RECEIPT_HASH_MISMATCH")
    if invocation.get("docker_exit_code") != 1 or invocation.get("docker_stderr") != "":
        errors.append("INVOCATION_RECEIPT_MISMATCH")
    if result.get("source_sha256") != freeze.get("source_sha256"):
        errors.append("AUDITED_SOURCE_HASH_MISMATCH")
    if result.get("image_id") != freeze.get("image_id"):
        errors.append("IMAGE_ID_MISMATCH")
    if result.get("formal_runner_invocations") != 0 or result.get("prior_eight_control_harness_invocations") != 0:
        errors.append("SCOPE_COUNT_MISMATCH")
    rows = {row.get("name"): row for row in result.get("rows", [])}
    if set(rows) != {"dotdot", "symlink"}:
        errors.append("CONTROL_SET_MISMATCH")
    else:
        if rows["dotdot"].get("decision") != "FAIL" or not rows["dotdot"].get("errors"):
            errors.append("DOTDOT_CONTROL_NOT_REJECTED")
        if rows["symlink"].get("decision") != "PASS_INDEPENDENT" or rows["symlink"].get("errors") != []:
            errors.append("SYMLINK_OUTCOME_MISMATCH")
    if result.get("decision") != "FAIL_SYMLINK_PATH_CONFINEMENT" or result.get("checks_pass") is not False:
        errors.append("DISPOSITION_MISMATCH")
    checks.extend(["invocation_and_result_binding", "control_outcomes"])
    audit = {
        "schema": "issue4649-v2-path-control-independent-audit-v1",
        "decision": "PASS_INDEPENDENT_AUDIT_OF_RETAINED_FAIL" if not errors else "FAIL_AUDIT",
        "checks": checks,
        "errors": errors,
        "result_sha256": result_hash,
        "formal_runner_invocations": 0,
    }
    encoded = json.dumps(audit, sort_keys=True) + "\n"
    (Path("/out") / "INDEPENDENT_AUDIT.json").write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
