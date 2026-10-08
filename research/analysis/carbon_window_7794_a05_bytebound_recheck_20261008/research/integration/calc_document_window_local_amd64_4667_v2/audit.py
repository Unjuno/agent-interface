"""Independent standard-library audit of the local-amd64 Calc raw record."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ALLOCATION = "calc-doc-window-local-amd64-4667-v2-20260927-01"
IMAGE_ID = "sha256:854f930b93be86111d80cca5268ee6423777ec21588de55a5fb717332993379d"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def disk_a1(path: Path) -> float | None:
    with zipfile.ZipFile(path, "r") as archive:
        sheet = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
    ns = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    value = sheet.find(".//s:c[@r='A1']/s:v", ns)
    return float(value.text) if value is not None else None


def audit(raw_path: Path) -> dict:
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    if raw.get("schema") != "calc-doc-window-local-amd64-raw-v1":
        errors.append("schema")
    if raw.get("allocation") != ALLOCATION or raw.get("container_image_id") != IMAGE_ID:
        errors.append("allocation_or_image_identity")
    if raw.get("container_platform") != "linux/amd64" or raw.get("harness_completed") is not True:
        errors.append("platform_or_harness")
    workbook = raw_path.parent / raw.get("workbook", "")
    if not workbook.is_file():
        errors.append("workbook_missing")
        actual_hash = None
        persisted = None
    else:
        data = workbook.read_bytes()
        actual_hash = sha256(data)
        try:
            persisted = disk_a1(workbook)
        except Exception:
            persisted = None
            errors.append("workbook_reopen_parse")
    before_hash = raw.get("workbook_sha256_before")
    after_hash = raw.get("workbook_sha256_after")
    if not before_hash or before_hash != after_hash or actual_hash != before_hash:
        errors.append("source_workbook_hash_changed_or_mismatch")
    if raw.get("live_a1_before") != 0 or raw.get("live_a1_after") != 7:
        errors.append("live_cell_transition")
    if raw.get("persisted_a1_after_independent_xlsx_read") != 0 or persisted != 0:
        errors.append("persisted_cell_not_baseline")
    if raw.get("document_modified_unsaved") is not True or raw.get("store_calls_after_initial_fixture_creation") != 0:
        errors.append("unsaved_boundary")

    windows = raw.get("root_tree_windows", [])
    tree_stdout = (raw.get("xwininfo_root_tree") or {}).get("stdout", "")
    independently_parsed = []
    for line in tree_stdout.splitlines():
        match = re.match(r'^(\s*)(0x[0-9a-fA-F]+)\s+"([^"]*)"', line)
        if match:
            independently_parsed.append({"indent": len(match.group(1)), "id": match.group(2), "title": match.group(3)})
    if windows != independently_parsed:
        errors.append("root_tree_parser_disagreement")
    receipts = raw.get("window_attribute_receipts", [])
    receipt_ids = [x.get("argv", [None])[-1] for x in receipts]
    window_ids = [x.get("id") for x in windows]
    if len(receipt_ids) != len(window_ids) or sorted(receipt_ids) != sorted(window_ids):
        errors.append("window_attribute_receipt_id_set")
    for receipt in receipts:
        if receipt.get("returncode") != 0 or receipt.get("timed_out") is not False:
            errors.append("window_attribute_command_failed")
        if "Window id:" not in receipt.get("stdout", ""):
            errors.append("window_attribute_id_not_reconciled")
    expected_title = workbook.name if workbook else ""
    matches = [w for w in independently_parsed if w["indent"] == 0 and expected_title in w["title"]
               and "LibreOffice Calc" in w["title"]]
    if raw.get("document_title_matches") != matches or len(matches) != 1:
        errors.append("document_title_identity_or_cardinality")
        target_state = None
    else:
        target = matches[0]
        receipt = next((x for x in receipts if x.get("argv", [None])[-1] == target["id"]), None)
        if receipt is None:
            errors.append("document_window_receipt_missing")
            target_state = None
        else:
            states = re.findall(r"Map State:\s*(\S+)", receipt.get("stdout", ""))
            target_state = states[0] if len(states) == 1 else None
            if target_state is None:
                errors.append("document_window_map_state_missing_or_ambiguous")
    if errors:
        decision = "STOP_AUDIT_OR_PROVENANCE"
    elif target_state == "IsViewable":
        decision = "PASS_DOCUMENT_WINDOW_VISIBLE_LOCAL_AMD64_SCOPED"
    elif target_state:
        decision = "CONTRADICTED_DOCUMENT_WINDOW_VISIBILITY"
    else:
        decision = "STOP_AUDIT_OR_PROVENANCE"
    return {
        "schema": "calc-doc-window-local-amd64-audit-v1",
        "decision": decision,
        "errors": errors,
        "target_map_state": target_state,
        "document_window_id": matches[0]["id"] if len(matches) == 1 else None,
        "window_count": len(windows),
        "attribute_receipt_count": len(receipts),
        "workbook_sha256_verified": actual_hash == before_hash == after_hash,
        "live_a1_after": raw.get("live_a1_after"),
        "persisted_a1": persisted,
        "scope": "single synthetic Calc window on local cached linux/amd64 image only",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("raw", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.raw.resolve(strict=True))
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 1 if result["decision"].startswith("STOP_") else 0


if __name__ == "__main__":
    raise SystemExit(main())
