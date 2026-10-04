"""Regression tests for exact typed-observation epoch identity."""
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "live_control"))

from doom_typed_observation_v1 import (
    SCHEMA,
    build_action_snapshot,
)
from action_validity_admission_v1 import CONTRACT_FORMAT


class TypedObservationEpochExactTests(unittest.TestCase):
    def setUp(self):
        self.binding = {"focus": 10, "surface": 10,
                        "geometry": [0, 0, 100, 100]}
        self.event = {
            "event": "typed_observation",
            "schema": SCHEMA,
            "id": "frame-1",
            "step": 1,
            "sequence": 1,
            "capture_ns": 1,
            "pointer_binding": copy.deepcopy(self.binding),
            "signals": {
                name: {
                    "signal_id": name,
                    "value": value,
                    "status": "observed",
                    "sequence": 1,
                    "capture_ns": 1,
                    "binding": copy.deepcopy(self.binding),
                }
                for name, value in (("health", 100), ("ammo", 5))
            },
            "frame_rgb_sha256": "a" * 64,
            "frame_size": [2, 2],
            "typed_extraction_started_ns": 2,
            "typed_ready_ns": 3,
            "capture_to_typed_ready_ms": 0.000002,
            "artifact_published": False,
            "grants_input_authority": False,
        }
        self.contract = {
            "format": CONTRACT_FORMAT,
            "source": {"signals": {"health": {}, "ammo": {}}},
        }

    def test_exact_integer_epoch_builds_snapshot(self):
        snapshot = build_action_snapshot(self.event, self.contract)
        self.assertEqual(snapshot["sequence"], 1)
        self.assertEqual(snapshot["capture_ns"], 1)

    def test_boolean_and_float_epoch_aliases_are_rejected(self):
        for signal in ("health", "ammo"):
            for field in ("sequence", "capture_ns"):
                for alias in (True, 1.0):
                    with self.subTest(signal=signal, field=field, alias=alias):
                        event = copy.deepcopy(self.event)
                        event["signals"][signal][field] = alias
                        with self.assertRaises(ValueError):
                            build_action_snapshot(event, self.contract)

    def test_boolean_and_float_top_level_sequence_aliases_are_rejected(self):
        for alias in (True, 1.0):
            with self.subTest(alias=alias):
                event = copy.deepcopy(self.event)
                event["sequence"] = alias
                with self.assertRaises(ValueError):
                    build_action_snapshot(event, self.contract)

    def test_unrequired_signal_must_still_match_event_epoch(self):
        event = copy.deepcopy(self.event)
        event["signals"]["ammo"]["capture_ns"] = True
        contract = {"format": CONTRACT_FORMAT,
                    "source": {"signals": {"health": {}}}}
        with self.assertRaises(ValueError):
            build_action_snapshot(event, contract)


if __name__ == "__main__":
    unittest.main()
