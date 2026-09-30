"""Freeze-check and retain a copied-data audit matrix; never runs the kernel probe."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys

from audit import REQUIRED_KEYS, adjudicate, mutate_one


HERE = Path(__file__).resolve().parent
ROOT = next(parent for parent in HERE.parents if (parent / ".git").exists())
FREEZE = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
INTAKE = ROOT / "runtime" / "results" / "kernel-time-intake-01"
SOURCE = INTAKE / "source"


def verify_sources() -> dict:
    verified = {}
    for relative, pin in FREEZE["sources"].items():
        path = ROOT / Path(relative)
        data = path.read_bytes()
        sha256 = hashlib.sha256(data).hexdigest()
        blob = subprocess.check_output(
            ["git", "rev-parse", f"{FREEZE['base_main']}:{relative}"],
            cwd=ROOT, text=True).strip()
        if sha256 != pin["sha256"] or blob != pin["git_blob"]:
            raise RuntimeError(f"frozen source identity mismatch: {relative}")
        verified[relative] = {"git_blob": blob, "sha256": sha256,
                              "verified": True}
    return verified


def main() -> int:
    pins = verify_sources()
    observed = json.loads((SOURCE / "probe-output.json").read_text(encoding="utf-8"))
    stored_legacy = json.loads(
        (SOURCE / "audit-output.json").read_text(encoding="utf-8"))
    legacy_stdout = subprocess.check_output(
        [sys.executable, str(SOURCE / "audit.py")], cwd=ROOT, text=True)
    legacy_reproduced = json.loads(legacy_stdout) == stored_legacy

    prior_intake = json.loads((INTAKE / "result.json").read_text(encoding="utf-8"))
    copied_controls = prior_intake["copied_record_controls"]
    legacy_false_no_gap = {
        mode: row.get("disposition") == "NO_GAP_OBSERVED"
        and row.get("errors") == []
        for mode, row in copied_controls.items()
    }
    if set(legacy_false_no_gap) != {"remove", "null", "string"}:
        raise RuntimeError("unexpected frozen copied-control inventory")

    boundary = FREEZE["boundary_contract"]
    original = adjudicate(observed, FREEZE["observed_probe_keys"], boundary)

    schema_control = {key: False for key in REQUIRED_KEYS}
    schema_control.update({"execution_end_700": True, "execution_end_999": True,
                           "effect_at_700": True, "effect_at_701": True,
                           "effect_at_900": True})
    schema_disposition = adjudicate(schema_control, sorted(schema_control), boundary)
    mutations = []
    for key in sorted(REQUIRED_KEYS):
        for mode in ("missing", "null", "string", "integer"):
            record, inventory = mutate_one(schema_control, key, mode)
            result = adjudicate(record, inventory, boundary)
            mutations.append({"key": key, "mutation": mode,
                              "disposition": result["disposition"],
                              "errors": result.get("errors", [])})

    injected = dict(observed, effect_at_900=True)
    injected_effect_900 = adjudicate(
        injected, FREEZE["observed_probe_keys"], boundary)
    passed = (legacy_reproduced and all(legacy_false_no_gap.values())
              and original["disposition"] == "HOLD_SCHEMA"
              and schema_disposition["disposition"] == "HOLD_CONTRACT_AMBIGUITY"
              and len(mutations) == len(REQUIRED_KEYS) * 4
              and all(row["disposition"] == "HOLD_SCHEMA" for row in mutations)
              and injected_effect_900["disposition"] == "HOLD_SCHEMA")
    output = {
        "allocation": FREEZE["allocation"],
        "base_main": FREEZE["base_main"],
        "source_pins": pins,
        "legacy_audit_reproduced": legacy_reproduced,
        "legacy_stored_disposition": stored_legacy["disposition"],
        "legacy_copied_control_false_no_gap": legacy_false_no_gap,
        "strict_original_record": original,
        "strict_complete_schema_control": schema_disposition,
        "effect_at_900_injected_without_frozen_provenance": injected_effect_900,
        "mutation_matrix": mutations,
        "mutation_controls": len(mutations),
        "disposition": "PASS_AUDITOR_GAP_SCOPED" if passed else "HOLD_SOURCE_OR_ORACLE",
        "scope": "retained evidence adjudication only; kernel probe and runtime were not executed or changed",
    }
    evidence = HERE / "evidence"
    evidence.mkdir(parents=True, exist_ok=False)
    (evidence / "audit-matrix.json").write_text(
        json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"disposition": output["disposition"],
                      "legacy_audit_reproduced": legacy_reproduced,
                      "legacy_false_no_gap_cases": sum(legacy_false_no_gap.values()),
                      "strict_original": original["disposition"],
                      "mutations": len(mutations),
                      "mutation_controls_held": sum(
                          row["disposition"] == "HOLD_SCHEMA" for row in mutations),
                      "evidence": str(evidence / "audit-matrix.json")},
                     sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
