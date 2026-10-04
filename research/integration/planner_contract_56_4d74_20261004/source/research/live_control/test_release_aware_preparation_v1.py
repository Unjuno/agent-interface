import unittest

from research.live_control.release_aware_preparation_v1 import ReleaseAwarePreparation


def accepted():
    return {"event": "accepted", "id": "a", "intent_token": "t", "accepted_ns": 10}


def released():
    owner = {"event": "owner_release", "reason": "focus_changed", "verified": True,
             "keys_down": [], "buttons_down": [], "verified_ns": 20}
    return {"event": "input_released", "id": "a", "intent_token": "t",
            "owner_release": owner, "published_ns": 25,
            "program_terminal_pending": True, "grants_input_authority": False}


def terminal():
    return {"event": "terminal", "id": "a", "status": "needs_decision",
            "terminal_ns": 100, "interruption": {"intent_token": "t",
            "record": released()["owner_release"]}}


class ReleaseAwarePreparationTests(unittest.TestCase):
    def tracker(self):
        tracker = ReleaseAwarePreparation("a")
        tracker.ingest({"status": "boundary", "records": [accepted(), released()]})
        return tracker

    def test_prepares_during_terminal_wait_without_authority(self):
        tracker = self.tracker()
        self.assertEqual(tracker.begin(30)["state"], "PREPARING_AWAITING_TERMINAL")
        prepared = tracker.complete({"op": "inspect", "region": "toolbar"}, 70)
        self.assertEqual(prepared["state"], "PREPARED_AWAITING_TERMINAL")
        self.assertFalse(prepared["may_submit_to_executor"])
        final = tracker.ingest({"status": "boundary", "records": [terminal()]})
        self.assertEqual(final["state"], "PREPARED_REQUIRES_FRESH_ACTION_VALIDITY")
        self.assertEqual(final["overlap_before_terminal_ns"], 70)
        self.assertTrue(final["requires_fresh_action_validity"])
        self.assertFalse(final["grants_input_authority"])

    def test_cannot_prepare_before_release(self):
        tracker = ReleaseAwarePreparation("a")
        tracker.ingest({"status": "boundary", "records": [accepted()]})
        with self.assertRaises(ValueError): tracker.begin(15)

    def test_wrong_terminal_fails_closed(self):
        tracker = self.tracker(); tracker.begin(30); tracker.complete({"op": "inspect"}, 60)
        wrong = terminal(); wrong["interruption"]["intent_token"] = "wrong"
        result = tracker.ingest({"status": "boundary", "records": [wrong]})
        self.assertEqual(result["state"], "NEEDS_RECONCILIATION")
        self.assertFalse(result["may_submit_to_executor"])

    def test_candidate_is_copied_and_hashed(self):
        tracker = self.tracker(); tracker.begin(30)
        candidate = {"op": "inspect", "args": [1]}
        first = tracker.complete(candidate, 40); candidate["args"].append(2)
        self.assertEqual(first["candidate"], {"op": "inspect", "args": [1]})
        self.assertEqual(tracker.view()["candidate"], first["candidate"])


if __name__ == "__main__": unittest.main()
