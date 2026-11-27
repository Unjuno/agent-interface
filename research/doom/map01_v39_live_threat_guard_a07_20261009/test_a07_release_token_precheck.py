import copy
import unittest
from test_audit_a07_owner_release_reconciliation import fixture
from a07_release_token_precheck import token_precheck

class TokenPrecheckTests(unittest.TestCase):
    def test_distinct_operation_tokens_allow_further_checks(self):
        events, owner = fixture()
        self.assertEqual(token_precheck(events)["status"], "READY_FOR_FURTHER_CHECKS")

    def test_reused_token_is_unverified(self):
        events, owner = fixture()
        other = copy.deepcopy(events)
        for row in other:
            row["id"] = "cover-2"
        self.assertEqual(token_precheck(events + other)["status"], "HOLD_AMBIGUOUS_TOKEN")

    def test_missing_token_is_unverified(self):
        events, owner = fixture()
        for row in events:
            if row.get("event") == "input_admission":
                row.pop("intent_token")
        self.assertEqual(token_precheck(events)["status"], "HOLD_AMBIGUOUS_TOKEN")

    def test_multiple_tokens_in_one_cancellation_are_unverified(self):
        events, _ = fixture()
        next(row for row in reversed(events) if row.get("event") == "input_admission")["intent_token"] = "intent-2"
        self.assertEqual(token_precheck(events)["status"], "HOLD_AMBIGUOUS_TOKEN")

    def test_malformed_or_orphan_identity_is_unverified(self):
        events, _ = fixture()
        next(row for row in events if row.get("event") == "input_admission")["intent_token"] = []
        self.assertEqual(token_precheck(events)["status"], "HOLD_AMBIGUOUS_TOKEN")
        events, _ = fixture()
        next(row for row in events if row.get("event") == "input_admission")["id"] = "missing"
        self.assertEqual(token_precheck(events)["status"], "HOLD_AMBIGUOUS_TOKEN")

    def test_duplicate_cancellation_identity_is_unverified(self):
        events, _ = fixture()
        events.append(dict(events[0]))
        self.assertEqual(token_precheck(events)["status"], "HOLD_AMBIGUOUS_TOKEN")

    def test_no_input_requires_no_token(self):
        events = [{"event": "cancel_requested", "id": "c1", "matched": True}]
        self.assertEqual(token_precheck(events)["status"], "READY_FOR_FURTHER_CHECKS")

if __name__ == "__main__":
    unittest.main()
