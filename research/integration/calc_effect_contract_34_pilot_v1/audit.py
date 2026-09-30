"""Independent disk-side audit; does not import the Calc runner or classifier."""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys

from openpyxl import load_workbook


def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main(raw_path: pathlib.Path) -> int:
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    source = raw_path.parent / raw["source_file"]
    wb = load_workbook(source, read_only=True, data_only=True)
    independently_read_value = wb.active["A1"].value
    wb.close()
    digest = sha256(source)
    errors = []
    if raw.get("allocation") != "calc-effect-contract-34-pilot-20260927-01":
        errors.append("allocation identity mismatch")
    if raw.get("cell_before_edit") != 0 or raw.get("cell_after_edit_live") != 7:
        errors.append("live transition did not match 0 -> 7")
    if raw.get("document_modified_unsaved") is not True:
        errors.append("Calc did not report an unsaved modification")
    if raw.get("save_store_calls") != 0:
        errors.append("save/store operation was recorded")
    if raw.get("program_completed") is not True:
        errors.append("program terminal was not recorded")
    if raw.get("visible_calc_window_ids") == []:
        errors.append("no visible Calc window was detected")
    if raw.get("source_sha256_before") != raw.get("source_sha256_after"):
        errors.append("source workbook hash changed")
    if digest != raw.get("source_sha256_before"):
        errors.append("independent current hash differs from baseline")
    if independently_read_value != 0 or raw.get("persisted_cell_after_independent_reopen") != 0:
        errors.append("saved workbook did not retain old A1=0")
    if raw.get("raw_classifications") != {
        "program_terminal_shortcut": "VERIFIED",
        "live_required_effect_shortcut": "VERIFIED",
        "saved_effect_contract": "CONTRADICTED",
    }:
        errors.append("raw policy classification mismatch")
    audit = {
        "schema": "calc-effect-contract-unsaved-boundary-audit-v1",
        "raw_sha256": sha256(raw_path),
        "source_sha256_independent": digest,
        "independently_reopened_A1": independently_read_value,
        "errors": errors,
        "disposition": "PASS_CALC_PERSISTENCE_BOUNDARY_CONSTRUCTION_ONLY"
        if not errors
        else "STOP_CONSTRUCTION",
        "formal_allocation_cases": 0,
        "claim_limit": "one unsaved Calc edit; not modal, model-facing, or integrated EffectContract evidence",
    }
    out = raw_path.parent / "audit.json"
    out.write_text(json.dumps(audit, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, sort_keys=True))
    return 0 if not errors else 2


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: audit.py /out/<run>/raw.json")
    raise SystemExit(main(pathlib.Path(sys.argv[1])))
