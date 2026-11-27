import unittest
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "doom"))
from test_running_action_guard_v3 import guard_v3, program, admission, COMMANDS


class InterruptedTerminalGuardTests(unittest.TestCase):
    def armed(self):
        guard = guard_v3()
        binding = program("primary", COMMANDS[:1], [0])
        submit, accepted = admission("p-interrupted", binding)
        accepted["intent_token"] = "intent-z"
        guard.admit_program(binding, submit, accepted)
        return guard, accepted

    def terminal(self, accepted):
        attempt = {"attempt": 1, "keyrelease_started_ns": 300,
                   "sync_returned_ns": 301, "keymap_sampled_ns": 302,
                   "server_key_down_before": True,
                   "server_key_down_after": False}
        return {"event": "terminal", "id": accepted["id"],
                "status": "needs_decision", "terminal_ns": 320,
                "release": {"verified": True, "verified_ns": 310,
                            "keys_down": [], "buttons_down": [],
                            "keys_unknown": [], "key_state_errors": []},
                "interruption": {"intent_token": "intent-z", "record": {
                    "event": "owner_release", "intent_token": "intent-z",
                    "reason": "target_generation_invalidated", "verified": True,
                    "keys_down": [], "buttons_down": [], "keys_unknown": [],
                    "key_state_errors": [],
                    "target_process_identity_reader": {"retired": True},
                    "key_release_attempts": {"113": {
                        "verified": True, "attempts": [attempt]}}}}}

    def test_matching_interruption_closes_action_without_cancellation_receipt(self):
        guard, accepted = self.armed()
        receipt = guard.record_interrupted_terminal(self.terminal(accepted))
        self.assertEqual(receipt["state"], "REVOKED_ACTION_NOT_CURRENT")
        self.assertFalse(receipt["current_input_authority"])
        self.assertFalse(receipt["physical_input_may_be_down"])
        self.assertTrue(receipt["requires_new_decision"])
        self.assertIsNone(receipt["active_intent"])

    def test_mismatched_interruption_keeps_guard_active(self):
        guard, accepted = self.armed()
        bad = self.terminal(accepted)
        bad["interruption"]["intent_token"] = "other"
        bad["interruption"]["record"]["intent_token"] = "other"
        with self.assertRaises(ValueError):
            guard.record_interrupted_terminal(bad)
        self.assertEqual(guard.receipt()["state"], "INPUT_ACTIVE")


if __name__ == "__main__":
    unittest.main()
