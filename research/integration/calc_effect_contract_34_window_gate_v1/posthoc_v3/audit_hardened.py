"""Superseding classification of #4643 evidence, with evidence-backed outcomes."""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import pathlib
import re
import zipfile

IMAGE = "issue-2849-task1-runtime@sha256:436172d89b145c6a9f9a57e655422c9558b3b0235347dd77607e9d61bcfa6393"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def visibility_state(raw: dict) -> str:
    tree = json.loads(raw.get("xwininfo_root_tree") or "{}")
    wid = raw.get("vcl_window_id")
    attrs = json.loads(raw.get("xwininfo_window_attributes") or "{}") if raw.get("xwininfo_window_attributes") else {}
    if tree.get("exit") != 0 or not wid or len(re.findall(r"0x[0-9a-fA-F]+ \"VCL ImplGetDefaultWindow\"", tree.get("stdout", ""))) != 1:
        return "UNKNOWN"
    if attrs.get("exit") != 0 or f"Window id: {wid}" not in attrs.get("stdout", ""):
        return "UNKNOWN"
    match = re.search(r"Map State:\s*(IsViewable|IsUnMapped|IsUnviewable)", attrs["stdout"])
    return match.group(1) if match else "UNKNOWN"


def read_workbook(raw_path: pathlib.Path, raw: dict) -> tuple[bytes, str]:
    source = raw_path.parent / raw["source_file"]
    if source.is_file():
        return source.read_bytes(), "xlsx"
    encoded = source.with_name(source.name + ".b64")
    return base64.b64decode(encoded.read_bytes(), validate=True), "base64"


def classify(raw: dict, map_state: str, disk_cell: object, hash_stable: bool, errors: list[str]) -> str:
    if (raw.get("allocation") != "calc-effect-contract-34-window-gate-20260927-01"
            or raw.get("image") != IMAGE
            or raw.get("harness_completed") is not True):
        return "STOP_CONSTRUCTION"
    if map_state in {"IsUnMapped", "IsUnviewable"}:
        return "CONTRADICTED_WINDOW_VISIBILITY"
    if map_state != "IsViewable":
        return "STOP_CONSTRUCTION"
    if errors:
        return "STOP_CONSTRUCTION"
    if raw.get("cell_after_edit_live") != 7 or disk_cell != 0 or not hash_stable:
        return "CONTRADICTED_EFFECT_STATE" if disk_cell is not None and hash_stable else "STOP_CONSTRUCTION"
    if map_state != "IsViewable":
        return "STOP_CONSTRUCTION"
    return "PASS_WINDOW_GATED_CONSTRUCTION_ONLY"


def audit(raw_path: pathlib.Path) -> dict:
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    errors = []
    data = None
    source_mode = "unavailable"
    disk_cell = None
    current = None
    try:
        data, source_mode = read_workbook(raw_path, raw)
        from openpyxl import load_workbook

        wb = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
        disk_cell = wb.active["A1"].value
        wb.close()
        current = sha256_bytes(data)
    except (KeyError, OSError, ValueError, zipfile.BadZipFile):
        errors.append("independent workbook evidence missing or invalid")
    stable = bool(raw.get("source_sha256_before") and raw.get("source_sha256_before") == raw.get("source_sha256_after") == current)
    state = visibility_state(raw)
    if raw.get("allocation") != "calc-effect-contract-34-window-gate-20260927-01": errors.append("allocation mismatch")
    if raw.get("image") != IMAGE: errors.append("pinned image mismatch")
    if raw.get("harness_completed") is not True: errors.append("harness completion missing")
    if raw.get("source_file") != "baseline.xlsx": errors.append("source file identity mismatch")
    if raw.get("cell_before_edit") != 0 or raw.get("cell_after_edit_live") != 7: errors.append("live transition mismatch")
    if raw.get("document_modified_unsaved") is not True or raw.get("save_store_calls") != 0: errors.append("unsaved document condition mismatch")
    if disk_cell != 0 or raw.get("persisted_cell_after_independent_reopen") != 0: errors.append("independent disk value mismatch")
    if not stable: errors.append("source hash mismatch")
    if state == "UNKNOWN": errors.append("window map state evidence missing or invalid")
    return {
        "schema": "calc-effect-contract-window-gate-audit-v2",
        "raw_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
        "source_sha256_independent": current,
        "source_read_mode": source_mode,
        "independently_reopened_A1": disk_cell,
        "window_map_state": state,
        "errors": errors,
        "disposition": classify(raw, state, disk_cell, stable, errors),
        "formal_allocation_cases": 0,
        "claim_limit": "posthoc reclassification of one synthetic construction case; not formal Issue 34 or runtime evidence",
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
    return 0 if result["disposition"].startswith("PASS") else (2 if result["disposition"].startswith("STOP") else 1)


if __name__ == "__main__":
    raise SystemExit(main())
