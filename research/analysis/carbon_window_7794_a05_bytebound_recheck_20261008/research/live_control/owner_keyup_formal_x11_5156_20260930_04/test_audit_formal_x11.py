import copy
import json
import unittest
from pathlib import Path

from audit_formal_x11 import audit

EXPECTED = json.loads(Path("EXPECTED.json").read_text(encoding="utf-8"))


def fixture_rows():
    rows = [{"event": "fixture"}]
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
        rows.append({"event": "joined_release", "case": case, "key": key, "keycode": code,
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
                 "request_started_ns": 20, "request_returned_ns": 30, "shared_sync_returned_ns": 40}})
    rows.append({"event": "owner_record", "record": {"event": "owner_release", "reason": "cancelled",
                 "verified": True, "keys_down": [], "buttons_down": []}})
    rows.extend([{"event": "case_terminal", "case": c, "all_up_verified": True,
                  "second_admission_rejected": c == "partial_cancel"} for c in EXPECTED["cases"]])
    rows += [{"event": "process_cleanup", "owner_stopped": True},
             {"event": "terminal_state", "neutral": True, "grants_input_authority": False},
             {"event": "runner_complete", "exit_code": 0}]
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
