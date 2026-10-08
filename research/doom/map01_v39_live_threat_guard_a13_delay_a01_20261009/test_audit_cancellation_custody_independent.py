import unittest
from audit_cancellation_custody_independent import audit


def empty(reason="release", token=None):
    return {"event": "owner_release", "reason": reason, "verified": True,
            "keys_down": [], "buttons_down": [], "keys_unknown": [],
            "intent_token": token}


class IndependentCustodyAuditTests(unittest.TestCase):
    def test_verified_empty_terminal_accounts_for_cancel_without_lease(self):
        rows = [
            {"event": "cancel_requested", "id": "cover-0", "matched": True},
            {"event": "terminal", "id": "cover-0", "status": "cancelled",
             "release": empty()},
        ]
        result = audit(rows)
        self.assertTrue(result["custody_pass"])
        self.assertEqual(result["no_lease_verified_empty_terminals"], 1)

    def test_admitted_lease_requires_same_token_cancel_release(self):
        token = "opaque-test-token"
        rows = [
            {"event": "cancel_requested", "id": "cover-1", "matched": True},
            {"event": "input_admission", "id": "cover-1", "intent_token": token},
            {"event": "input_released", "id": "cover-1", "intent_token": token,
             "owner_release": empty("cancelled", token)},
            {"event": "terminal", "id": "cover-1", "status": "cancelled",
             "release": empty(), "interruption": {"intent_token": token}},
        ]
        result = audit(rows)
        self.assertTrue(result["custody_pass"])
        self.assertEqual(result["active_lease_releases_token_matched"], 1)

    def test_mismatched_release_token_fails_closed(self):
        rows = [
            {"event": "cancel_requested", "id": "cover-2", "matched": True},
            {"event": "input_admission", "id": "cover-2", "intent_token": "lease-a"},
            {"event": "input_released", "id": "cover-2", "intent_token": "lease-b",
             "owner_release": empty("cancelled", "lease-b")},
            {"event": "terminal", "id": "cover-2", "status": "cancelled",
             "release": empty(), "interruption": {"intent_token": "lease-a"}},
        ]
        result = audit(rows)
        self.assertFalse(result["custody_pass"])
        self.assertEqual(result["unaccounted_cancellations"], 1)


if __name__ == "__main__":
    unittest.main()
