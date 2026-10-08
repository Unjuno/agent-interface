"""Independent audit of a retained #5225 audit matrix (stdlib only)."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess


HERE = Path(__file__).resolve().parent
ROOT = next(parent for parent in HERE.parents if (parent / ".git").exists())


def main() -> int:
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    manifest = json.loads((HERE / "evidence" / "MANIFEST.json").read_text(encoding="utf-8"))
    capture = HERE / "evidence" / "audit-matrix.json"
    result = json.loads(capture.read_text(encoding="utf-8"))
    expected_fields = {
        "execution_end_700", "execution_end_999", "execution_end_1000",
        "execution_end_1001", "execution_wrong_command", "effect_at_499",
        "effect_at_699", "effect_at_700", "effect_at_701", "effect_at_900",
    }
    expected_mutations = {
        (field, mutation)
        for field in expected_fields
        for mutation in ("missing", "null", "string", "integer")
    }
    rows = result.get("mutation_matrix")
    observed_mutations = {(row.get("key"), row.get("mutation")) for row in rows or []}
    checks = {
        "base_main_matches_freeze": result.get("base_main") == freeze.get("base_main"),
        "legacy_audit_reproduced": result.get("legacy_audit_reproduced") is True,
        "legacy_stored_result_preserved": result.get("legacy_stored_disposition")
            == "PASS_TEMPORAL_RECEIPT_GAP_SCOPED",
        "three_legacy_false_no_gap_controls": result.get(
            "legacy_copied_control_false_no_gap") == {
                "remove": True, "null": True, "string": True},
        "original_record_holds_incomplete": result.get("strict_original_record", {}).get(
            "disposition") == "HOLD_SCHEMA",
        "complete_schema_holds_ambiguous_contract": result.get(
            "strict_complete_schema_control", {}).get("disposition")
            == "HOLD_CONTRACT_AMBIGUITY",
        "invented_effect_900_holds": result.get(
            "effect_at_900_injected_without_frozen_provenance", {}).get(
                "disposition") == "HOLD_SCHEMA",
        "all_40_mutations_present_once": len(rows or []) == 40
            and observed_mutations == expected_mutations,
        "all_mutations_fail_closed": bool(rows) and all(
            row.get("disposition") == "HOLD_SCHEMA" for row in rows),
        "scoped_disposition": result.get("disposition") == "PASS_AUDITOR_GAP_SCOPED",
        "manifest_main_matches_freeze": manifest.get("base_main") == freeze.get("base_main"),
        "manifest_matrix_hash_matches": manifest.get("audit_matrix", {}).get("sha256")
            == hashlib.sha256(capture.read_bytes()).hexdigest(),
    }
    study_source_checks = {}
    for relative, expected in manifest.get("study_source_sha256", {}).items():
        digest = hashlib.sha256((HERE / relative).read_bytes()).hexdigest()
        study_source_checks[relative] = digest == expected
    checks["all_study_sources_match_manifest"] = bool(study_source_checks) and all(
        study_source_checks.values())
    pin_checks = {}
    for relative, pin in freeze["sources"].items():
        raw = (ROOT / Path(relative)).read_bytes()
        blob = subprocess.check_output(
            ["git", "rev-parse", f"{freeze['base_main']}:{relative}"],
            cwd=ROOT, text=True).strip()
        pin_checks[relative] = {
            "sha256_matches": hashlib.sha256(raw).hexdigest() == pin["sha256"],
            "git_blob_matches": blob == pin["git_blob"],
        }
    checks["all_frozen_source_pins_match"] = all(
        row["sha256_matches"] and row["git_blob_matches"]
        for row in pin_checks.values())
    report = {"checks": checks, "source_pin_checks": pin_checks,
              "study_source_checks": study_source_checks,
              "audit_matrix_sha256": hashlib.sha256(capture.read_bytes()).hexdigest(),
              "passed": all(checks.values()),
              "scope": "independent result integrity check; no kernel/probe rerun"}
    print(json.dumps(report, sort_keys=True, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
