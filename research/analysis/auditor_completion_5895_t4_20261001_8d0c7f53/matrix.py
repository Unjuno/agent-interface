"""Deterministic, isolated eight-case completion-record mutation matrix."""

from __future__ import annotations

import copy


EXPECTED_EXIT = {
    "control": 0,
    "bool_false": 0,
    "float_zero": 0,
    "null": 1,
    "string_zero": 1,
    "missing_code": 1,
    "duplicate_success": 1,
    "success_plus_failure": 0,
}


def make_matrix(base_rows: list[dict]) -> list[dict]:
    """Build each raw case from an unchanged fixture with one explicit mutation."""
    originals = [row for row in base_rows if row.get("event") == "runner_complete"]
    if (len(originals) != 1 or type(originals[0].get("exit_code")) is not int
            or originals[0]["exit_code"] != 0):
        raise ValueError("base must contain exactly one integer-zero runner completion")

    def make(case_id: str, mutate) -> dict:
        rows = copy.deepcopy(base_rows)
        indexes = [index for index, row in enumerate(rows) if row.get("event") == "runner_complete"]
        mutate(rows, indexes)
        return {"case_id": case_id, "expected_exit": EXPECTED_EXIT[case_id], "rows": rows}

    return [
        make("control", lambda rows, indexes: None),
        make("bool_false", lambda rows, indexes: rows[indexes[0]].__setitem__("exit_code", False)),
        make("float_zero", lambda rows, indexes: rows[indexes[0]].__setitem__("exit_code", 0.0)),
        make("null", lambda rows, indexes: rows[indexes[0]].__setitem__("exit_code", None)),
        make("string_zero", lambda rows, indexes: rows[indexes[0]].__setitem__("exit_code", "0")),
        make("missing_code", lambda rows, indexes: rows[indexes[0]].pop("exit_code")),
        make("duplicate_success", lambda rows, indexes: rows.insert(indexes[0] + 1, copy.deepcopy(rows[indexes[0]]))),
        make("success_plus_failure", lambda rows, indexes: rows.insert(
            indexes[0] + 1, {"event": "runner_complete", "exit_code": 1})),
    ]
