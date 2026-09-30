import json
import unittest
from pathlib import Path
from copy import deepcopy

from audit_formal_x11 import audit
from test_audit_formal_x11 import fixture_rows


EXPECTED = json.loads(Path("EXPECTED.json").read_text(encoding="utf-8"))


def bitmap_hex(keycodes, down):
    value = bytearray(32)
    for key, code in keycodes.items():
        if key in down:
            value[code // 8] |= 1 << (code % 8)
    return value.hex()


def witness_rows():
    rows = [r for r in fixture_rows() if r.get("event") != "keymap_snapshot"]
    admissions = {(r["case"], r["key"]): r["keycode"] for r in rows if r.get("event") == "admission"}
    specs = [
        ("single_explicit", "pre_down", 5, ["a"], set()),
        ("single_explicit", "post_down", 9, ["a"], {"a"}),
        ("single_explicit", "post_release", 60, ["a"], set()),
        ("two_key_explicit", "pre_down", 15, ["a", "b"], set()),
        ("two_key_explicit", "post_down", 19, ["a", "b"], {"a", "b"}),
        ("two_key_explicit", "post_release", 80, ["a", "b"], set()),
        ("partial_cancel", "pre_down", 70, ["a"], set()),
        ("partial_cancel", "post_down", 80, ["a"], {"a"}),
        ("partial_cancel", "post_cleanup", 90, ["a"], set()),
    ]
    for case, stage, timestamp, keys, down in specs:
        keycodes = {key: admissions[(case, key)] for key in keys}
        rows.append({"event": "keymap_snapshot", "sample_id": f"{case}:{stage}",
                     "case": case, "stage": stage, "observed_ns": timestamp,
                     "keycodes": keycodes, "bitmap_hex": bitmap_hex(keycodes, down)})
    return rows


class KeymapWitnessTests(unittest.TestCase):
    def test_boolean_only_down_up_receipts_are_not_independent_evidence(self):
        rows = [r for r in fixture_rows() if r.get("event") != "keymap_snapshot"]
        errors = audit(rows, EXPECTED)
        self.assertTrue(any("keymap witness" in error for error in errors), errors)

    def test_audit_accepts_complete_raw_keymap_snapshots(self):
        self.assertEqual(audit(witness_rows(), EXPECTED), [])

    def test_bitmap_contradicting_true_summary_is_rejected(self):
        rows = witness_rows()
        sample = next(r for r in rows if r.get("sample_id") == "single_explicit:post_down")
        sample["bitmap_hex"] = bitmap_hex(sample["keycodes"], set())
        errors = audit(rows, EXPECTED)
        self.assertTrue(any("keymap witness" in error for error in errors), errors)

    def test_missing_snapshot_fails_closed(self):
        rows = witness_rows()
        rows.remove(next(r for r in rows if r.get("case") == "partial_cancel" and r.get("stage") == "post_cleanup"))
        self.assertTrue(any("snapshot inventory mismatch" in error for error in audit(rows, EXPECTED)))

    def test_bad_length_and_wrong_keycode_identity_fail_closed(self):
        for mutate in (
            lambda row: row.update(bitmap_hex="00" * 31),
            lambda row: row.update(keycodes={"a": 99}),
        ):
            rows = witness_rows()
            sample = next(r for r in rows if r.get("case") == "single_explicit" and r.get("stage") == "post_down")
            mutate(sample)
            self.assertTrue(any("keymap witness" in error for error in audit(rows, EXPECTED)))

    def test_snapshot_times_must_be_strictly_monotonic(self):
        rows = witness_rows()
        row = next(r for r in rows if r.get("case") == "single_explicit" and r.get("stage") == "post_release")
        row["observed_ns"] = 9
        self.assertTrue(any("timestamp" in error for error in audit(rows, EXPECTED)))

    def test_runner_order_pre_admission_snapshots_are_auditable(self):
        rows = witness_rows()
        pre = [r for r in rows if r.get("event") == "keymap_snapshot" and r.get("stage") == "pre_down"]
        rest = [r for r in rows if r.get("event") != "keymap_snapshot"]
        tail = [r for r in rows if r.get("event") == "keymap_snapshot" and r.get("stage") != "pre_down"]
        self.assertEqual(audit([rest[0], *pre, *rest[1:], *tail], EXPECTED), [])

    def test_nonadmitted_pressed_key_fails_full_bitmap_state(self):
        rows = witness_rows()
        sample = next(r for r in rows if r.get("case") == "single_explicit" and r.get("stage") == "post_release")
        extra = bytearray.fromhex(sample["bitmap_hex"])
        extra[7] |= 1 << 3
        sample["bitmap_hex"] = extra.hex()
        self.assertTrue(any("keymap witness" in error for error in audit(rows, EXPECTED)))

    def test_fixture_allocation_and_freeze_must_match_expected(self):
        rows = witness_rows()
        fixture = next(r for r in rows if r.get("event") == "fixture")
        fixture["allocation"] = "stale-allocation"
        self.assertTrue(any("fixture identity" in error for error in audit(rows, EXPECTED)))

    def test_fixture_frozen_main_must_match_expected(self):
        rows = witness_rows()
        fixture = next(r for r in rows if r.get("event") == "fixture")
        fixture["frozen_main"] = "stale-main"
        self.assertTrue(any("fixture identity" in error for error in audit(rows, EXPECTED)))

    def test_two_admitted_keys_must_have_distinct_keycodes(self):
        rows = witness_rows()
        second = next(r for r in rows if r.get("event") == "admission"
                      and r.get("case") == "two_key_explicit" and r.get("key") == "b")
        second["keycode"] = 38
        self.assertTrue(any("duplicate admitted keycode" in error for error in audit(rows, EXPECTED)))


if __name__ == "__main__":
    unittest.main()
