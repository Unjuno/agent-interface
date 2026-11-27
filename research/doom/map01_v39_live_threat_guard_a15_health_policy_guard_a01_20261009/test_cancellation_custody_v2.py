import unittest

from audit_cancellation_custody_v2 import reconcile_cancellations


def terminal(identifier, *, status="cancelled", release=None, interruption=None):
    if release is None:
        release = {"verified": True, "keys_down": [], "buttons_down": [],
                   "keys_unknown": [], "intent_token": None}
    row = {"event": "terminal", "id": identifier, "status": status,
           "release": release}
    if interruption is not None:
        row["interruption"] = interruption
    return row


class CancellationCustodyV2Tests(unittest.TestCase):
    def test_no_input_admission_uses_verified_empty_terminal(self):
        events = [
            {"event": "accepted", "id": "cover-0", "intent_token": "planned-token"},
            {"event": "cancel_requested", "id": "cover-0", "matched": True},
            terminal("cover-0"),
        ]
        result = reconcile_cancellations(events)
        self.assertTrue(result["all_cancellations_custodied"])
        self.assertEqual(result["no_active_lease_ids"], ["cover-0"])
        self.assertEqual(result["active_lease_ids"], [])

    def test_active_admission_requires_matching_owner_release(self):
        token = "active-token"
        owner_release = {"reason": "cancelled", "verified": True,
                         "keys_down": [], "buttons_down": [], "keys_unknown": [],
                         "intent_token": token}
        events = [
            {"event": "accepted", "id": "cover-1", "intent_token": token},
            {"event": "input_admission", "id": "cover-1", "intent_token": token},
            {"event": "cancel_requested", "id": "cover-1", "matched": True},
            {"event": "input_released", "id": "cover-1", "intent_token": token,
             "owner_release": owner_release},
            terminal("cover-1", interruption={"intent_token": token}),
        ]
        result = reconcile_cancellations(events)
        self.assertTrue(result["all_cancellations_custodied"])
        self.assertEqual(result["active_lease_ids"], ["cover-1"])

    def test_missing_or_mismatched_active_release_fails_closed(self):
        token = "active-token"
        events = [
            {"event": "input_admission", "id": "cover-2", "intent_token": token},
            {"event": "cancel_requested", "id": "cover-2", "matched": True},
            {"event": "input_released", "id": "cover-2", "intent_token": "wrong-token",
             "owner_release": {"reason": "cancelled", "verified": True,
                               "keys_down": [], "buttons_down": [], "keys_unknown": [],
                               "intent_token": "wrong-token"}},
            terminal("cover-2", interruption={"intent_token": token}),
        ]
        result = reconcile_cancellations(events)
        self.assertFalse(result["all_cancellations_custodied"])
        self.assertEqual(result["unaccounted_cancel_ids"], ["cover-2"])

    def test_nonempty_terminal_release_fails_closed_without_lease(self):
        events = [
            {"event": "cancel_requested", "id": "cover-3", "matched": True},
            terminal("cover-3", release={"verified": True, "keys_down": ["w"],
                                         "buttons_down": [], "keys_unknown": []}),
        ]
        result = reconcile_cancellations(events)
        self.assertFalse(result["all_cancellations_custodied"])

    def test_input_admission_without_a_valid_token_fails_closed(self):
        events = [
            {"event": "input_admission", "id": "cover-4"},
            {"event": "cancel_requested", "id": "cover-4", "matched": True},
            terminal("cover-4"),
        ]
        result = reconcile_cancellations(events)
        self.assertFalse(result["all_cancellations_custodied"])


if __name__ == "__main__":
    unittest.main()
