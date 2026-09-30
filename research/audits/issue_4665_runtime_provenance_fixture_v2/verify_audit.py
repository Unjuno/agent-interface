"""Independent raw-only verifier; does not import the experiment runner/auditor."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    study = Path("/study")
    inputs = Path("/inputs")
    output = Path("/evidence/formal01/AUDIT.json")
    raw = json.loads(output.read_text(encoding="utf-8"))
    freeze_bytes = (study / "FREEZE.json").read_bytes()
    freeze = json.loads(freeze_bytes)
    errors = []
    if digest(study / "FREEZE.json") != (study / "FREEZE.sha256").read_text(encoding="ascii").split()[0]:
        errors.append("FREEZE_SIDECAR_MISMATCH")
    for filename, expected in freeze["source_sha256"].items():
        if digest(study / filename) != expected:
            errors.append("SOURCE_HASH_MISMATCH:" + filename)
    for filename, expected in freeze["study_sha256"].items():
        if digest(study / filename) != expected:
            errors.append("STUDY_HASH_MISMATCH:" + filename)
    for role, (filename, _repo_path, expected) in freeze["input_files"].items():
        if digest(inputs / filename) != expected:
            errors.append("INPUT_HASH_MISMATCH:" + role)
    if digest(inputs / "MANIFEST.json") != freeze["manifest_sha256"]:
        errors.append("MANIFEST_HASH_MISMATCH")
    receipt = json.loads(Path("/runtime/receipt.json").read_text(encoding="utf-8"))
    if receipt != raw["observed_host_runtime"]:
        errors.append("HOST_RECEIPT_RAW_MISMATCH")
    if receipt != {key: value for key, value in freeze["expected_runtime"].items() if key != "python"}:
        errors.append("HOST_RUNTIME_EXPECTATION_MISMATCH")
    if raw["observed_container_python"] != freeze["expected_runtime"]["python"]:
        errors.append("PYTHON_EXPECTATION_MISMATCH")
    if raw["decision"] != "PASS_RUNTIME_BOUND_AUDIT_SCOPED":
        errors.append("FORMAL_DECISION_NOT_PASS")
    if raw["baseline"]["decision"] != "PASS_RESULT_LEDGER_BINDING_SCOPED" or raw["baseline"]["errors"]:
        errors.append("BASELINE_NOT_CLEAN")
    if set(raw["ledger_controls"]) != {"drop_input_row", "input_digest", "input_path"} or not all(row["rejected"] for row in raw["ledger_controls"].values()):
        errors.append("LEDGER_MUTATION_CONTROLS_INVALID")
    if set(raw["runtime_mismatch_controls"]) != {"docker_engine", "daemon_platform", "image_id", "image_platform", "python"}:
        errors.append("RUNTIME_CONTROL_FIELD_SET_INVALID")
    if not all(row["stopped"] and not row["semantic_audit_invoked"] and row["decision"] == "STOP_PROVENANCE_OR_ENVIRONMENT" for row in raw["runtime_mismatch_controls"].values()):
        errors.append("RUNTIME_MISMATCH_CONTROL_ESCAPED")
    result = {
        "schema": "issue4682-independent-audit-v1",
        "decision": "PASS_INDEPENDENT_AUDIT" if not errors else "FAIL_INDEPENDENT_AUDIT",
        "errors": errors,
        "formal_audit_sha256": digest(output),
        "input_manifest_sha256": digest(inputs / "MANIFEST.json"),
        "inputs_verified": len(freeze["input_files"]),
        "source_files_verified": len(freeze["source_sha256"]),
        "scope": "raw receipt/result/hash consistency; does not execute semantic auditor",
    }
    Path("/evidence/INDEPENDENT_AUDIT.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
