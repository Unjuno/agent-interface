"""Independent, raw-only audit logic for Issue #4912 construction output."""
from __future__ import annotations

EXPECTED_ALLOCATION = "typed-readout-precision-boundary-1014-v4-20260928-01"
EXPECTED_MODES = {"fp16", "bf16", "fp32"}
EXPECTED_ROWS = [("B00", 0), ("B00", 7), ("B00", 15),
                 ("B17", 0), ("B17", 7), ("B17", 15),
                 ("B63", 0), ("B63", 7), ("B63", 15)]
EXPECTED_ANSWER_IDS = list(range(15, 23))
ATOL = 0.002
RTOL = 0.002


def validate_result(result: dict) -> None:
    assert result["allocation"] == EXPECTED_ALLOCATION
    assert result["status"] == "CONSTRUCTION_COMPLETE"
    assert result["answer_ids"] == EXPECTED_ANSWER_IDS
    assert result["answer_token_ids_verified"] is True
    assert set(result["modes"]) == EXPECTED_MODES
    rows = result["rows"]
    assert len(rows) == len(EXPECTED_ROWS) * len(EXPECTED_MODES)
    expected = {(mode, bundle, slot) for mode in EXPECTED_MODES for bundle, slot in EXPECTED_ROWS}
    actual = {(r["mode"], r["bundle_id"], r["slot"]) for r in rows}
    assert actual == expected
    assert len(actual) == len(rows)
    for row in rows:
        a, b = row["full_logits"], row["cached_logits"]
        assert len(a) == len(b) == len(EXPECTED_ANSWER_IDS)
        abs_d = [abs(x-y) for x, y in zip(a, b, strict=True)]
        rel_d = [d / max(abs(x), 1e-4) for x, d in zip(a, abs_d, strict=True)]
        assert row["comparison"]["max_abs"] == max(abs_d)
        assert row["comparison"]["max_rel"] == max(rel_d)
        winner_a = max(range(8), key=lambda i: (a[i], -i))
        winner_b = max(range(8), key=lambda i: (b[i], -i))
        assert row["comparison"]["argmax_equal"] is (winner_a == winner_b)
        within = max(abs_d) <= ATOL and max(rel_d) <= RTOL
        assert row["comparison"]["within_tolerance"] is within
        assert type(row["cache_isolation"]) is bool
    for mode, summary in result["modes"].items():
        mode_rows = [r for r in rows if r["mode"] == mode]
        assert summary["rows"] == len(EXPECTED_ROWS)
        assert summary["all_within_tolerance"] is all(r["comparison"]["within_tolerance"] for r in mode_rows)
        assert summary["all_winners_equal"] is all(r["comparison"]["argmax_equal"] for r in mode_rows)
        assert summary["all_cache_isolation"] is all(r["cache_isolation"] for r in mode_rows)


def corruption_controls(result: dict) -> int:
    import copy

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
        except (AssertionError, KeyError, TypeError, ValueError):
            rejected += 1
    assert rejected == len(controls)
    return rejected
