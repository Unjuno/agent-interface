import copy
import unittest
from test_audit_live_v3 import AuditLiveV3Tests
import audit_live_v6 as v6

class V6TokenTests(unittest.TestCase):
    def fixture(self):
        h = AuditLiveV3Tests()
        events, decisions, scorer = h.valid_case(admitted=True)
        for row in events:
            if row["event"] in ("input_admission", "input_release_transition"):
                row.update(step=1, intent_token="t1")
        return h, events, decisions, scorer

    def test_shared_token_cannot_pass(self):
        h, events, decisions, scorer = self.fixture()
        other = copy.deepcopy(events)
        for row in other:
            row["id"] = "c2"
        result, _ = h.run_audit(events + other, decisions, scorer, auditor=v6, result_name="AUDIT_V6.json")
        self.assertNotEqual(result["status"], "PASS")
        self.assertFalse(result["scoped_pass"])

    def test_missing_token_never_passes(self):
        h, events, decisions, scorer = self.fixture()
        next(row for row in events if row["event"] == "input_admission").pop("intent_token")
        result, _ = h.run_audit(events, decisions, scorer, auditor=v6, result_name="AUDIT_V6.json")
        self.assertNotEqual(result["status"], "PASS")
        self.assertFalse(result["checks"]["token_ownership_unambiguous"])

    def test_invalid_release_remains_fail_even_if_token_is_ambiguous(self):
        h, events, decisions, scorer = self.fixture()
        next(row for row in events if row["event"] == "input_release_transition")["owner_thread_keyup_verified"] = False
        other = copy.deepcopy(events)
        for row in other:
            row["id"] = "c2"
        result, _ = h.run_audit(events + other, decisions, scorer, auditor=v6, result_name="AUDIT_V6.json")
        self.assertEqual(result["status"], "FAIL")

    def test_distinct_token_and_exact_transition_can_pass_scoped(self):
        h, events, decisions, scorer = self.fixture()
        result, _ = h.run_audit(events, decisions, scorer, auditor=v6, result_name="AUDIT_V6.json")
        self.assertEqual(result["status"], "PASS")
        self.assertFalse(result["formal_pass"])

if __name__ == "__main__":
    unittest.main()
