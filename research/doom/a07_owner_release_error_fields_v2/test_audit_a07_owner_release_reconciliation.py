import unittest

from audit_a07_owner_release_reconciliation import audit


def fixture():
    token = "intent-1"
    release = {
        "verified": True,
        "keys_down": [], "buttons_down": [], "keys_unknown": [],
        "key_release_attempts": {
            "40": {"verified": True, "attempts": [{
                "server_key_down_before": True,
                "server_key_down_after": False,
                "sync_returned_ns": 25,
                "keyrelease_error": None,
                "sync_error": None,
            }]},
        },
    }
    events = [
        {"event": "cancel_requested", "id": "cover-1", "matched": True,
         "requested_ns": 30},
        {"event": "input_admission", "id": "cover-1", "key": "d",
         "intent_token": token, "admitted_ns": 10},
        {"event": "keys_held", "id": "cover-1", "keys": ["d"]},
        {"event": "input_release_transition", "id": "cover-1", "key": "d",
         "owner_thread_keyup_verified": True, "release_batch_complete": True},
        {"event": "input_admission", "id": "cover-1", "key": "d",
         "intent_token": token, "admitted_ns": 20},
        {"event": "keys_held", "id": "cover-1", "keys": ["d"]},
        {"event": "input_released", "id": "cover-1", "owner_release": release},
        {"event": "terminal", "id": "cover-1", "release": {
            "verified": True, "keys_down": [], "buttons_down": [],
            "keys_unknown": [],
        }},
    ]
    owner_events = [{"event": "owner_explicit_keyup", "key": "d", "keycode": 40,
                     "intent_token": token}]
    return events, owner_events


class OwnerReleaseReconciliationTests(unittest.TestCase):
    def test_terminal_owner_release_accounts_for_last_unbatched_keyup(self):
        events, owner_events = fixture()
        result = audit(events, owner_events)
        self.assertEqual(result["status"], "PASS_CUSTODY_RECONCILED_SCOPED")
        self.assertFalse(result["formal_pass"])
        row = result["cancellations"][0]
        self.assertEqual(row["terminal_owner_release_accounts_for"]["d"], {
            "missing_explicit_transition_count": 1,
            "keycode": "40",
            "verified_terminal_keyup_count": 1,
            "owner_release_key_verified": True,
        })

    def test_missing_terminal_keyup_attempt_fails_closed(self):
        events, owner_events = fixture()
        events[6]["owner_release"]["key_release_attempts"]["40"]["attempts"] = []
        result = audit(events, owner_events)
        self.assertEqual(result["status"], "FAIL")
        self.assertFalse(result["cancellations"][0]["pass"])

    def test_post_cancel_admission_fails_closed(self):
        events, owner_events = fixture()
        events[4]["admitted_ns"] = 31
        result = audit(events, owner_events)
        self.assertEqual(result["status"], "FAIL")

    def test_empty_cancel_without_admission_needs_no_release_event(self):
        events = [
            {"event": "cancel_requested", "id": "cover-0", "matched": True,
             "requested_ns": 10},
            {"event": "terminal", "id": "cover-0", "release": {
                "verified": True, "keys_down": [], "buttons_down": [],
                "keys_unknown": [],
            }},
        ]
        result = audit(events, [])
        self.assertEqual(result["status"], "PASS_CUSTODY_RECONCILED_SCOPED")

    def test_duplicate_cancellation_id_fails_closed(self):
        events, owner_events = fixture()
        events.append({"event": "cancel_requested", "id": "cover-1",
                       "matched": True, "requested_ns": 30})
        result = audit(events, owner_events)
        self.assertEqual(result["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
