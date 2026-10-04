#!/usr/bin/env python3
"""Independent saved-artifact audit of the merged #57 caller-progress probe."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET


REPO = Path(__file__).resolve().parents[3]
PACKAGE = REPO / "research/integration/calc_caller_progress_57_4d74_20261004/calc-caller-progress-57-4d74"
NS = {
    "office": "urn:oasis:names:tc:opendocument:xmlns:office:1.0",
    "table": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
    "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def spreadsheet_cells(path: Path) -> dict[str, dict[str, str | None]]:
    root = ET.parse(path).getroot()
    sheet = root.find("office:body/office:spreadsheet", NS)
    if sheet is None:
        raise ValueError("missing OpenDocument spreadsheet body")
    result: dict[str, dict[str, str | None]] = {}
    row_number = 0
    for table in sheet.findall("table:table", NS):
        for row in table.findall("table:table-row", NS):
            row_number += int(row.get(f"{{{NS['table']}}}number-rows-repeated", "1"))
            col_number = 0
            for cell in row:
                if cell.tag not in {
                    f"{{{NS['table']}}}table-cell",
                    f"{{{NS['table']}}}covered-table-cell",
                }:
                    continue
                repeat = int(cell.get(f"{{{NS['table']}}}number-columns-repeated", "1"))
                value_type = cell.get(f"{{{NS['office']}}}value-type")
                value = cell.get(f"{{{NS['office']}}}value")
                formula = cell.get(f"{{{NS['table']}}}formula")
                text = "".join("".join(node.itertext())
                                for node in cell.findall("text:p", NS))
                if value_type == "string":
                    value = text
                if value is not None or formula is not None or text:
                    for offset in range(repeat):
                        col = col_number + offset
                        letters = ""
                        n = col + 1
                        while n:
                            n, rem = divmod(n - 1, 26)
                            letters = chr(65 + rem) + letters
                        result[f"{letters}{row_number}"] = {
                            "value": value,
                            "formula": formula,
                        }
                col_number += repeat
    return result


def audit() -> dict:
    plan = load_json(PACKAGE / "PLAN.json")
    execution = load_json(PACKAGE / "EXECUTION.json")
    errors: list[str] = []
    source_results = {}
    for relative, expected in plan["source_hashes"].items():
        path = PACKAGE / relative
        actual = sha256(path.read_bytes()) if path.is_file() else None
        source_results[relative] = {"expected": expected, "actual": actual,
                                    "match": actual == expected}
        if actual != expected:
            errors.append(f"source pin mismatch: {relative}")

    original = (PACKAGE / "caller_main.py").read_bytes()
    retained = (PACKAGE / "caller_retention.py").read_bytes()
    before = b'delivery="confirmed")\n        return finish("TASK_SUCCEEDED"'
    after = b'delivery="confirmed", execution_progress=execution)\n        return finish("TASK_SUCCEEDED"'
    contrast_ok = original.count(before) == 1 and original.replace(before, after) == retained
    if not contrast_ok:
        errors.append("reference is not exactly the declared one-line retention change")

    expected_cells = {
        "A1": {"value": "a", "formula": None},
        "B1": {"value": "b", "formula": None},
        "C1": {"value": "product", "formula": None},
        "A2": {"value": "101", "formula": None},
        "B2": {"value": "103", "formula": None},
        "C2": {"value": "10403", "formula": "of:=[.A2]*[.B2]"},
    }
    rows = []
    planned_rows = plan["rows"]
    executed_rows = execution["rows"]
    if len(planned_rows) != 2 or len(executed_rows) != len(planned_rows):
        errors.append("row count mismatch")

    for index, spec in enumerate(planned_rows):
        label = f"row{index + 1}"
        directory = PACKAGE / "runs" / label
        raw = load_json(directory / "raw.json")
        host = load_json(directory / "HOST_RECEIPT.json")
        row_errors = []
        if executed_rows[index].get("spec") != spec or raw.get("spec") != spec:
            row_errors.append("row specification mismatch")
        if raw.get("source_hashes") != plan["source_hashes"]:
            row_errors.append("raw source identity mismatch")
        if raw.get("errors") or host.get("errors") or host.get("exit_code") != 0:
            row_errors.append("runner/host error or nonzero exit")
        if host.get("model_calls") != 0 or plan.get("model_calls") != 0:
            row_errors.append("unexpected model call")
        if raw.get("adapter_calls") != ["execute", "verify"] or len(raw.get("tasks", [])) != 1:
            row_errors.append("expected one execute and one verify")
        if raw.get("caller_events", []).count({"event": "adaptive_route_finished"}) > 1:
            row_errors.append("duplicate terminal caller event")
        terminal_events = [e for e in raw.get("caller_events", [])
                           if e.get("event") == "adaptive_route_finished"]
        if len(terminal_events) != 1:
            row_errors.append("terminal caller event count is not one")

        task = raw["tasks"][0]
        receipt = task["receipt"]
        execution_receipt = receipt["execution"]
        digest = sha256(json.dumps(receipt, sort_keys=True).encode("utf-8"))
        projection = raw.get("execution_projection", {})
        if projection.get("native_receipt_sha256") != digest or projection.get("caller_decision") != {"status": "completed"}:
            row_errors.append("typed native progress projection mismatch")
        caller = raw["caller_result"]
        expected_progress = None if spec["arm"] == "main" else {"status": "completed"}
        if (caller.get("outcome"), caller.get("reason"), caller.get("task_effect"),
                caller.get("delivery"), caller.get("execution_progress")) != (
                "TASK_NOT_VERIFIED", "unavailable", "unavailable", "confirmed", expected_progress):
            row_errors.append("caller result/progress mismatch")
        if caller.get("input_authority") != "consumed_by_recorded_execute_stage":
            row_errors.append("input authority mismatch")
        if caller.get("accounting", {}).get("attempted_calls") != 0:
            row_errors.append("nonzero model accounting")
        if caller.get("attempt_ledger") or caller.get("model_call_ledger"):
            row_errors.append("unexpected model ledger entry")
        stages = caller.get("stages", {})
        if any(stages.get(name, {}).get("status") != "completed"
               for name in ("execute", "verify_effect")):
            row_errors.append("execute/verify stage not completed")

        ops = task["program"]["ops"]
        releases = execution_receipt.get("releases", [])
        if execution_receipt.get("completed_ops") != list(range(len(ops))):
            row_errors.append("native operation completion mismatch")
        if not releases or not all(r.get("verified") is True and
                                   r.get("keys_down") == [] and
                                   r.get("buttons_down") == [] for r in releases):
            row_errors.append("native release evidence mismatch")
        physical = raw.get("cleanup_physical", {})
        cleanup = raw.get("cleanup_release", {})
        if physical.get("keys") != [] or physical.get("buttons") != 0:
            row_errors.append("post-cleanup physical input is nonempty")
        if cleanup.get("verified") is not True or cleanup.get("keys_down") != [] or cleanup.get("buttons_down") != []:
            row_errors.append("post-cleanup release receipt mismatch")

        workbook_path = directory / "heldout-comparison.fods"
        actual_cells = spreadsheet_cells(workbook_path)
        if actual_cells != expected_cells:
            row_errors.append("independent FODS saved-effect mismatch")
        rows.append({
            "row": label,
            "arm": spec["arm"],
            "saved_effect_cells": actual_cells,
            "native_attempts": len(raw.get("tasks", [])),
            "model_calls": host.get("model_calls"),
            "caller_outcome": caller.get("outcome"),
            "execution_progress": caller.get("execution_progress"),
            "release_verified": bool(releases) and all(r.get("verified") is True for r in releases),
            "errors": row_errors,
        })
        errors.extend(f"{label}: {error}" for error in row_errors)

    return {
        "allocation": plan.get("allocation"),
        "source_main": plan.get("source_main"),
        "scope": "independent offline re-audit of preserved native receipts and FODS outputs; no allocation rerun",
        "source_hashes_match": all(v["match"] for v in source_results.values()),
        "one_line_contrast_exact": contrast_ok,
        "rows": rows,
        "errors": errors,
        "disposition": "PASS_REAUDIT_SCOPED" if not errors else "HOLD_REAUDIT_MISMATCH",
        "limits": [
            "does not rerun or independently blind the original allocation",
            "does not establish natural verifier failures, semantic target admission, recovery efficacy, or efficiency benefit",
            "does not establish all-descendant or graceful-close guarantees",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps({"disposition": result["disposition"],
                      "rows": len(result["rows"]), "errors": result["errors"]}))
    return 0 if not result["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
