"""Independent audit; does not import the runner or a candidate classifier."""
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


def main(raw_path: pathlib.Path) -> int:
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    errors = []
    image = "issue-2849-task1-runtime@sha256:436172d89b145c6a9f9a57e655422c9558b3b0235347dd77607e9d61bcfa6393"
    if raw.get("allocation") != "calc-effect-contract-34-window-gate-20260927-01": errors.append("allocation mismatch")
    if raw.get("image") != image: errors.append("image mismatch")
    if raw.get("cell_before_edit") != 0 or raw.get("cell_after_edit_live") != 7: errors.append("live transition mismatch")
    if raw.get("document_modified_unsaved") is not True or raw.get("save_store_calls") != 0: errors.append("unsaved document boundary mismatch")
    if raw.get("harness_completed") is not True: errors.append("harness not complete")
    if raw.get("source_sha256_before") != raw.get("source_sha256_after"): errors.append("source hash changed")
    tree = json.loads(raw.get("xwininfo_root_tree") or "{}")
    wid = raw.get("vcl_window_id")
    attr = json.loads(raw.get("xwininfo_window_attributes") or "{}") if raw.get("xwininfo_window_attributes") else {}
    if tree.get("exit") != 0 or not wid or len(re.findall(r"0x[0-9a-fA-F]+ \"VCL ImplGetDefaultWindow\"", tree.get("stdout", ""))) != 1: errors.append("VCL root-tree window evidence missing or ambiguous")
    if attr.get("exit") != 0 or f"Window id: {wid}" not in attr.get("stdout", "") or "Map State: IsViewable" not in attr.get("stdout", ""): errors.append("same-run VCL window is not proven viewable")
    source = raw_path.parent / raw["source_file"]
    wb = load_workbook(source, read_only=True, data_only=True)
    disk_cell = wb.active["A1"].value
    wb.close()
    current = digest(source)
    if disk_cell != 0 or raw.get("persisted_cell_after_independent_reopen") != 0: errors.append("saved workbook A1 is not baseline zero")
    if current != raw.get("source_sha256_before") or current != raw.get("source_sha256_after"): errors.append("independent workbook hash mismatch")
    result = {
        "schema": "calc-effect-contract-window-gate-audit-v1",
        "raw_sha256": digest(raw_path),
        "source_sha256_independent": current,
        "independently_reopened_A1": disk_cell,
        "window_map_state": "IsViewable" if "Map State: IsViewable" in attr.get("stdout", "") else "UNKNOWN",
        "errors": errors,
        "disposition": "PASS_WINDOW_GATED_CONSTRUCTION_ONLY" if not errors else "STOP_CONSTRUCTION",
        "formal_allocation_cases": 0,
        "claim_limit": "one synthetic unsaved Calc edit; not runtime or formal Issue 34 evidence",
    }
    (raw_path.parent / "audit.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if not errors else 2


if __name__ == "__main__":
    if len(sys.argv) != 2: raise SystemExit("usage: audit.py /out/<run>/raw.json")
    raise SystemExit(main(pathlib.Path(sys.argv[1])))
