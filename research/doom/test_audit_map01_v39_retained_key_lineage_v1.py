import unittest

from audit_map01_v39_retained_key_lineage_v1 import audit


def admission(step, key, code, ack):
    return {"event": "input_admission", "id": "p", "step": step,
            "intent_token": "t", "owner_id": "o", "key": key,
            "keycode": code, "input_ack_ns": ack,
            "admitted_ns": ack - 1, "valid_until_ns": 10000,
            "target_process_identity": [1, 2, "h", 3]}


def attempt(start, sync, sample):
    return {"keyrelease_started_ns": start, "sync_returned_ns": sync,
            "keymap_sampled_ns": sample, "server_key_down_before": True,
            "server_key_down_after": False, "keyrelease_error": None,
            "sync_error": None, "keymap_before_error": None,
            "keymap_after_error": None}


def transition(source, detail):
    receipt = {**source, "operation": "down"}
    keyup = {"event": "owner_explicit_keyup", "owner_id": "o",
             "intent_token": "t", "key": source["key"],
             "keycode": source["keycode"], "server_keyup_verified": True,
             "server_keyup_attempts": [detail]}
    return {"event": "input_release_transition", "operation": "up",
            "admission_receipt": receipt, "admission_receipt_valid": True,
            "owner_transition_verified": True, "ordinary_release_candidate": True,
            "owner_cleanup_intervened": False, "release_batch_complete": True,
            "owner_id": "o", "intent_token": "t", "key": source["key"],
            "owner_thread_keyup_receipt": keyup}


class RetainedKeyLineageTests(unittest.TestCase):
    def setUp(self):
        self.first = admission(0, "a", 38, 100)
        self.last = admission(2, "a", 38, 300)
        self.events = [self.first, self.last,
                       transition(self.first, attempt(200, 210, 220))]
        self.owner = [{"event": "owner_release", "reason": "cancelled",
                       "intent_token": "t", "target_process_identity": [1, 2, "h", 3],
                       "verified": True, "keys_down": [], "keys_unknown": [],
                       "key_release_attempts": {"38": {
                           "verified": True,
                           "attempts": [attempt(400, 410, 420)]}}}]
        self.score = {"event": "post_control_score", "kill_count": 0,
                      "death_count": 0, "map_exit": False}
        self.samples = [{"controller_visible": False, "payload": {
            "schema": "independent-progress-sample-v2", "sample_ns": 500,
            "kill_count": 0, "map_exit": False}}]

    def test_distinguishes_direct_release_from_cancel_cleanup(self):
        result = audit(self.events, self.owner, self.score, self.samples)
        self.assertTrue(result["pass"])
        self.assertEqual(result["explicit_up_count"], 1)
        self.assertEqual(result["cancel_cleanup_count"], 1)
        self.assertEqual([row["step"] for row in result["matches"]], [0, 2])

    def test_unmatched_admission_fails_closed(self):
        result = audit(self.events[:2], [], self.score, self.samples)
        self.assertFalse(result["pass"])
        self.assertFalse(result["key_release_lineage_complete"])
        self.assertEqual(len(result["unresolved_admissions"]), 2)

    def test_unverified_server_transition_is_not_counted(self):
        broken = self.events[2].copy()
        broken["owner_thread_keyup_receipt"] = {
            **broken["owner_thread_keyup_receipt"],
            "server_keyup_attempts": [attempt(200, 210, 220) | {
                "server_key_down_after": True}]}
        result = audit([self.first, self.last, broken], self.owner, self.score,
                       self.samples)
        self.assertFalse(result["pass"])
        self.assertEqual(result["explicit_up_count"], 0)
        # Once the direct receipt is lost, two same-key admissions are open;
        # the cancellation record cannot safely be attributed to either.
        self.assertEqual(result["cancel_cleanup_count"], 0)


if __name__ == "__main__":
    unittest.main()
