"""Fail-closed raw-only validation for the Issue #4912 recovered result."""
from __future__ import annotations

import copy


class AuditValidationError(ValueError):
    """Raised when a retained raw result violates the frozen contract."""


EXPECTED_ALLOCATION = "typed-readout-precision-boundary-1014-v5-20260928-01"
EXPECTED_MODES = {"fp16", "bf16", "fp32"}
EXPECTED_ROWS = [("B00", 0), ("B00", 7), ("B00", 15),
                 ("B17", 0), ("B17", 7), ("B17", 15),
                 ("B63", 0), ("B63", 7), ("B63", 15)]
EXPECTED_ANSWER_IDS = list(range(15, 23))
ATOL = 0.002
RTOL = 0.002


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AuditValidationError(message)


def validate_result(result: dict) -> None:
    require(isinstance(result, dict), "result must be an object")
    require(result.get("allocation") == EXPECTED_ALLOCATION, "allocation mismatch")
    require(result.get("status") == "CONSTRUCTION_COMPLETE", "status mismatch")
    require(result.get("answer_ids") == EXPECTED_ANSWER_IDS, "answer IDs mismatch")
    require(result.get("answer_token_ids_verified") is True, "answer token IDs are unverified")
    modes = result.get("modes")
    require(isinstance(modes, dict) and set(modes) == EXPECTED_MODES, "mode set mismatch")
    rows = result.get("rows")
    require(isinstance(rows, list), "rows must be a list")
    require(len(rows) == len(EXPECTED_ROWS) * len(EXPECTED_MODES), "row count mismatch")
    expected = {(mode, bundle, slot) for mode in EXPECTED_MODES for bundle, slot in EXPECTED_ROWS}
    actual = {(r["mode"], r["bundle_id"], r["slot"]) for r in rows}
    require(actual == expected, "row identity set mismatch")
    require(len(actual) == len(rows), "duplicate rows")
    for row in rows:
        a, b = row["full_logits"], row["cached_logits"]
        require(len(a) == len(b) == len(EXPECTED_ANSWER_IDS), "logit vector length mismatch")
        abs_d = [abs(x - y) for x, y in zip(a, b, strict=True)]
        rel_d = [d / max(abs(x), 1e-4) for x, d in zip(a, abs_d, strict=True)]
        require(row["comparison"]["max_abs"] == max(abs_d), "max_abs mismatch")
        require(row["comparison"]["max_rel"] == max(rel_d), "max_rel mismatch")
        winner_a = max(range(8), key=lambda i: (a[i], -i))
        winner_b = max(range(8), key=lambda i: (b[i], -i))
        require(row["comparison"]["argmax_equal"] is (winner_a == winner_b), "argmax mismatch")
        within = max(abs_d) <= ATOL and max(rel_d) <= RTOL
        require(row["comparison"]["within_tolerance"] is within, "tolerance result mismatch")
        require(type(row["cache_isolation"]) is bool, "cache_isolation must be boolean")
    for mode, summary in modes.items():
        mode_rows = [r for r in rows if r["mode"] == mode]
        require(summary["rows"] == len(EXPECTED_ROWS), f"{mode} row count mismatch")
        require(summary["all_within_tolerance"] is all(
            r["comparison"]["within_tolerance"] for r in mode_rows),
            f"{mode} tolerance summary mismatch")
        require(summary["all_winners_equal"] is all(
            r["comparison"]["argmax_equal"] for r in mode_rows),
            f"{mode} winner summary mismatch")
        require(summary["all_cache_isolation"] is all(
            r["cache_isolation"] for r in mode_rows),
            f"{mode} cache summary mismatch")


def corruption_controls(result: dict) -> int:
    controls = []
    changed = copy.deepcopy(result)
    changed["allocation"] = "mutated"
    controls.append(changed)
    changed = copy.deepcopy(result)
    changed["rows"].pop()
    controls.append(changed)
    changed = copy.deepcopy(result)
    changed["rows"][0]["full_logits"][0] += 1.0
    controls.append(changed)
    changed = copy.deepcopy(result)
    changed["rows"][0]["comparison"]["argmax_equal"] = not changed["rows"][0]["comparison"]["argmax_equal"]
    controls.append(changed)
    changed = copy.deepcopy(result)
    changed["rows"][0]["cache_isolation"] = False
    changed["modes"][changed["rows"][0]["mode"]]["all_cache_isolation"] = True
    controls.append(changed)
    rejected = 0
    for candidate in controls:
        try:
            validate_result(candidate)
        except (AuditValidationError, KeyError, TypeError, ValueError):
            rejected += 1
    require(rejected == len(controls), "one or more corruption controls were accepted")
    return rejected

