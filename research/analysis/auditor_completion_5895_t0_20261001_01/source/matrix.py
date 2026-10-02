"""Deterministic completion-record mutations for the registered #5156 T0."""
from __future__ import annotations

import copy


_EXPECT_EXIT = {
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
    """Return eight isolated raw-record sets; never mutate the caller's rows."""
    originals = [row for row in base_rows if row.get("event") == "runner_complete"]
    if len(originals) != 1 or type(originals[0].get("exit_code")) is not int or originals[0]["exit_code"] != 0:
        raise ValueError("base must contain exactly one integer-zero runner completion")

    def case(case_id: str, mutate) -> dict:
        rows = copy.deepcopy(base_rows)
        completion_indexes = [i for i, row in enumerate(rows) if row.get("event") == "runner_complete"]
        mutate(rows, completion_indexes)
        return {"case_id": case_id, "expected_exit": _EXPECT_EXIT[case_id], "rows": rows}

    return [
        case("control", lambda rows, indexes: None),
        case("bool_false", lambda rows, indexes: rows[indexes[0]].__setitem__("exit_code", False)),
        case("float_zero", lambda rows, indexes: rows[indexes[0]].__setitem__("exit_code", 0.0)),
        case("null", lambda rows, indexes: rows[indexes[0]].__setitem__("exit_code", None)),
        case("string_zero", lambda rows, indexes: rows[indexes[0]].__setitem__("exit_code", "0")),
        case("missing_code", lambda rows, indexes: rows[indexes[0]].pop("exit_code")),
        case("duplicate_success", lambda rows, indexes: rows.insert(indexes[0] + 1, copy.deepcopy(rows[indexes[0]]))),
        case("success_plus_failure", lambda rows, indexes: rows.insert(indexes[0] + 1, {"event": "runner_complete", "exit_code": 1})),
    ]
