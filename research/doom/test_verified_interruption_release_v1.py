import copy
import unittest

from verified_interruption_release_v1 import qualified_interruption_release


class VerifiedInterruptionReleaseTests(unittest.TestCase):
    def setUp(self):
        attempt = {"attempt": 1, "keyrelease_started_ns": 10,
                   "sync_returned_ns": 11, "keymap_sampled_ns": 12,
                   "server_key_down_before": True,
                   "server_key_down_after": False}
        self.terminal = {
            "event": "terminal", "status": "needs_decision",
            "interruption": {"intent_token": "token-a", "record": {
                "event": "owner_release", "intent_token": "token-a",
                "reason": "target_generation_invalidated", "verified": True,
                "keys_down": [], "buttons_down": [], "keys_unknown": [],
                "key_state_errors": [],
                "target_process_identity_reader": {"retired": True},
                "key_release_attempts": {"113": {
                    "verified": True, "attempts": [attempt]}}}}}

    def test_accepts_only_matching_verified_retired_owner_release(self):
        self.assertTrue(qualified_interruption_release(self.terminal, "token-a"))

    def test_rejects_wrong_token_missing_receipt_nonempty_state_or_live_reader(self):
        self.assertFalse(qualified_interruption_release(self.terminal, "token-b"))
        mutations = (
            lambda row: row["interruption"].pop("record"),
            lambda row: row["interruption"]["record"].update(verified=False),
            lambda row: row["interruption"]["record"].update(keys_down=[113]),
            lambda row: row["interruption"]["record"]["target_process_identity_reader"].update(retired=False),
            lambda row: row["interruption"]["record"]["key_release_attempts"]["113"]["attempts"][0].update(server_key_down_after=True),
            lambda row: row.update(status="completed"),
        )
        for mutate in mutations:
            candidate = copy.deepcopy(self.terminal)
            mutate(candidate)
            with self.subTest(candidate=candidate):
                self.assertFalse(qualified_interruption_release(candidate, "token-a"))


if __name__ == "__main__":
    unittest.main()
