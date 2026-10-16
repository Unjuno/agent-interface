import copy
import unittest

from audit_v2 import audit
from runner_v2 import build_raw


EXPECTED = [
    {"release_id": "fixture-explicit-a-01", "owner_id": "owner-a",
     "intent_token": "intent-a", "keycode": 38,
     "trigger_class": "explicit_up", "reason": "explicit_up"},
    {"release_id": "fixture-cancel-b-01", "owner_id": "owner-b",
     "intent_token": "intent-b", "keycode": 56,
     "trigger_class": "owner_lease_cleanup", "reason": "cancelled"},
]


class AuditCompletenessTests(unittest.TestCase):
    def setUp(self):
        self.raw = build_raw(copy.deepcopy(EXPECTED))

    def test_complete_inventory_passes(self):
        self.assertEqual(audit(EXPECTED, self.raw["records"]), [])

    def test_deleting_all_brackets_fails(self):
        errors = audit(EXPECTED, [])
        self.assertTrue(any(x.startswith("expected_release_missing:") for x in errors))

    def test_deleting_one_expected_bracket_fails(self):
        errors = audit(EXPECTED, self.raw["records"][:1])
        self.assertTrue(any("fixture-cancel-b-01" in x for x in errors))

    def test_duplicate_release_fails(self):
        rows = self.raw["records"] + [copy.deepcopy(self.raw["records"][0])]
        self.assertTrue(any("unexpected_duplicate_release" in x
                            for x in audit(EXPECTED, rows)))

    def test_unexpected_release_fails(self):
        row = copy.deepcopy(self.raw["records"][0])
        row["release_id"] = "unregistered"
        self.assertTrue(any("unexpected_release:unregistered" in x
                            for x in audit(EXPECTED, self.raw["records"] + [row])))

    def test_identity_change_fails(self):
        rows = copy.deepcopy(self.raw["records"])
        rows[0]["intent_token"] = "other-intent"
        self.assertTrue(any("release_identity_mismatch" in x for x in audit(EXPECTED, rows)))

    def test_non_bracket_event_fails_closed(self):
        rows = copy.deepcopy(self.raw["records"])
        rows[0]["event"] = "owner_release"
        self.assertTrue(any("unexpected_event" in x for x in audit(EXPECTED, rows)))

    def test_boolean_timestamp_is_rejected(self):
        rows = copy.deepcopy(self.raw["records"])
        rows[0]["request_started_ns"] = True
        self.assertTrue(any("timestamp_type:request_started_ns" in x
                            for x in audit(EXPECTED, rows)))

    def test_inverted_timestamps_are_rejected(self):
        rows = copy.deepcopy(self.raw["records"])
        rows[0]["request_returned_ns"] = rows[0]["request_started_ns"] - 1
        self.assertTrue(any("timestamp_order" in x for x in audit(EXPECTED, rows)))

    def test_authority_escalation_is_rejected(self):
        rows = copy.deepcopy(self.raw["records"])
        rows[0]["grants_input_authority"] = True
        self.assertTrue(any("authority" in x for x in audit(EXPECTED, rows)))

    def test_physical_key_up_claim_is_rejected(self):
        rows = copy.deepcopy(self.raw["records"])
        rows[0]["physical_key_up_claimed"] = True
        self.assertTrue(any("physical_claim" in x for x in audit(EXPECTED, rows)))

    def test_empty_frozen_inventory_fails_closed(self):
        self.assertEqual(audit([], []), ["expected_inventory_missing_or_empty"])


if __name__ == "__main__":
    unittest.main()
