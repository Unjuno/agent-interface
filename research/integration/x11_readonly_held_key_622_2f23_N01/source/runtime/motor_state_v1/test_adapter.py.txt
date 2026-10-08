from __future__ import annotations

import copy
import unittest

from .adapter import SCHEMA, validate


def base():
    return {"schema": SCHEMA, "state_id": "s1", "owner_id": "o1", "owner_revision": 2,
            "observation_id": "obs1", "surface_id": "surface1", "coordinate_frame": "window_client",
            "commanded_pointer": {"x": 10, "y": 20}, "observed_pointer": {"x": 10, "y": 20},
            "held_keys": [], "held_buttons": [], "input_ack": {"id": "ack1", "status": "ACKED"},
            "release": {"status": "NOT_TERMINAL", "retained": False}, "uncertainty": "NONE", "events": []}


class MotorStateAdapterTests(unittest.TestCase):
    def test_confirmed_and_explicit_uncertainty(self):
        self.assertEqual(validate(base()), (True, "ok"))
        row = base(); row["uncertainty"] = "OS_UNCONFIRMED"; row["observed_pointer"] = None; row["input_ack"]["status"] = "UNKNOWN"
        self.assertEqual(validate(row), (True, "ok"))

    def test_release_requires_retained_transition(self):
        row = base(); row["release"] = {"status": "VERIFIED_EMPTY", "retained": True}
        self.assertEqual(validate(row), (False, "release_event_not_retained"))
        row["events"] = [{"type": "RELEASE_TRANSITION", "status": "VERIFIED_EMPTY"}]
        self.assertEqual(validate(row), (True, "ok"))

    def test_authority_and_implicit_confirmation_fail_closed(self):
        row = base(); row["authority"] = {"lease_id": "extend-me"}
        self.assertEqual(validate(row), (False, "unknown_or_authority_field"))
        row = base(); row["observed_pointer"] = None
        self.assertEqual(validate(row), (False, "implicit_confirmation"))

    def test_validation_is_nonmutating(self):
        row = base(); frozen = copy.deepcopy(row); validate(row)
        self.assertEqual(row, frozen)


if __name__ == "__main__":
    unittest.main()
