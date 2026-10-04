"""Current typed-backend owner composition checks; no X11 or game required."""
import unittest
from unittest.mock import patch

import doom_cancel_telemetry_backend_v1 as candidate
from doom_typed_release_backend_v2 import Backend as Previous


class FakeOwner:
    owner_id = "owner-v12-test"

    def __init__(self):
        self.calls = []
        self.closed = False

    def call(self, operation, lease=None, key=None):
        self.calls.append((operation, lease, key))
        if operation == "up":
            return {"event": "input_release_rpc", "operation": "up",
                    "payload": key, "owner_id": self.owner_id,
                    "release_transition_interval_ns": [10, 12],
                    "interval_width_ns": 2, "grants_input_authority": False}
        return None

    def close(self):
        self.closed = True


class Lease:
    intent_token = "intent-v12-test"


class DoomTypedReleaseBackendV3Tests(unittest.TestCase):
    def test_consumer_installs_v12_owner_after_previous_setup(self):
        old = FakeOwner()
        selected = FakeOwner()

        def previous_init(backend, _session, _out, _emit, _signal_readers):
            backend.owner = old
            backend._input_event_context = None

        with patch.object(Previous, "__init__", previous_init), \
                patch.object(candidate, "InputOwner", return_value=selected) as factory:
            backend = candidate.Backend(type("Session", (), {"name": ":99"})(), None,
                                        lambda _row: None, {})

        factory.assert_called_once_with(":99")
        self.assertTrue(old.closed)
        self.assertIs(backend.owner, selected)
        self.assertIsNone(backend._input_event_context)

    def test_v12_owner_retains_v11_release_interval_receipt_in_backend_event(self):
        backend = object.__new__(candidate.Backend)
        backend.owner = FakeOwner()
        backend.lease = Lease()
        backend.held = {"space"}
        backend._input_event_context = ("plan-v12", 4)
        backend.events = []
        backend.emit = backend.events.append

        backend.raw("space", False)

        self.assertEqual(backend.owner.calls, [("up", backend.lease, "space")])
        self.assertEqual(backend.held, set())
        self.assertEqual(len(backend.events), 1)
        release = backend.events[0]
        self.assertEqual(release["event"], "input_release_rpc")
        self.assertEqual(release["release_transition_interval_ns"], [10, 12])
        self.assertEqual((release["id"], release["step"]), ("plan-v12", 4))
        self.assertEqual(release["intent_token"], "intent-v12-test")


if __name__ == "__main__":
    unittest.main(verbosity=2)

