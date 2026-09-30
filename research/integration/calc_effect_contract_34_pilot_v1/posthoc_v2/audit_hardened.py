"""Additive hardened audit of retained Issue #4626 evidence; never overwrites v1."""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re

from openpyxl import load_workbook


def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def visibility_errors(raw: dict) -> list[str]:
    ids = raw.get("visible_calc_window_ids")
    if type(ids) is not list or not ids:
        return ["visible Calc window evidence must be a non-empty list"]
    if any(not isinstance(item, str) or re.fullmatch(r"0x[0-9a-fA-F]+", item) is None for item in ids):
        return ["visible Calc window evidence contains an invalid window ID"]
    return []


def audit(raw_path: pathlib.Path) -> dict:
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    errors = visibility_errors(raw)
    if raw.get("cell_before_edit") != 0 or raw.get("cell_after_edit_live") != 7:
        errors.append("live transition did not match 0 -> 7")
    if raw.get("document_modified_unsaved") is not True or raw.get("save_store_calls") != 0:
        errors.append("unsaved document condition did not reconcile")
    if raw.get("program_completed") is not True:
        errors.append("harness completion did not reconcile")
    source = raw_path.parent / raw["source_file"]
    wb = load_workbook(source, read_only=True, data_only=True)
    disk_cell = wb.active["A1"].value
    wb.close()
    current = sha256(source)
    stable = bool(raw.get("source_sha256_before") and raw.get("source_sha256_before") == raw.get("source_sha256_after") == current)
    if disk_cell != 0 or raw.get("persisted_cell_after_independent_reopen") != 0:
        errors.append("independent saved A1 was not zero")
    if not stable:
        errors.append("independent workbook hash did not match stable before/after hashes")
    return {
        "schema": "calc-effect-contract-hardened-audit-v1",
        "raw_sha256": sha256(raw_path),
        "source_sha256_independent": current,
        "independently_reopened_A1": disk_cell,
        "visibility_evidence_valid": not visibility_errors(raw),
        "errors": errors,
        "disposition": "PASS_CALC_PERSISTENCE_BOUNDARY_CONSTRUCTION_ONLY" if not errors else "STOP_CONSTRUCTION",
        "formal_allocation_cases": 0,
        "claim_limit": "posthoc audit of one retained construction row; not runtime or formal Issue 34 evidence",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=pathlib.Path, required=True)
    parser.add_argument("--out", type=pathlib.Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError(f"refusing to overwrite {args.out}")
    result = audit(args.raw)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if not result["errors"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
