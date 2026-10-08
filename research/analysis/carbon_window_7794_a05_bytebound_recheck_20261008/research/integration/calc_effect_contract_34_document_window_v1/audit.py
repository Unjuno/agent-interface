"""Independent raw/window/workbook audit; does not import the runner."""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import sys

from openpyxl import load_workbook


def digest(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def state(stdout: str) -> str | None:
    m = re.search(r"Map State:\s*(IsViewable|IsUnMapped|IsUnviewable)", stdout)
    return m.group(1) if m else None


def title(stdout: str) -> str | None:
    m = re.search(r"^xwininfo: Window id: 0x[0-9a-fA-F]+ \"(.*)\"$", stdout, flags=re.MULTILINE)
    return m.group(1) if m else None


def main(raw_path: pathlib.Path) -> int:
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    errors = []
    tree = raw.get("root_tree") or {}
    ids = raw.get("root_child_ids")
    windows = raw.get("child_window_attributes")
    if tree.get("exit") != 0 or type(ids) is not list or not ids or type(windows) is not list:
        errors.append("root window tree/child inventory missing")
        windows = windows if type(windows) is list else []
        ids = ids if type(ids) is list else []
    observed_ids = [w.get("window_id") for w in windows]
    if len(ids) != len(set(ids)) or sorted(ids) != sorted(observed_ids):
        errors.append("child-window query inventory does not exactly match root tree")
    parsed = []
    for item in windows:
        out = item.get("stdout", "")
        wid = item.get("window_id")
        if item.get("exit") != 0 or f"Window id: {wid}" not in out:
            errors.append(f"child query failed or ID mismatch: {wid}")
        parsed.append({"window_id": wid, "title": title(out), "map_state": state(out)})
    doc_title = "document-window-probe.xlsx - LibreOffice Calc"
    docs = [w for w in parsed if w["title"] == doc_title]
    if len(docs) != 1:
        errors.append("document-titled window missing or ambiguous")
        disposition = "STOP_CONSTRUCTION"
    elif docs[0]["map_state"] == "IsUnMapped":
        disposition = "CONTRADICTED_DOCUMENT_WINDOW_VISIBILITY"
    elif docs[0]["map_state"] == "IsViewable":
        disposition = "PASS_DOCUMENT_WINDOW_VISIBLE_CONSTRUCTION_ONLY"
    else:
        errors.append("document window map state missing/unknown")
        disposition = "STOP_CONSTRUCTION"
    if raw.get("cell_before_edit") != 0 or raw.get("cell_after_edit_live") != 7:
        errors.append("live transition mismatch")
    if raw.get("document_modified_unsaved") is not True or raw.get("save_store_calls") != 0:
        errors.append("unsaved condition mismatch")
    source = raw_path.parent / raw["source_file"]
    wb = load_workbook(source, read_only=True, data_only=True)
    disk_cell = wb.active["A1"].value
    wb.close()
    current = digest(source)
    if disk_cell != 0 or raw.get("persisted_cell_after_independent_reopen") != 0:
        errors.append("independent saved workbook value mismatch")
    if not (current == raw.get("source_sha256_before") == raw.get("source_sha256_after") and current):
        errors.append("independent source hash mismatch")
    result = {
        "schema": "calc-effect-contract-document-window-audit-v1",
        "raw_sha256": digest(raw_path),
        "source_sha256_independent": current,
        "independently_reopened_A1": disk_cell,
        "parsed_child_windows": parsed,
        "document_window_count": len(docs),
        "errors": errors,
        "disposition": disposition if not errors else (disposition if disposition.startswith("CONTRADICTED") else "STOP_CONSTRUCTION"),
        "formal_allocation_cases": 0,
        "claim_limit": "one synthetic Calc/Xvfb presentation construction; not runtime or formal Issue 34 evidence",
    }
    (raw_path.parent / "audit.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if disposition.startswith("PASS") and not errors else (1 if disposition.startswith("CONTRADICTED") else 2)


if __name__ == "__main__":
    if len(sys.argv) != 2: raise SystemExit("usage: audit.py /out/<allocation>/raw.json")
    raise SystemExit(main(pathlib.Path(sys.argv[1])))
