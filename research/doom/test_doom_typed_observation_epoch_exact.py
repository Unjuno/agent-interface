"""Regression tests for exact typed-observation epoch identity."""
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "live_control"))

from doom_typed_observation_v1 import (
    SCHEMA,
    build_action_snapshot,
    extract_typed_observation,
)
from action_validity_admission_v1 import CONTRACT_FORMAT
from PIL import Image


class TypedObservationEpochExactTests(unittest.TestCase):
    def setUp(self):
        self.binding = {"focus": 1, "surface": 1,
                        "geometry": [1, 1, 100, 100]}
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

    def test_boolean_and_float_aliases_in_top_level_binding_are_rejected(self):
        for key in ("focus", "surface", "geometry"):
            for alias in (True, 1.0):
                with self.subTest(key=key, alias=alias):
                    event = copy.deepcopy(self.event)
                    if key == "geometry":
                        event["pointer_binding"][key][0] = alias
                    else:
                        event["pointer_binding"][key] = alias
                    with self.assertRaises(ValueError):
                        build_action_snapshot(event, self.contract)

    def test_boolean_and_float_aliases_in_signal_bindings_are_rejected(self):
        for signal in ("health", "ammo"):
            for key in ("focus", "surface", "geometry"):
                for alias in (True, 1.0):
                    with self.subTest(signal=signal, key=key, alias=alias):
                        event = copy.deepcopy(self.event)
                        if key == "geometry":
                            event["signals"][signal]["binding"][key][0] = alias
                        else:
                            event["signals"][signal]["binding"][key] = alias
                        with self.assertRaises(ValueError):
                            build_action_snapshot(event, self.contract)

    def test_extraction_rejects_nested_binding_aliases_before_reader_calls(self):
        class Reader:
            def __init__(self, signal_id):
                self.signal_id = signal_id
                self.called = False

            def read_frame(self, observation, frame):
                self.called = True
                return {
                    "format": "observable-signal-v1",
                    "status": "observed",
                    "signal_id": self.signal_id,
                    "value": 100,
                    "sequence": observation["sequence"],
                    "capture_ns": observation["capture_ns"],
                    "binding": observation["pointer_binding"],
                    "wad_sha256": "b" * 64,
                }

        for key in ("focus", "surface", "geometry"):
            with self.subTest(key=key):
                metadata = {
                    "id": "frame-1", "step": 1, "sequence": 1,
                    "capture_ns": 1,
                    "pointer_binding": copy.deepcopy(self.binding),
                }
                if key == "geometry":
                    metadata["pointer_binding"][key][0] = True
                else:
                    metadata["pointer_binding"][key] = True
                readers = {name: Reader(name) for name in ("health", "ammo")}
                with self.assertRaises(ValueError):
                    extract_typed_observation(
                        Image.new("RGB", (2, 2)), metadata, readers,
                        clock=iter((2, 3)).__next__)
                self.assertFalse(any(reader.called for reader in readers.values()))

    def test_extraction_rejects_reader_epoch_aliases(self):
        class Reader:
            def __init__(self, signal_id, field=None, alias=None):
                self.signal_id = signal_id
                self.field = field
                self.alias = alias

            def read_frame(self, observation, frame):
                result = {
                    "format": "observable-signal-v1",
                    "status": "observed",
                    "signal_id": self.signal_id,
                    "value": 100,
                    "sequence": observation["sequence"],
                    "capture_ns": observation["capture_ns"],
                    "binding": copy.deepcopy(observation["pointer_binding"]),
                    "wad_sha256": "b" * 64,
                }
                if self.signal_id == "health" and self.field:
                    result[self.field] = self.alias
                return result

        for field in ("sequence", "capture_ns"):
            for alias in (True, 1.0):
                with self.subTest(field=field, alias=alias):
                    metadata = {
                        "id": "frame-1", "step": 1, "sequence": 1,
                        "capture_ns": 1,
                        "pointer_binding": copy.deepcopy(self.binding),
                    }
                    readers = {
                        "health": Reader("health", field, alias),
                        "ammo": Reader("ammo"),
                    }
                    with self.assertRaises(ValueError):
                        extract_typed_observation(
                            Image.new("RGB", (2, 2)), metadata, readers,
                            clock=iter((2, 3)).__next__)

    def test_extraction_rejects_reader_binding_aliases(self):
        class Reader:
            def __init__(self, signal_id):
                self.signal_id = signal_id

            def read_frame(self, observation, frame):
                binding = copy.deepcopy(observation["pointer_binding"])
                if self.signal_id == "health":
                    binding["focus"] = True
                return {
                    "format": "observable-signal-v1",
                    "status": "observed",
                    "signal_id": self.signal_id,
                    "value": 100,
                    "sequence": observation["sequence"],
                    "capture_ns": observation["capture_ns"],
                    "binding": binding,
                    "wad_sha256": "b" * 64,
                }

        metadata = {
            "id": "frame-1", "step": 1, "sequence": 1,
            "capture_ns": 1,
            "pointer_binding": copy.deepcopy(self.binding),
        }
        readers = {name: Reader(name) for name in ("health", "ammo")}
        with self.assertRaises(ValueError):
            extract_typed_observation(
                Image.new("RGB", (2, 2)), metadata, readers,
                clock=iter((2, 3)).__next__)


if __name__ == "__main__":
    unittest.main()
