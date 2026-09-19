from __future__ import annotations

import unittest

from .dispatch_bridge import bridge_dispatch_result
from .adapter import SCHEMA


def context(**overrides):
    value = {
        "state_id": "s1", "owner_id": "o1", "owner_revision": 1,
        "observation_id": "obs1", "surface_id": "surface1",
        "coordinate_frame": "screen", "commanded_pointer": {},
        "observed_pointer": {"x": 1, "y": 2}, "held_keys": [],
        "held_buttons": [], "input_ack": {"id": "ack1", "status": "ACKED"},
        "release": {"status": "NOT_TERMINAL", "retained": False},
        "uncertainty": "NONE", "events": [],
    }
    value.update(overrides)
    return value


class DispatchBridgeTests(unittest.TestCase):
    def test_explicit_context_maps_accepted_result(self):
        row, report = bridge_dispatch_result({"status": "accepted"}, context())
        self.assertTrue(report["accepted"])
        self.assertEqual(row["schema"], SCHEMA)

    def test_missing_context_fails_closed(self):
        row, report = bridge_dispatch_result({"status": "accepted"}, None)
        self.assertIsNone(row)
        self.assertEqual(report["reason"], "explicit_context_required")

    def test_accepted_result_cannot_invent_context(self):
        row, report = bridge_dispatch_result({"status": "accepted", "surface_id": "fake"}, None)
        self.assertIsNone(row)
        self.assertEqual(report["reason"], "explicit_context_required")

    def test_rejected_result_is_visible_but_not_accepted(self):
        row, report = bridge_dispatch_result({"status": "rejected"}, context())
        self.assertIsNone(row)
        self.assertFalse(report["accepted"])
        self.assertEqual(report["reason"], "dispatch_not_accepted")

    def test_release_transition_is_retained(self):
        row, report = bridge_dispatch_result({"status": "released"}, context())
        self.assertIsNone(row)
        self.assertEqual(report["validation"], "ok")
        self.assertEqual(report["reason"], "dispatch_not_accepted")

    def test_result_and_context_are_not_mutated(self):
        result = {"status": "failed"}
        original = context()
        snapshot = (dict(result), dict(original))
        bridge_dispatch_result(result, original)
        self.assertEqual(result, snapshot[0])
        self.assertEqual(original, snapshot[1])


if __name__ == "__main__":
    unittest.main()
