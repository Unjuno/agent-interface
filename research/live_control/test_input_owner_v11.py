"""Pure contract tests for input_owner_v11; no X11 display is required."""
import unittest
from unittest.mock import patch

from input_owner_v10 import InputOwner as Previous
from input_owner_v11 import InputOwner


class Lease:
    deadline = 9_999
    intent_token = "intent-test"


class InputOwnerV11Tests(unittest.TestCase):
    def owner(self):
        owner = object.__new__(InputOwner)
        owner.owner_id = "owner-test"
        return owner

    def test_key_up_is_bracketed_around_existing_v10_call(self):
        owner = self.owner()
        with patch.object(Previous, "call", return_value=None) as previous, \
             patch("input_owner_v11.time.perf_counter_ns", side_effect=[100, 145]):
            receipt = owner.call("up", Lease(), "space")
        previous.assert_called_once()
        self.assertEqual(receipt["event"], "input_release_rpc")
        self.assertEqual(receipt["operation"], "up")
        self.assertEqual(receipt["payload"], "space")
        self.assertEqual(receipt["owner_id"], "owner-test")
        self.assertEqual(receipt["intent_token"], "intent-test")
        self.assertEqual(receipt["release_transition_interval_ns"], [100, 145])
        self.assertEqual(receipt["interval_width_ns"], 45)
        self.assertEqual(receipt["valid_until_ns"], 9_999)
        self.assertTrue(receipt["x11_release_and_sync_completed_before_return"])
        self.assertFalse(receipt["continuous_physical_state_sampled"])
        self.assertFalse(receipt["application_consumption_observed"])
        self.assertFalse(receipt["grants_input_authority"])

    def test_button_up_uses_same_receipt_contract(self):
        owner = self.owner()
        with patch.object(Previous, "call", return_value=None), \
             patch("input_owner_v11.time.perf_counter_ns", side_effect=[200, 211]):
            receipt = owner.call("button_up", Lease(), 1)
        self.assertEqual(receipt["operation"], "button_up")
        self.assertEqual(receipt["payload"], 1)
        self.assertEqual(receipt["release_transition_interval_ns"], [200, 211])

    def test_non_release_operation_preserves_v10_result(self):
        owner = self.owner()
        expected = {"event": "input_admission", "input_ack_ns": 333}
        with patch.object(Previous, "call", return_value=expected) as previous, \
             patch("input_owner_v11.time.perf_counter_ns") as clock:
            actual = owner.call("down", Lease(), "a")
        self.assertIs(actual, expected)
        previous.assert_called_once()
        clock.assert_not_called()

    def test_underlying_release_failure_does_not_fabricate_receipt(self):
        owner = self.owner()
        with patch.object(Previous, "call", side_effect=RuntimeError("owner failed")), \
             patch("input_owner_v11.time.perf_counter_ns", return_value=400) as clock:
            with self.assertRaisesRegex(RuntimeError, "owner failed"):
                owner.call("up", Lease(), "a")
        # Only the pre-call timestamp is sampled; there is no successful return edge.
        self.assertEqual(clock.call_count, 1)

    def test_unexpected_v10_release_payload_fails_closed(self):
        owner = self.owner()
        with patch.object(Previous, "call", return_value={"unexpected": True}), \
             patch("input_owner_v11.time.perf_counter_ns", side_effect=[500, 510]):
            with self.assertRaisesRegex(RuntimeError, "unexpectedly returned"):
                owner.call("up", Lease(), "a")


if __name__ == "__main__":
    unittest.main()
