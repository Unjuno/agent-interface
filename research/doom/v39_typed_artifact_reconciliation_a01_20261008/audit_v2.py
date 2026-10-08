import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE_ROOT = Path(os.environ.get("SOURCE_ROOT", ROOT))
RESULT = ROOT / "results" / "a01" / "RESULT.json"
AUDIT = RESULT.with_name("AUDIT_V2.json")
if AUDIT.exists():
    raise SystemExit("STOP_AUDIT_OUTPUT_EXISTS")

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    freeze_path = ROOT / "FREEZE.json"
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    raw_bytes = RESULT.read_bytes()
    raw = json.loads(raw_bytes)
    checks = {}
    for rel, expected in freeze["sha256"].items():
        base = ROOT if rel in ("probe.py", "audit.py", "PREREGISTRATION.md") else SOURCE_ROOT
        checks[f"frozen_file:{rel}"] = sha256(base / rel) == expected
    source_path = "research/doom/doom_typed_observation_v1.py"
    checks["source_commit"] = raw.get("source_commit") == freeze["source_commit"]
    checks["source_blob"] = (
        raw.get("source_blob") == freeze["source_files"][source_path]["git_blob"]
    )
    rows = raw.get("rows")
    names = [
        "control_exact", "id_bool_int_alias", "step_bool_int_alias",
        "sequence_bool_int_alias", "capture_bool_int_alias",
        "binding_nested_bool_int_alias",
    ]
    checks["case_names_and_order"] = (
        type(rows) is list and [row.get("case") for row in rows] == names
    )
    checks["control_reconstructed"] = (
        type(rows) is list and rows[0].get("matched") is True and
        type(rows[0].get("checks")) is dict and
        all(value is True for value in rows[0]["checks"].values())
    )
    actual_aliases = [row["case"] for row in rows[1:] if row.get("matched") is True]
    checks["alias_summary"] = raw.get("accepted_aliases") == actual_aliases
    expected_result = (
        "FAIL_BOOL_INT_ALIAS_ACCEPTED" if actual_aliases
        else "PASS_EXACT_IDENTITY" if checks["control_reconstructed"]
        else "HOLD_CONTROL_REJECTED"
    )
    checks["result_label"] = raw.get("result") == expected_result
    checks["all_five_aliases_reconstructed"] = actual_aliases == names[1:]
    audit = {
        "schema": "issue8566-reconcile-alias-a01-audit-v2",
        "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "checks": checks,
        "passed": all(checks.values()),
        "experimental_result": raw.get("result"),
        "accepted_aliases": actual_aliases,
        "supersedes": "AUDIT_INITIAL_FAILURE.json; original audit.py and initial failure are retained",
        "audit_scope": "source/raw integrity and deterministic row reconstruction; not a second experiment",
    }
    AUDIT.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n",
                     encoding="utf-8")
    print(json.dumps({
        "passed": audit["passed"],
        "experimental_result": audit["experimental_result"],
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "raw_sha256": audit["raw_sha256"],
    }, sort_keys=True))
    if not audit["passed"]:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
