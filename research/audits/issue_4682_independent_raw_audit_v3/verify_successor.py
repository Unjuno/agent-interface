"""Independent raw-only verification of the retained Issue #4682 result."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_outcome(raw: dict, receipt: dict, expected: dict) -> list[str]:
    errors = []
    if raw.get("decision") != "PASS_RUNTIME_BOUND_AUDIT_SCOPED":
        errors.append("RAW_DECISION_MISMATCH")
    if raw.get("observed_host_runtime") != receipt:
        errors.append("RECEIPT_RAW_MISMATCH")
    expected_host = {key: value for key, value in expected.items() if key != "python"}
    if receipt != expected_host:
        errors.append("HOST_RUNTIME_MISMATCH")
    if raw.get("observed_container_python") != expected.get("python"):
        errors.append("CONTAINER_PYTHON_MISMATCH")
    baseline = raw.get("baseline")
    if not isinstance(baseline, dict) or baseline.get("decision") != "PASS_RESULT_LEDGER_BINDING_SCOPED" or baseline.get("errors") != []:
        errors.append("BASELINE_MISMATCH")
    ledger = raw.get("ledger_controls")
    if not isinstance(ledger, dict) or set(ledger) != {"drop_input_row", "input_digest", "input_path"} or not all(
        isinstance(row, dict) and row.get("rejected") is True for row in ledger.values()
    ):
        errors.append("LEDGER_CONTROLS_MISMATCH")
    runtime = raw.get("runtime_mismatch_controls")
    fields = {"docker_engine", "daemon_platform", "image_id", "image_platform", "python"}
    if not isinstance(runtime, dict) or set(runtime) != fields or not all(
        isinstance(row, dict)
        and row.get("stopped") is True
        and row.get("semantic_audit_invoked") is False
        and row.get("decision") == "STOP_PROVENANCE_OR_ENVIRONMENT"
        for row in runtime.values()
    ):
        errors.append("RUNTIME_CONTROLS_MISMATCH")
    return errors


def main() -> int:
    study = Path("/study")
    evidence = Path("/evidence/formal01/AUDIT.json")
    receipt_path = Path("/runtime/receipt.json")
    out = Path("/out/INDEPENDENT_AUDIT.json")
    freeze = json.loads((study / "FREEZE.json").read_text(encoding="utf-8"))
    raw = json.loads(evidence.read_text(encoding="utf-8"))
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    v3 = json.loads(Path("/v3/FREEZE.json").read_text(encoding="utf-8"))
    errors = []
    if digest(Path("/v3/FREEZE.json")) != Path("/v3/FREEZE.sha256").read_text(encoding="ascii").split()[0]:
        errors.append("V3_FREEZE_SIDECAR_MISMATCH")
    for filename, expected in v3.get("source_sha256", {}).items():
        if digest(Path("/v3") / filename) != expected:
            errors.append("V3_SOURCE_HASH_MISMATCH:" + filename)
    for filename, expected in v3.get("study_sha256", {}).items():
        if digest(Path("/v3") / filename) != expected:
            errors.append("V3_STUDY_HASH_MISMATCH:" + filename)
    for path, expected in v3["copied_artifact_sha256"].items():
        actual_path = {
            "v2_freeze": study / "FREEZE.json",
            "formal_audit": evidence,
            "runtime_receipt": receipt_path,
        }[path]
        if digest(actual_path) != expected:
            errors.append("COPIED_ARTIFACT_HASH_MISMATCH:" + path)
    if digest(study / "FREEZE.json") != (study / "FREEZE.sha256").read_text(encoding="ascii").split()[0]:
        errors.append("V2_FREEZE_SIDECAR_MISMATCH")
    if digest(study / "inputs/MANIFEST.json") != freeze.get("manifest_sha256"):
        errors.append("V2_MANIFEST_MISMATCH")
    for filename, expected in freeze.get("source_sha256", {}).items():
        if digest(study / filename) != expected:
            errors.append("V2_SOURCE_HASH_MISMATCH:" + filename)
    for role, (filename, _repo_path, expected) in freeze.get("input_files", {}).items():
        if digest(study / "inputs" / filename) != expected:
            errors.append("V2_INPUT_HASH_MISMATCH:" + role)
    errors.extend(validate_outcome(raw, receipt, v3["expected_runtime"]))
    result = {
        "schema": "issue4687-independent-audit-v1",
        "decision": "PASS_INDEPENDENT_AUDIT_V3" if not errors else "FAIL_RAW_EVIDENCE_MISMATCH",
        "errors": errors,
        "formal_audit_sha256": digest(evidence),
        "runtime_receipt_sha256": digest(receipt_path),
        "v2_freeze_sha256": digest(study / "FREEZE.json"),
        "v2_inputs_verified": len(freeze.get("input_files", {})),
        "v2_sources_verified": len(freeze.get("source_sha256", {})),
        "scope": "independent raw consistency only; no semantic formal rerun",
    }
    out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
