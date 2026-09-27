#!/usr/bin/python3
"""Independent audit of formal01; does not import runner or monitor."""
import argparse
import hashlib
import json
from pathlib import Path

import openpyxl


SCHEDULE = [("A", 1), ("B", 1), ("B", 2),
            ("A", 2), ("A", 3), ("B", 3)]
EVENT_NAMES = {2: "key_press", 3: "key_release",
               4: "button_press", 5: "button_release"}


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()


def inspect_run(root, mode, block):
    out = root/f"run-{mode}{block}"
    row = json.loads((out/"row.json").read_text(encoding="utf-8"))
    errors = []
    if row.get("mode") != mode or row.get("block") != block:
        errors.append("row_identity")
    workbook = out/"workbook.xlsx"
    pre = sha(workbook)
    if pre != row.get("workbook_post_sha256"):
        errors.append("workbook_post_hash")
    score = openpyxl.load_workbook(workbook, data_only=True, read_only=True)
    ws = score["Sheet1"]
    values = {f"A{i}": ws[f"A{i}"].value for i in range(1, 6)}
    score.close()
    if values != row.get("scored_cells"):
        errors.append("runner_scorer_disagreement")
    counts = {name: 0 for name in EVENT_NAMES.values()}
    events_path = out/"xrecord.jsonl"
    raw_lines = events_path.read_text(encoding="utf-8").splitlines() if events_path.exists() else []
    for line in raw_lines:
        event = json.loads(line)
        name = EVENT_NAMES.get(event.get("type"))
        if name:
            counts[name] += 1
        else:
            errors.append("unexpected_xrecord_type")
    if counts != row.get("xrecord_counts"):
        errors.append("xrecord_count_disagreement")
    if row.get("xrecord_exit") != 0 or not row.get("xrecord_started"):
        errors.append("xrecord_lifecycle")
    if row.get("window", {}).get("window_id") != row.get("focus_before_click"):
        errors.append("initial_focus_mismatch")
    if row.get("focus_after_click") != row.get("window", {}).get("window_id"):
        errors.append("post_click_focus_mismatch")
    if row.get("window_after_click", {}).get("pid") != row.get("window", {}).get("pid"):
        errors.append("window_process_identity_changed")
    if row.get("window_pid_bound_to_profile") is not True:
        errors.append("window_process_not_bound_to_private_profile")
    remaining = row.get("libreoffice_processes_after_cleanup") or []
    if any(not proc.get("state", "").startswith("Z") for proc in remaining):
        errors.append("libreoffice_process_not_terminal")
    if any(proc.get("returncode") is None for proc in row.get("processes", [])):
        errors.append("fixture_process_not_reaped")
    if row.get("selection_before_click", {}).get("absolute_name") != "$Sheet1.$A$1":
        errors.append("initial_cell_unexpected")

    if mode == "A":
        if row.get("task_input_attempted") is not True:
            errors.append("control_input_missing")
        if values.get("A1") is not None or values.get("A2") is not None:
            errors.append("control_modified_target_cells")
        if values.get("A3") != 116 or values.get("A4") != 476:
            errors.append("control_wrong_target_effect_missing")
        if counts != {"key_press": 11, "key_release": 11,
                      "button_press": 1, "button_release": 1}:
            errors.append("control_event_ledger")
        if row.get("decision") != "CONTROL_WRONG_TARGET_WRITE":
            errors.append("control_disposition")
    else:
        if row.get("task_input_attempted") is not False:
            errors.append("gate_emitted_task_input")
        if row.get("selection_after_click", {}).get("absolute_name") != "$Sheet1.$A$3":
            errors.append("mapping_changed")
        if row.get("gate", {}).get("allowed") is not False:
            errors.append("gate_not_refused")
        if any(values.get(f"A{i}") is not None for i in range(1, 6)):
            errors.append("gate_workbook_changed")
        if counts != {"key_press": 0, "key_release": 0,
                      "button_press": 1, "button_release": 1}:
            errors.append("gate_event_ledger")
        if row.get("decision") != "GATE_REFUSED":
            errors.append("gate_disposition")

    return {"mode": mode, "block": block, "errors": errors,
            "row_sha256": sha(out/"row.json"),
            "workbook_sha256": pre,
            "xrecord_sha256": sha(events_path),
            "xrecord_lines": len(raw_lines), "xrecord_counts": counts,
            "cells": values,
            "construction_selection": row.get("selection_after_click"),
            "input_attempted": row.get("task_input_attempted"),
            "processes": row.get("processes")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("evidence", type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    rows = [inspect_run(args.evidence, mode, block) for mode, block in SCHEDULE]
    errors = [f"{row['mode']}{row['block']}:{error}"
              for row in rows for error in row["errors"]]
    has_a, has_b = any(r["mode"] == "A" for r in rows), any(r["mode"] == "B" for r in rows)
    if any(e.endswith(":mapping_changed") for e in errors):
        decision = "HOLD_MAPPING_CHANGED"
    elif any(e.endswith(":gate_emitted_task_input") for e in errors):
        decision = "FAIL_GUARD_BYPASS"
    elif errors:
        decision = "FAIL_INTEGRITY" if any("disagreement" in e or "hash" in e for e in errors) else "FAIL_OR_HOLD_GATE"
    elif has_a and has_b and len(rows) == 6:
        decision = "PASS_STALE_TARGET_BLOCKED_SCOPED"
    else:
        decision = "HOLD_INCOMPLETE_DENOMINATOR"
    result = {"schema": "issue2704_stale_target_receipt_audit_v1",
              "decision": decision, "sessions": len(rows),
              "expected_sessions": 6, "errors": errors, "rows": rows,
              "scope": "independent workbook/event/hash audit; no production CLI claim"}
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out/"audit.json").write_text(json.dumps(result, indent=2,
                                                   sort_keys=True)+"\n",
                                       encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    if decision != "PASS_STALE_TARGET_BLOCKED_SCOPED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

