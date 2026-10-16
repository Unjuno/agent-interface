"""Exact JSON-identity regressions for typed/full observation reconciliation."""
import copy
from pathlib import Path
import tempfile
import unittest

from doom_typed_observation_v1 import (
    SCHEMA,
    frame_rgb_sha256,
    reconcile_artifact,
)
from PIL import Image


class Reader:
    def __init__(self, row):
        self.row = row

    def read(self, observation):
        return copy.deepcopy(self.row)


class TypedArtifactReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.image_path = Path(self.temp.name) / "frame.png"
        image = Image.new("RGB", (2, 2), (11, 22, 33))
        image.save(self.image_path)
        self.binding = {"window": "w1", "geometry": [0, 0, 2, 2]}
        self.typed = {
            "schema": SCHEMA,
            "id": "frame-1",
            "step": 0,
            "sequence": 1,
            "capture_ns": 1,
            "pointer_binding": copy.deepcopy(self.binding),
            "frame_rgb_sha256": frame_rgb_sha256(image),
            "signals": {},
        }
        self.observation = {
            "event": "observation",
            "exact": True,
            "id": "frame-1",
            "step": 0,
            "sequence": 1,
            "capture_ns": 1,
            "pointer_binding": copy.deepcopy(self.binding),
            "image": str(self.image_path),
        }
        self.readers = {}
        for name, value in (("health", 100), ("ammo", 10)):
            row = {
                "status": "observed",
                "value": value,
                "sequence": 1,
                "capture_ns": 1,
                "binding": copy.deepcopy(self.binding),
            }
            self.typed["signals"][name] = copy.deepcopy(row)
            self.readers[name] = Reader(row)

    def reconcile(self, typed=None, observation=None):
        return reconcile_artifact(
            copy.deepcopy(self.typed if typed is None else typed),
            copy.deepcopy(self.observation if observation is None else observation),
            copy.deepcopy(self.readers),
        )

    def test_exact_identity_pair_matches(self):
        result = self.reconcile()
        self.assertTrue(result["matched"], result["checks"])
        self.assertTrue(all(result["checks"].values()), result["checks"])

    def test_boolean_integer_aliases_in_epoch_fields_do_not_match(self):
        cases = (
            ("id", True, 1),
            ("step", False, 0),
            ("sequence", True, 1),
            ("capture_ns", False, 0),
        )
        for field, typed_value, observation_value in cases:
            with self.subTest(field=field):
                typed = copy.deepcopy(self.typed)
                observation = copy.deepcopy(self.observation)
                typed[field] = typed_value
                observation[field] = observation_value
                result = self.reconcile(typed, observation)
                self.assertFalse(result["matched"], result["checks"])
                self.assertFalse(result["checks"]["same_epoch"])

    def test_nested_boolean_integer_pointer_binding_alias_does_not_match(self):
        typed = copy.deepcopy(self.typed)
        observation = copy.deepcopy(self.observation)
        typed["pointer_binding"]["geometry"][0] = True
        observation["pointer_binding"]["geometry"][0] = 1
        for name in typed["signals"]:
            typed["signals"][name]["binding"]["geometry"][0] = True
            self.readers[name].row["binding"]["geometry"][0] = 1
        result = self.reconcile(typed, observation)
        self.assertFalse(result["matched"], result["checks"])
        self.assertFalse(result["checks"]["same_binding"])


if __name__ == "__main__":
    unittest.main()
