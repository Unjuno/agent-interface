"""Pure provenance tests for doom_typed_release_backend_v2; no X11 required."""
import unittest
from unittest.mock import patch

from doom_typed_release_backend_v1 import Backend as Previous
from doom_typed_release_backend_v2 import Backend


class Lease:
    deadline = 88_000
    intent_token = "intent-v2"


class FakeOwner:
    owner_id = "owner-v11-test"

    def __init__(self):
        self.calls = []
        self.fail_on = None

    def call(self, operation, lease=None, key=None):
        self.calls.append((operation, lease, key))
        if operation == self.fail_on:
            raise RuntimeError("owner failure")
        if operation == "down":
            return {
                "event": "input_admission",
                "key": key,
                "admitted_ns": 10,
                "input_ack_ns": 11,
                "valid_until_ns": lease.deadline,
            }
        if operation == "up":
            return {
                "event": "input_release_rpc",
                "operation": "up",
                "payload": key,
                "owner_id": self.owner_id,
                "intent_token": lease.intent_token,
                "call_started_ns": 20,
                "call_returned_ns": 21,
                "release_transition_interval_ns": [20, 21],
                "interval_width_ns": 1,
                "valid_until_ns": lease.deadline,
                "x11_release_and_sync_completed_before_return": True,
                "continuous_physical_state_sampled": False,
                "application_consumption_observed": False,
                "grants_input_authority": False,
            }
        raise AssertionError(operation)


class BackendV2Tests(unittest.TestCase):
    def backend(self):
        backend = object.__new__(Backend)
        backend.owner = FakeOwner()
        backend.lease = Lease()
        backend.held = set()
        backend._input_event_context = ("plan-7", 3)
        backend.events = []
        backend.emit = backend.events.append
        return backend

    def test_down_and_release_are_bound_to_program_step(self):
        backend = self.backend()
        backend.raw("space", True)
        backend.raw("space", False)
        self.assertEqual(backend.held, set())
        self.assertEqual([row["event"] for row in backend.events],
                         ["input_admission", "input_release_rpc"])
        for row in backend.events:
            self.assertEqual(row["id"], "plan-7")
            self.assertEqual(row["step"], 3)
            self.assertEqual(row["owner_id"], "owner-v11-test")
            self.assertEqual(row["intent_token"], "intent-v2")
        release = backend.events[-1]
        self.assertEqual(release["release_transition_interval_ns"], [20, 21])
        self.assertFalse(release["grants_input_authority"])

    def test_missing_context_rejects_before_owner_call(self):
        backend = self.backend()
        backend._input_event_context = None
        with self.assertRaisesRegex(RuntimeError, "outside program/step"):
            backend.raw("a", True)
        self.assertEqual(backend.owner.calls, [])
        self.assertEqual(backend.events, [])
        self.assertEqual(backend.held, set())

    def test_failed_release_keeps_backend_hold_tracking(self):
        backend = self.backend()
        backend.raw("a", True)
        backend.owner.fail_on = "up"
        with self.assertRaisesRegex(RuntimeError, "owner failure"):
            backend.raw("a", False)
        self.assertEqual(backend.held, {"a"})
        self.assertEqual(len(backend.events), 1)

    def test_execute_sets_and_clears_context_even_on_error(self):
        backend = object.__new__(Backend)
        backend._input_event_context = None
        sentinel = ValueError("synthetic")
        with patch.object(Previous, "execute", side_effect=sentinel) as previous:
            with self.assertRaises(ValueError):
                backend.execute({"op": "observe"}, object(), "p", 4)
        previous.assert_called_once()
        self.assertIsNone(backend._input_event_context)

    def test_nested_context_fails_before_previous_execute(self):
        backend = object.__new__(Backend)
        backend._input_event_context = ("other", 0)
        with patch.object(Previous, "execute") as previous:
            with self.assertRaisesRegex(RuntimeError, "nested"):
                backend.execute({"op": "observe"}, object(), "p", 4)
        previous.assert_not_called()


if __name__ == "__main__":
    unittest.main()
