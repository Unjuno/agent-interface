#!/usr/bin/env python3
"""Independently re-score the saved D01 Calc rows without replaying them."""

from __future__ import annotations

import json
import subprocess
import xml.etree.ElementTree as ET

D01_COMMIT = "f89e59c33a5ca18e9b0a917a596a55b9a99467a6"
D01_ROOT = "research/integration/calc_click_text_3311_20261004_4d74/runs"
SCHEDULE_MS = [0, 50, 50, 0, 0, 50, 50, 0]
NS = {
    "office": "urn:oasis:names:tc:opendocument:xmlns:office:1.0",
    "table": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
    "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0",
}


def git_blob(path: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"{D01_COMMIT}:{path}"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout


def read_sheet(data: bytes) -> tuple[list[str], str | None, int]:
    root = ET.fromstring(data)
    rows = root.findall(".//table:table-row", NS)
    matrix: list[list[tuple[str, str | None]]] = []
    for row in rows:
        cells: list[tuple[str, str | None]] = []
        for cell in list(row):
            if cell.tag not in {
                f"{{{NS['table']}}}table-cell",
                f"{{{NS['table']}}}covered-table-cell",
            }:
                continue
            value = cell.get(f"{{{NS['office']}}}value")
            if value is None:
                value = "".join(
                    paragraph.text or ""
                    for paragraph in cell.findall(".//text:p", NS)
                )
            formula = cell.get(f"{{{NS['table']}}}formula")
            repeated = int(
                cell.get(f"{{{NS['table']}}}number-columns-repeated", "1")
            )
            cells.extend([(value, formula)] * repeated)
        matrix.append(cells)
    values = [matrix[1][column][0] for column in range(3)]
    formula = matrix[1][2][1]
    populated = sum(value != "" for row in matrix for value, _ in row)
    return values, formula, populated


def main() -> None:
    rows = []
    for row_number, wait_ms in enumerate(SCHEDULE_MS, 1):
        prefix = f"{D01_ROOT}/row{row_number}/"
        raw = json.loads(git_blob(prefix + "raw.json"))
        host = json.loads(git_blob(prefix + "HOST_RECEIPT.json"))
        prime_values, prime_formula, prime_populated = read_sheet(
            git_blob(prefix + "prime.fods")
        )
        trial_values, trial_formula, trial_populated = read_sheet(
            git_blob(prefix + "trial.fods")
        )
        trial_program = raw["tasks"][1]["program"]
        operations = trial_program["ops"]
        release_index = max(
            index
            for index, operation in enumerate(operations)
            if operation.get("op") == "pointer_button"
            and operation.get("down") is False
            and operation.get("button") == "left"
        )
        first_text_index = next(
            index
            for index, operation in enumerate(operations)
            if index > release_index and operation.get("op") == "text"
        )
        pre_text_waits = [
            operation
            for operation in operations[release_index + 1 : first_text_index]
            if operation.get("op") == "wait_update"
        ]
        wait_matches = (
            len(pre_text_waits) == 0
            if wait_ms == 0
            else len(pre_text_waits) == 1
            and pre_text_waits[0].get("timeout_ms") == wait_ms
        )
        cleanup = raw["cleanup_physical"]
        cleanup_release = raw["cleanup_release"]
        assert raw["spec"]["click_wait_ms"] == wait_ms
        assert raw["errors"] == []
        assert host["exit_code"] == 0 and host["model_calls"] == 0
        assert prime_values == ["11", "13", "143"]
        assert prime_formula == "of:=[.A2]*[.B2]" and prime_populated == 6
        assert trial_values == ["73", "79", "5767"]
        assert trial_formula == "of:=[.A2]*[.B2]" and trial_populated == 6
        assert wait_matches
        assert cleanup_release["verified"]
        assert cleanup_release["keys_down"] == []
        assert cleanup_release["buttons_down"] == []
        assert cleanup["keys"] == [] and cleanup["buttons"] == 0
        rows.append(
            {
                "row": row_number,
                "click_wait_ms": wait_ms,
                "prime_cells_A2_B2_C2": prime_values,
                "trial_cells_A2_B2_C2": trial_values,
                "trial_formula": trial_formula,
                "populated_cells_in_each_saved_sheet": 6,
                "pre_first_text_waits_ms": [
                    operation["timeout_ms"] for operation in pre_text_waits
                ],
                "model_calls": host["model_calls"],
                "verified_neutral_cleanup": True,
            }
        )
    assert [row["click_wait_ms"] for row in rows] == SCHEDULE_MS
    assert sum(row["click_wait_ms"] == 0 for row in rows) == 4
    assert sum(row["click_wait_ms"] == 50 for row in rows) == 4
    print(
        json.dumps(
            {
                "schema": "calc3311-d01-independent-saved-data-reaudit-v1",
                "d01_commit": D01_COMMIT,
                "decision": "PASS_INDEPENDENT_SAVED_EFFECT_AND_RECEIPT_RECHECK",
                "rows": rows,
                "interpretation": (
                    "The saved effect is exact at both 0 ms and 50 ms (4/4 each). "
                    "This does not establish a timing cause for A01, generally reliable "
                    "wait policy, or a production default."
                ),
                "scope": (
                    "Read-only Git-object, FODS and receipt audit; no producer, GUI, "
                    "model, container or allocation was rerun."
                ),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
