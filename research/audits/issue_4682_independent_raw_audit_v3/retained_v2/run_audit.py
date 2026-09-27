"""Single raw audit with host-observed runtime identity and fail-closed gates."""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

from audit_ledger import audit, derive_input_ledger
from runtime_guard import RUNTIME_FIELDS, validate_runtime


STUDY = Path("/study")
INPUTS = Path("/inputs")
OUTPUT = Path("/out/formal01")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=False)
    freeze_bytes = (STUDY / "FREEZE.json").read_bytes()
    freeze = json.loads(freeze_bytes)
    runtime_receipt = json.loads(Path("/runtime/receipt.json").read_text(encoding="utf-8"))
    expected_runtime = freeze["expected_runtime"]
    runtime_errors = validate_runtime(runtime_receipt, expected_runtime, ".".join(map(str, sys.version_info[:3])))

    # Predeclared one-field adversarial controls exercise the same pure guard.
    mismatch_controls = {}
    for field in RUNTIME_FIELDS:
        altered_receipt = copy.deepcopy(runtime_receipt)
        altered_python = ".".join(map(str, sys.version_info[:3]))
        if field == "python":
            altered_python = "0.0.0"
        else:
            altered_receipt[field] = "mismatch"
        errors = validate_runtime(altered_receipt, expected_runtime, altered_python)
        mismatch_controls[field] = {
            "stopped": bool(errors),
            "errors": errors,
            "semantic_audit_invoked": False,
            "decision": "STOP_PROVENANCE_OR_ENVIRONMENT" if errors else "UNEXPECTED_PASS",
        }

    integrity_errors = []
    if sha256(freeze_bytes) != (STUDY / "FREEZE.sha256").read_text(encoding="ascii").split()[0]:
        integrity_errors.append("FREEZE_SIDECAR_MISMATCH")
    for filename, expected in freeze["source_sha256"].items():
        if sha256((STUDY / filename).read_bytes()) != expected:
            integrity_errors.append("SOURCE_SHA256_MISMATCH:" + filename)
    for filename, expected in freeze["study_sha256"].items():
        if sha256((STUDY / filename).read_bytes()) != expected:
            integrity_errors.append("STUDY_SHA256_MISMATCH:" + filename)

    manifest_bytes = (INPUTS / "MANIFEST.json").read_bytes()
    actual_ledger, input_errors = derive_input_ledger(INPUTS)
    if sha256(manifest_bytes) != freeze["manifest_sha256"]:
        input_errors.append("MANIFEST_SHA256_MISMATCH")
    for role, row in actual_ledger.items():
        if freeze["input_sha256"].get(role) != row["sha256"]:
            input_errors.append("FREEZE_INPUT_SHA256_MISMATCH:" + role)

    identity_errors = runtime_errors + integrity_errors + input_errors
    baseline = None
    controls = {}
    if not identity_errors:
        baseline_envelope = {"input_sha256": copy.deepcopy(actual_ledger)}
        baseline = audit(INPUTS, baseline_envelope)
        mutations = {}
        dropped = copy.deepcopy(baseline_envelope)
        dropped["input_sha256"].pop("accepted", None)
        mutations["drop_input_row"] = audit(INPUTS, dropped)
        changed = copy.deepcopy(baseline_envelope)
        changed["input_sha256"]["accepted"]["sha256"] = "0" * 64
        mutations["input_digest"] = audit(INPUTS, changed)
        wrong_path = copy.deepcopy(baseline_envelope)
        wrong_path["input_sha256"]["audit_plan"]["path"] = "PLAN.md"
        mutations["input_path"] = audit(INPUTS, wrong_path)
        controls = {
            name: {
                "rejected": row["decision"] == "FAIL_RESULT_LEDGER_BINDING" and bool(row["errors"]),
                "decision": row["decision"],
                "errors": row["errors"],
            }
            for name, row in mutations.items()
        }

    mismatch_pass = any(not row["stopped"] for row in mismatch_controls.values())
    if identity_errors:
        decision = "STOP_PROVENANCE_OR_ENVIRONMENT"
    elif mismatch_pass:
        decision = "FAIL_RUNTIME_MISMATCH_ACCEPTED"
    elif baseline["decision"] == "PASS_RESULT_LEDGER_BINDING_SCOPED" and all(row["rejected"] for row in controls.values()):
        decision = "PASS_RUNTIME_BOUND_AUDIT_SCOPED"
    else:
        decision = "FAIL_RESULT_LEDGER_BINDING"

    result = {
        "schema": "issue4665-runtime-provenance-v2",
        "issue": 4682,
        "allocation": freeze["allocation"],
        "decision": decision,
        "expected_runtime": expected_runtime,
        "observed_host_runtime": runtime_receipt,
        "observed_container_python": ".".join(map(str, sys.version_info[:3])),
        "runtime_errors": runtime_errors,
        "identity_errors": identity_errors,
        "baseline": baseline,
        "ledger_controls": controls,
        "runtime_mismatch_controls": mismatch_controls,
        "invocations": {"formal_container": 1, "semantic_audit": 4 if baseline else 0, "predecessor_runner": 0, "predecessor_auditor": 0},
        "scope": "synthetic-ledger-and-runtime-provenance-only; no predecessor formal replay",
    }
    (OUTPUT / "AUDIT.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"decision": decision, "runtime_errors": runtime_errors, "mismatch_controls": mismatch_controls}, sort_keys=True))
    return 0 if decision == "PASS_RUNTIME_BOUND_AUDIT_SCOPED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
