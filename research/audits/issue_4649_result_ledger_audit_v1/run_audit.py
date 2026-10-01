"""One-shot offline audit and two preregistered result-ledger corruptions."""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

from audit_ledger import audit, derive_input_ledger


def main() -> int:
    inputs = Path("/inputs")
    study = Path("/study")
    output = Path("/out/formal01")
    output.mkdir(parents=True, exist_ok=False)
    freeze_bytes = (study / "FREEZE.json").read_bytes()
    freeze = json.loads(freeze_bytes)
    identity_errors = []
    digest = lambda data: hashlib.sha256(data).hexdigest()
    sidecar = (study / "FREEZE.sha256").read_text(encoding="ascii").split()[0]
    if digest(freeze_bytes) != sidecar:
        identity_errors.append("FREEZE_SIDECAR_MISMATCH")
    if digest((study / "PLAN.md").read_bytes()) != freeze.get("plan_sha256"):
        identity_errors.append("PLAN_SHA256_MISMATCH")
    if digest((study / "ENVIRONMENT.json").read_bytes()) != freeze.get("environment_sha256"):
        identity_errors.append("ENVIRONMENT_SHA256_MISMATCH")
    for filename, expected in freeze.get("source_sha256", {}).items():
        if digest((study / filename).read_bytes()) != expected:
            identity_errors.append("SOURCE_SHA256_MISMATCH:" + filename)
    manifest = inputs / "MANIFEST.json"
    manifest_actual = hashlib.sha256(manifest.read_bytes()).hexdigest()
    actual_ledger, input_errors = derive_input_ledger(inputs)
    if manifest_actual != freeze.get("manifest_sha256"):
        input_errors.append("MANIFEST_SHA256_MISMATCH")
    for role, row in actual_ledger.items():
        if freeze.get("input_sha256", {}).get(role) != row["sha256"]:
            input_errors.append("FREEZE_INPUT_SHA256_MISMATCH:" + role)
    baseline_envelope = {"input_sha256": copy.deepcopy(actual_ledger)}
    baseline = audit(inputs, baseline_envelope)
    identity_errors.extend(input_errors)

    mutations = {}
    dropped = copy.deepcopy(baseline_envelope)
    dropped["input_sha256"].pop("accepted", None)
    mutations["drop_input_row"] = audit(inputs, dropped)

    changed = copy.deepcopy(baseline_envelope)
    changed["input_sha256"]["accepted"]["sha256"] = "0" * 64
    mutations["input_digest"] = audit(inputs, changed)

    wrong_path = copy.deepcopy(baseline_envelope)
    wrong_path["input_sha256"]["audit_plan"]["path"] = "PLAN.md"
    mutations["input_path"] = audit(inputs, wrong_path)

    controls = {
        name: {
            "rejected": row["decision"] == "FAIL_RESULT_LEDGER_BINDING" and bool(row["errors"]),
            "decision": row["decision"],
            "errors": row["errors"],
        }
        for name, row in mutations.items()
    }
    result = {
        "schema": "issue4665-result-ledger-audit-v1",
        "issue": 4665,
        "allocation": "issue4649-result-ledger-audit-20260927-01",
        "decision": (
            "STOP_PROVENANCE_OR_ENVIRONMENT" if identity_errors else
            "PASS_RESULT_LEDGER_BINDING_SCOPED"
            if baseline["decision"] == "PASS_RESULT_LEDGER_BINDING_SCOPED"
            and all(row["rejected"] for row in controls.values())
            else "FAIL_RESULT_LEDGER_BINDING"
        ),
        "docker_engine": "28.5.1",
        "image_id": "sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9",
        "execution_platform": "linux/amd64",
        "python": sys.version,
        "manifest_sha256": manifest_actual,
        "input_errors": identity_errors,
        "baseline": baseline,
        "controls": controls,
        "invocations": {"audit": 1, "predecessor_runner": 0, "predecessor_auditor": 0},
        "scope": "ledger-binding-only; does not re-audit unpublished #4649 raw output ZIP",
    }
    (output / "AUDIT.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"decision": result["decision"], "controls": controls, "input_errors": input_errors}, sort_keys=True))
    return 0 if result["decision"] == "PASS_RESULT_LEDGER_BINDING_SCOPED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
