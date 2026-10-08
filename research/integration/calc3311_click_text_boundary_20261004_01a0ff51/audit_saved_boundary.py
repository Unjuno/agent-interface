#!/usr/bin/env python3
"""Independently audit the saved #3311 A01 click-to-text evidence boundary.

This reads only immutable Git objects pinned below. It does not start Calc,
replay input, invoke a model, or modify repository state.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path


PINNED_MAIN = "8c66c43918c7b8ac4b3daf929e07b163ba306d81"
STUDY = "research/integration/calc_realapp_3311_20261004_4d74"
NS = {
    "office": "urn:oasis:names:tc:opendocument:xmlns:office:1.0",
    "table": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
    "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0",
}


def git_blob(path: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"{PINNED_MAIN}:{path}"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout


def value(cell: ET.Element) -> str:
    attr = f"{{{NS['office']}}}value"
    if attr in cell.attrib:
        return cell.attrib[attr]
    return "".join(node.text or "" for node in cell.findall(".//text:p", NS))


def expand_row(row: ET.Element) -> list[ET.Element]:
    cells: list[ET.Element] = []
    for cell in list(row):
        if cell.tag not in {
            f"{{{NS['table']}}}table-cell",
            f"{{{NS['table']}}}covered-table-cell",
        }:
            continue
        count = int(cell.get(f"{{{NS['table']}}}number-columns-repeated", "1"))
        cells.extend([cell] * count)
    return cells


def field_names(value: object) -> set[str]:
    names: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            names.add(str(key))
            names.update(field_names(child))
    elif isinstance(value, list):
        for child in value:
            names.update(field_names(child))
    return names


def main() -> None:
    plan = json.loads(git_blob(f"{STUDY}/PLAN.json"))
    pinned_files = {
        "native_sequence.py": f"{STUDY}/native_sequence.py",
        "sources/runtime/backends/x11_v1/backend.py":
            f"{STUDY}/sources/runtime/backends/x11_v1/backend.py",
        "sources/runtime/backends/x11_v1/session.py":
            f"{STUDY}/sources/runtime/backends/x11_v1/session.py",
    }
    source_checks = {}
    source_bytes = {}
    for name, path in pinned_files.items():
        blob = git_blob(path)
        actual = hashlib.sha256(blob).hexdigest()
        expected = plan["source_hashes"][name]
        source_checks[name] = {"expected": expected, "actual": actual,
                               "match": actual == expected}
        source_bytes[name] = blob
        assert actual == expected, f"source hash mismatch: {name}"

    done = json.loads(git_blob(f"{STUDY}/runs/session1-direct/task1.DONE.json"))
    fods = git_blob(f"{STUDY}/runs/session1-direct/task1.fods")
    saved_hash = hashlib.sha256(fods).hexdigest()
    assert saved_hash == done["saved_sha256"]

    root = ET.fromstring(fods)
    tables = root.findall(".//table:table", NS)
    assert tables, "no ODF table found"
    rows = tables[0].findall("table:table-row", NS)
    matrix = [expand_row(row) for row in rows]
    # The first row is headers; following rows are spreadsheet rows 2 and 3.
    actual = {
        "A2": value(matrix[1][0]),
        "B2": value(matrix[1][1]),
        "C2": value(matrix[1][2]),
        "C2_formula": matrix[1][2].get(f"{{{NS['table']}}}formula"),
        "A3": value(matrix[2][0]),
    }
    expected_task = next(task for task in plan["tasks"] if task["index"] == 1)
    expected = {
        "A2": str(expected_task["a"]),
        "B2": str(expected_task["b"]),
        "C2": str(expected_task["a"] * expected_task["b"]),
        "C2_formula": "of:=[.A2]*[.B2]",
        "A3": "",
    }

    ops = done["program"]["ops"]
    release_index = max(
        i for i, op in enumerate(ops)
        if op.get("op") == "pointer_button"
        and op.get("button") == "left"
        and op.get("down") is False
    )
    first_text_index = next(
        i for i, op in enumerate(ops[release_index + 1:], release_index + 1)
        if op.get("op") == "text"
    )
    first_wait_index = next(
        (i for i, op in enumerate(ops) if i > first_text_index
         and op.get("op") == "wait_update"),
        None,
    )
    pre_text_gate_ops = [
        op.get("op") for op in ops[release_index + 1:first_text_index]
        if op.get("op") in {"wait_update", "observe", "verify"}
    ]
    first_text = ops[first_text_index]

    execution = done["receipt"]["execution"]
    waits = execution["waits"]
    first_char_wait = next(
        (wait for wait in waits if wait["operation_index"] == first_wait_index),
        None,
    )
    assert first_wait_index is not None and first_char_wait is not None
    release = execution["releases"][-1]
    names = field_names(done)
    cell_identity_fields = sorted(names & {
        "selected_cell", "active_cell", "current_cell", "cell_identity",
        "target_cell", "cell_address", "key_target",
    })
    input_event_record_fields = sorted(names & {
        "input_events", "key_events", "operation_events", "operation_receipts",
    })

    result = {
        "schema": "calc3311-a01-click-text-boundary-audit-v1",
        "pinned_main": PINNED_MAIN,
        "allocation": "CALC-REALAPP-3311-4D74-A01-20261004",
        "source_hashes": source_checks,
        "saved_document": {
            "sha256": saved_hash,
            "matches_done_record": True,
            "actual": actual,
            "expected": expected,
            "effect_match": actual == expected,
        },
        "dispatch_boundary": {
            "program_status": done["receipt"]["status"],
            "completed_ops": len(execution["completed_ops"]),
            "verified_empty_release": bool(
                release["verified"] and not release["keys_down"]
                and not release["buttons_down"]
            ),
            "last_pointer_release_op": release_index,
            "first_text_op": first_text_index,
            "first_text_payload": first_text.get("text"),
            "pre_text_gate_ops": pre_text_gate_ops,
            "first_following_wait": first_char_wait,
            "execution_receipt_fields": sorted(execution),
            "cell_identity_fields": cell_identity_fields,
            "input_event_record_fields": input_event_record_fields,
            "observation_count": len(execution["observations"]),
        },
        "pinned_backend_semantics": {
            "source_declares_wait_update_fixed_delay":
                b"fixed delay" in source_bytes[
                    "sources/runtime/backends/x11_v1/backend.py"],
            "receipt_reports_update_observed_null":
                first_char_wait["update_observed"] is None,
        },
        "finding": (
            "SAVED_EFFECT_FAILURE_REPRODUCED; FIRST_TEXT_HAS_NO_PREINPUT_SELECTION_ACK; "
            "CLICK_TO_TEXT_CAUSALITY_UNOBSERVED"
        ),
        "scope": (
            "Independent saved-source/FODS/receipt audit only. The recorded data do not "
            "identify which cell received each native key event or prove the cause of "
            "A01's failure. No GUI, input, model, container, or formal allocation was run."
        ),
    }
    assert actual != expected
    assert done["receipt"]["status"] == "completed"
    assert result["dispatch_boundary"]["verified_empty_release"]
    assert not pre_text_gate_ops
    assert first_char_wait["kind"] == "fixed_delay"
    assert first_char_wait["update_observed"] is None
    assert not cell_identity_fields
    assert not input_event_record_fields
    assert not execution["observations"]
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
