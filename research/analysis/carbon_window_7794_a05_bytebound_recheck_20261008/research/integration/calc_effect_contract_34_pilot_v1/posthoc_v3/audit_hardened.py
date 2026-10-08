"""Strict posthoc audit of Issue #4626 retained evidence and base64 artifact."""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import pathlib
import re
import zipfile

ALLOCATION = "calc-effect-contract-34-pilot-20260927-01"
IMAGE = "issue-2849-task1-runtime@sha256:436172d89b145c6a9f9a57e655422c9558b3b0235347dd77607e9d61bcfa6393"
CLASSIFICATIONS = {
    "program_terminal_shortcut": "VERIFIED",
    "live_required_effect_shortcut": "VERIFIED",
    "saved_effect_contract": "CONTRADICTED",
}


def read_workbook(raw_path: pathlib.Path, raw: dict) -> tuple[bytes, str]:
    source = raw_path.parent / raw["source_file"]
    if source.is_file():
        return source.read_bytes(), "xlsx"
    encoded = source.with_name(source.name + ".b64")
    return base64.b64decode(encoded.read_bytes(), validate=True), "base64"


def evidence_errors(raw: dict, disk_cell: object, hash_stable: bool) -> list[str]:
    errors = []
    ids = raw.get("visible_calc_window_ids")
    if type(ids) is not list or not ids:
        errors.append("visible Calc window evidence must be a non-empty list")
    elif any(not isinstance(x, str) or re.fullmatch(r"0x[0-9a-fA-F]+", x) is None for x in ids):
        errors.append("visible Calc window evidence contains malformed XIDs")
    if raw.get("allocation") != ALLOCATION: errors.append("allocation identity mismatch")
    if raw.get("image") != IMAGE: errors.append("pinned image identity mismatch")
    if raw.get("source_file") != "baseline.xlsx": errors.append("source file identity mismatch")
    if raw.get("program_completed") is not True: errors.append("harness completion missing")
    if raw.get("cell_before_edit") != 0 or raw.get("cell_after_edit_live") != 7: errors.append("live transition mismatch")
    if raw.get("document_modified_unsaved") is not True or raw.get("save_store_calls") != 0: errors.append("unsaved condition mismatch")
    if raw.get("raw_classifications") != CLASSIFICATIONS: errors.append("shortcut/saved-effect classification missing or inconsistent")
    if disk_cell != 0 or raw.get("persisted_cell_after_independent_reopen") != 0: errors.append("independent disk value mismatch")
    if not hash_stable: errors.append("source workbook hash mismatch")
    return errors


def disposition(errors: list[str]) -> str:
    return "STOP_CONSTRUCTION" if errors else "PASS_CALC_PERSISTENCE_BOUNDARY_CONSTRUCTION_ONLY"


def audit(raw_path: pathlib.Path) -> dict:
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    errors = []
    source_mode, disk_cell, current = "unavailable", None, None
    try:
        data, source_mode = read_workbook(raw_path, raw)
        from openpyxl import load_workbook
        wb = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
        disk_cell = wb.active["A1"].value
        wb.close()
        current = hashlib.sha256(data).hexdigest()
    except (KeyError, OSError, ValueError, zipfile.BadZipFile):
        errors.append("independent workbook evidence missing or invalid")
    stable = bool(current and raw.get("source_sha256_before") == raw.get("source_sha256_after") == current)
    errors.extend(evidence_errors(raw, disk_cell, stable))
    return {
        "schema": "calc-effect-contract-hardened-audit-v3",
        "raw_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
        "source_sha256_independent": current,
        "source_read_mode": source_mode,
        "independently_reopened_A1": disk_cell,
        "visibility_evidence_valid": not any("visible Calc window" in e or "XIDs" in e for e in errors),
        "errors": errors,
        "disposition": disposition(errors),
        "formal_allocation_cases": 0,
        "claim_limit": "posthoc integrity audit of one construction row; not runtime or formal Issue 34 evidence",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=pathlib.Path, required=True)
    parser.add_argument("--out", type=pathlib.Path, required=True)
    args = parser.parse_args()
    if args.out.exists(): raise FileExistsError(f"refusing to overwrite {args.out}")
    result = audit(args.raw)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["disposition"].startswith("PASS") else 2


if __name__ == "__main__":
    raise SystemExit(main())
