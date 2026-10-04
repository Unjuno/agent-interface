"""Composition checks for the cancellation-aware owner successor."""
import unittest
from unittest.mock import ANY, patch

from input_owner_v10 import InputOwner as Base
from input_owner_v11 import InputOwner as Telemetry
from input_owner_v12 import InputOwner


class Lease:
    deadline = 1_000
    intent_token = "intent-v12"


class InputOwnerV12Tests(unittest.TestCase):
    def test_v12_preserves_v11_release_interval_telemetry(self):
        owner = object.__new__(InputOwner)
        owner.owner_id = "owner-v12"
        self.assertTrue(issubclass(InputOwner, Telemetry))

        with patch.object(Base, "call", return_value=None) as base_call, \
                patch("input_owner_v11.time.perf_counter_ns", side_effect=[100, 145]):
            receipt = owner.call("up", Lease(), "space")

        base_call.assert_called_once_with("up", ANY, "space")
        self.assertEqual(receipt["event"], "input_release_rpc")
        self.assertEqual(receipt["release_transition_interval_ns"], [100, 145])
        self.assertEqual(receipt["intent_token"], "intent-v12")
        self.assertFalse(receipt["grants_input_authority"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
