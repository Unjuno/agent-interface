"""Independent provenance and decision audit for the retained #4667 row."""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import pathlib
import re
import zipfile

ALLOCATION = "calc-effect-contract-34-document-window-20260927-01"
IMAGE = "issue-2849-task1-runtime@sha256:436172d89b145c6a9f9a57e655422c9558b3b0235347dd77607e9d61bcfa6393"
DOCUMENT_TITLE = "document-window-probe.xlsx - LibreOffice Calc"
VCL_TITLE = "VCL ImplGetDefaultWindow"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_xlsx(raw_path: pathlib.Path, raw: dict) -> tuple[bytes, str]:
    source = raw_path.parent / raw["source_file"]
    if source.is_file():
        return source.read_bytes(), "xlsx"
    encoded = source.with_name(source.name + ".b64")
    return base64.b64decode(encoded.read_bytes(), validate=True), "base64"


def parse_windows(raw: dict) -> tuple[list[dict], list[str]]:
    errors: list[str] = []
    tree = raw.get("root_tree")
    ids = raw.get("root_child_ids")
    records = raw.get("child_window_attributes")
    if not isinstance(tree, dict) or tree.get("exit") != 0:
        return [], ["root window-tree command missing or failed"]
    tree_text = tree.get("stdout")
    if not isinstance(tree_text, str):
        return [], ["root window-tree output missing or malformed"]
    tree_ids = re.findall(r"^\s+(0x[0-9a-fA-F]+)\b", tree_text, re.MULTILINE)
    count = re.search(r"^\s*(\d+) children:\s*$", tree_text, re.MULTILINE)
    if count is None or int(count.group(1)) != len(tree_ids):
        errors.append("root-tree child count does not reconcile")
    if not isinstance(ids, list) or not ids or any(not isinstance(x, str) or re.fullmatch(r"0x[0-9a-fA-F]+", x) is None for x in ids):
        errors.append("raw root-child ID inventory missing or malformed")
        ids = []
    if ids != tree_ids or len(set(ids)) != len(ids):
        errors.append("raw root-child IDs do not exactly match unique tree IDs")
    if not isinstance(records, list):
        errors.append("child-window attributes inventory missing")
        records = []
    record_ids = [item.get("window_id") if isinstance(item, dict) else None for item in records]
    ids_are_strings = all(isinstance(x, str) for x in record_ids)
    if record_ids != ids or (ids_are_strings and len(set(record_ids)) != len(record_ids)):
        errors.append("child-window query inventory does not exactly match tree order")

    parsed = []
    for item in records:
        if not isinstance(item, dict):
            continue
        wid = item.get("window_id")
        stdout = item.get("stdout", "")
        if not isinstance(stdout, str):
            stdout = ""
        receipt = re.search(r"^xwininfo: Window id: (0x[0-9a-fA-F]+)(?: \"(.*)\"| \(has no name\))$", stdout, re.MULTILINE)
        state = re.search(r"^\s*Map State: (IsViewable|IsUnMapped|IsUnviewable)\s*$", stdout, re.MULTILINE)
        if item.get("exit") != 0 or receipt is None or receipt.group(1) != wid:
            errors.append(f"failed or mismatched xwininfo receipt for {wid}")
        if state is None:
            errors.append(f"window map state missing or unknown for {wid}")
        parsed.append({
            "window_id": wid,
            "title": receipt.group(2) if receipt and receipt.lastindex == 2 else None,
            "map_state": state.group(1) if state else None,
        })
    return parsed, errors


def audit_values(raw: dict, frozen: dict, disk_value: object, source_hash: str, raw_hash: str, frozen_hash: str) -> dict:
    errors: list[str] = []
    if raw.get("schema") != "calc-effect-contract-document-window-raw-v1": errors.append("raw schema mismatch")
    if raw.get("allocation") != ALLOCATION: errors.append("allocation identity mismatch")
    if raw.get("image") != IMAGE: errors.append("pinned image identity mismatch")
    if raw.get("source_file") != "document-window-probe.xlsx": errors.append("source file identity mismatch")
    if raw.get("harness_completed") is not True: errors.append("harness completion missing")
    if raw.get("cell_before_edit") != 0 or raw.get("cell_after_edit_live") != 7: errors.append("live cell transition mismatch")
    if raw.get("document_modified_unsaved") is not True or raw.get("save_store_calls") != 0: errors.append("unsaved/no-save gate mismatch")
    if raw.get("persisted_cell_after_independent_reopen") != 0 or disk_value != 0: errors.append("independently saved A1 value mismatch")
    if not source_hash or source_hash != raw.get("source_sha256_before") or source_hash != raw.get("source_sha256_after"):
        errors.append("independent source hash mismatch")

    parsed, window_errors = parse_windows(raw)
    errors.extend(window_errors)
    documents = [w for w in parsed if w["title"] == DOCUMENT_TITLE]
    helpers = [w for w in parsed if w["title"] == VCL_TITLE]
    if len(documents) != 1: errors.append("document-titled window missing or ambiguous")
    if len(helpers) != 1: errors.append("VCL helper window missing or ambiguous")

    if frozen.get("raw_sha256") != raw_hash: errors.append("frozen audit is not bound to this raw file")
    if frozen.get("source_sha256_independent") != source_hash: errors.append("frozen audit source hash mismatch")
    if frozen.get("independently_reopened_A1") != disk_value: errors.append("frozen audit disk value mismatch")
    if frozen.get("schema") != "calc-effect-contract-document-window-audit-v1": errors.append("frozen audit schema mismatch")

    if errors:
        disposition = "STOP_CONSTRUCTION"
    elif documents[0]["map_state"] == "IsViewable":
        disposition = "PASS_DOCUMENT_WINDOW_VISIBLE_CONSTRUCTION_ONLY"
    elif documents[0]["map_state"] in {"IsUnMapped", "IsUnviewable"}:
        disposition = "CONTRADICTED_DOCUMENT_WINDOW_VISIBILITY"
    else:
        disposition = "STOP_CONSTRUCTION"
        errors.append("document window state is not recognized")

    return {
        "schema": "calc-effect-contract-document-window-posthoc-audit-v1",
        "raw_sha256": raw_hash,
        "frozen_audit_sha256": frozen_hash,
        "source_sha256_independent": source_hash,
        "independently_reopened_A1": disk_value,
        "document_windows": documents,
        "vcl_helper_windows": helpers,
        "parsed_child_count": len(parsed),
        "errors": errors,
        "disposition": disposition,
        "formal_allocation_cases": 0,
        "claim_limit": "posthoc integrity and decision audit of one construction row; not formal Issue 34 or runtime evidence",
    }


def audit(raw_path: pathlib.Path, frozen_path: pathlib.Path) -> dict:
    raw_bytes = raw_path.read_bytes()
    raw = json.loads(raw_bytes)
    frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
    try:
        data, _mode = read_xlsx(raw_path, raw)
        from openpyxl import load_workbook
        wb = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
        value = wb.active["A1"].value
        wb.close()
        source_hash = sha256(data)
    except (KeyError, OSError, ValueError, TypeError, zipfile.BadZipFile):
        value, source_hash = None, ""
    return audit_values(raw, frozen, value, source_hash, sha256(raw_bytes), sha256(frozen_path.read_bytes()))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=pathlib.Path, required=True)
    parser.add_argument("--frozen-audit", type=pathlib.Path, required=True)
    parser.add_argument("--out", type=pathlib.Path, required=True)
    args = parser.parse_args()
    if args.out.exists(): raise FileExistsError(f"refusing to overwrite {args.out}")
    result = audit(args.raw, args.frozen_audit)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["disposition"].startswith("PASS") else (1 if result["disposition"].startswith("CONTRADICTED") else 2)


if __name__ == "__main__":
    raise SystemExit(main())
