import copy
import json
import unittest
from pathlib import Path

from audit_formal_x11 import audit

EXPECTED = json.loads(Path("EXPECTED.json").read_text(encoding="utf-8"))


def fixture_rows():
    rows = [{"event": "fixture", "allocation": "MAP01-OWNER-KEYMAP-WITNESS-5156-T3-20261001-01",
             "frozen_main": "728d30cb2bf4e3b0a183a929258064d3ba823404"}]
    for case, key, code, owner, intent in (
        ("single_explicit", "a", 38, "o1", "i1"),
        ("two_key_explicit", "a", 38, "o2", "i2"),
        ("two_key_explicit", "b", 56, "o2", "i2"),
        ("partial_cancel", "a", 38, "o3", "i3"),
    ):
        rows.append({"event": "admission", "case": case, "key": key, "keycode": code,
                     "owner_id": owner, "intent_token": intent, "down_verified": True,
                     "grants_input_authority": False})
    for case, key, code, owner, intent, n in (
        ("single_explicit", "a", 38, "o1", "i1", 0),
        ("two_key_explicit", "a", 38, "o2", "i2", 1),
        ("two_key_explicit", "b", 56, "o2", "i2", 2),
    ):
        rows.append({"event": "joined_release", "owner_event": "owner_key_release_bracket",
                     "case": case, "key": key, "keycode": code,
                     "owner_id": owner, "intent_token": intent, "trigger_class": "explicit_up",
                     "timing_valid": True, "grants_input_authority": False,
                     "physical_key_up_claimed": False, "request_started_ns": 20+n*10,
                     "request_returned_ns": 30+n*10, "shared_sync_returned_ns": 40+n*10,
                     "caller_started_ns": 10+n*10, "caller_returned_ns": 50+n*10,
                     "caller_owner_id": owner, "caller_intent_token": intent})
    rows.append({"event": "owner_record", "record": {"event": "owner_key_release_bracket",
                 "trigger_class": "owner_lease_cleanup", "reason": "cancelled", "key": None,
                 "keycode": 38, "owner_id": "o3", "intent_token": "i3", "timing_valid": True,
                 "grants_input_authority": False, "physical_key_up_claimed": False,
                 "request_started_ns": 82, "request_returned_ns": 84, "shared_sync_returned_ns": 86}})
    rows.append({"event": "owner_record", "record": {"event": "owner_release", "reason": "cancelled",
                 "verified": True, "keys_down": [], "buttons_down": []}})
    rows.extend([{"event": "case_terminal", "case": c, "all_up_verified": True,
                  "second_admission_rejected": c == "partial_cancel"} for c in EXPECTED["cases"]])
    rows += [{"event": "process_cleanup", "owner_stopped": True},
             {"event": "terminal_state", "neutral": True, "grants_input_authority": False},
             {"event": "runner_complete", "exit_code": 0}]
    # Deterministic keymap witness bytes make the older audit tests exercise the
    # strengthened raw-only contract too. Tests that need legacy bool-only rows
    # remove these records explicitly.
    states = (
        ("single_explicit", "pre_down", 5, {"a": 38}, set()),
        ("single_explicit", "post_down", 9, {"a": 38}, {"a"}),
        ("single_explicit", "post_release", 60, {"a": 38}, set()),
        ("two_key_explicit", "pre_down", 15, {"a": 38, "b": 56}, set()),
        ("two_key_explicit", "post_down", 19, {"a": 38, "b": 56}, {"a", "b"}),
        ("two_key_explicit", "post_release", 80, {"a": 38, "b": 56}, set()),
        ("partial_cancel", "pre_down", 70, {"a": 38}, set()),
        ("partial_cancel", "post_down", 80, {"a": 38}, {"a"}),
        ("partial_cancel", "post_cleanup", 90, {"a": 38}, set()),
    )
    for case, stage, stamp, keycodes, down in states:
        bitmap = bytearray(32)
        for key, code in keycodes.items():
            if key in down:
                bitmap[code // 8] |= 1 << (code % 8)
        rows.append({"event": "keymap_snapshot", "case": case, "stage": stage,
                     "observed_ns": stamp, "keycodes": keycodes, "bitmap_hex": bitmap.hex()})
    return rows


class FormalAuditTests(unittest.TestCase):
    def test_pristine_inventory_passes(self):
        self.assertEqual(audit(fixture_rows(), EXPECTED), [])

    def test_dropping_all_release_rows_fails(self):
        rows = [r for r in fixture_rows() if r.get("event") not in ("joined_release", "owner_record")]
        self.assertTrue(any("release inventory mismatch" in e for e in audit(rows, EXPECTED)))

    def test_dropping_one_per_key_release_fails(self):
        rows = fixture_rows()
        removed = False
        kept = []
        for row in rows:
            if not removed and row.get("event") == "joined_release" and row.get("key") == "b":
                removed = True
            else:
                kept.append(row)
        self.assertTrue(any("release inventory mismatch" in e for e in audit(kept, EXPECTED)))

    def test_duplicate_admission_identity_fails_closed(self):
        rows = fixture_rows()
        admission = next(r for r in rows if r.get("event") == "admission")
        rows.append(copy.deepcopy(admission))
        self.assertTrue(any("admission identity duplicated" in e for e in audit(rows, EXPECTED)))

    def test_duplicate_case_terminal_fails_closed(self):
        rows = fixture_rows()
        terminal = next(r for r in rows if r.get("event") == "case_terminal")
        rows.append(copy.deepcopy(terminal))
        self.assertTrue(any("case terminal duplicated" in e for e in audit(rows, EXPECTED)))

    def test_inverted_and_non_integer_timestamps_fail(self):
        for mutation in (lambda r: r.update(request_returned_ns=1),
                         lambda r: r.update(shared_sync_returned_ns=True)):
            rows = fixture_rows()
            item = next(r for r in rows if r.get("event") == "joined_release")
            mutation(item)
            self.assertTrue(any("ordering invalid" in e for e in audit(rows, EXPECTED)))

    def test_false_authority_and_fake_autonomous_caller_time_fail(self):
        rows = fixture_rows()
        next(r for r in rows if r.get("event") == "joined_release")["grants_input_authority"] = True
        auto = next(r["record"] for r in rows if r.get("event") == "owner_record")
        auto["caller_started_ns"] = 5
        errors = audit(rows, EXPECTED)
        self.assertTrue(any("authority" in e for e in errors))
        self.assertTrue(any("fabricate caller" in e for e in errors))

    def test_wrong_explicit_trigger_class_fails(self):
        rows = fixture_rows()
        next(r for r in rows if r.get("event") == "joined_release")["trigger_class"] = "owner_lease_cleanup"
        self.assertTrue(any("release inventory mismatch" in e or "class mismatch" in e
                            for e in audit(rows, EXPECTED)))

    def test_missing_owner_event_provenance_fails(self):
        rows = fixture_rows()
        next(r for r in rows if r.get("event") == "joined_release").pop("owner_event")
        self.assertTrue(any("source owner event provenance" in e for e in audit(rows, EXPECTED)))

    def test_two_key_release_order_is_enforced(self):
        rows = fixture_rows()
        indexes = [i for i, r in enumerate(rows) if r.get("event") == "joined_release"
                   and r.get("case") == "two_key_explicit"]
        rows[indexes[0]], rows[indexes[1]] = rows[indexes[1]], rows[indexes[0]]
        self.assertTrue(any("release order mismatch" in e for e in audit(rows, EXPECTED)))

    def test_cancel_owner_receipt_must_independently_verify_neutral(self):
        rows = fixture_rows()
        receipt = next(r["record"] for r in rows if r.get("event") == "owner_record"
                       and r.get("record", {}).get("event") == "owner_release")
        receipt["verified"] = False
        self.assertTrue(any("cancelled owner-release" in e for e in audit(rows, EXPECTED)))


if __name__ == "__main__":
    unittest.main()
