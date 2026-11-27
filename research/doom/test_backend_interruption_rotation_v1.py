import unittest

from test_map01_process_identity_backend import backend_fixture


class BackendInterruptionRotationTests(unittest.TestCase):
    def test_backend_rotates_only_after_qualified_interruption_receipt(self):
        with backend_fixture() as (backend, events, generation, fake):
            old_owner = backend.owner
            old_owner._inner.identity_reader.worker.close()
            terminal = {
                "event": "terminal", "id": "interrupted-action",
                "status": "needs_decision", "input_owner_generation": 0,
                "input_owner_id": old_owner.owner_id,
                "release": {"verified": True, "keys_down": [],
                            "buttons_down": [], "keys_unknown": [],
                            "key_state_errors": [],
                            "target_process_identity_reader": {"retired": True}},
                "interruption": {"intent_token": "intent", "record": {
                    "event": "owner_release", "intent_token": "intent",
                    "reason": "target_generation_invalidated", "verified": True,
                    "keys_down": [], "buttons_down": [], "keys_unknown": [],
                    "key_state_errors": [],
                    "target_process_identity_reader": {"retired": True},
                    "key_release_attempts": {"38": {"verified": True,
                        "attempts": [{"attempt": 1, "keyrelease_started_ns": 10,
                            "sync_returned_ns": 11, "keymap_sampled_ns": 12,
                            "server_key_down_before": True,
                            "server_key_down_after": False}]}}}}}
            receipt = backend.rotate_input_owner_after_cancel(terminal)
            self.assertEqual(receipt["generation"], 1)
            self.assertEqual(receipt["previous_owner_id"], old_owner.owner_id)
            self.assertNotEqual(receipt["owner_id"], old_owner.owner_id)
            self.assertTrue(receipt["source_invalidated"])
            with self.assertRaisesRegex(ValueError, "qualified interruption"):
                backend.rotate_input_owner_after_cancel(
                    dict(terminal, interruption={"intent_token": "intent", "record": {}}))


if __name__ == "__main__":
    unittest.main()
