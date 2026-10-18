import json
import copy
import hashlib
import tempfile
from pathlib import Path
import sys
import unittest

from PIL import Image


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "live_control"))
from doom_hud_signal_v3 import DoomStatusNumberReader
from doom_typed_observation_v1 import (
    build_action_snapshot, extract_typed_observation, reconcile_artifact)
from action_validity_admission_v1 import CONTRACT_FORMAT


WAD = REPO / "_vizdoom/vizdoom/freedoom2.wad"
RUNTIME = HERE / "results/map01-soft-context-v31-live-01/runtime"


class DoomHudSignalV3Tests(unittest.TestCase):
    def test_in_memory_and_retained_png_paths_match_all_v31_frames(self):
        readers = [DoomStatusNumberReader(WAD, signal_id=name)
                   for name in ("health", "ammo")]
        observations = [json.loads(line) for line in
            (RUNTIME / "events.jsonl").read_text(encoding="utf-8").splitlines()
            if json.loads(line).get("event") == "observation"]
        self.assertEqual(len(observations), 247)
        for original in observations:
            observation = dict(original)
            observation["image"] = str(RUNTIME / Path(original["image"]).name)
            with Image.open(observation["image"]) as opened:
                frame = opened.convert("RGB")
            for reader in readers:
                self.assertEqual(reader.read_frame(observation, frame),
                                 reader.read(observation))

    def test_in_memory_path_fails_closed_without_frame(self):
        reader = DoomStatusNumberReader(WAD, signal_id="health")
        observation = {"sequence": 1, "capture_ns": 2,
                       "pointer_binding": {"focus": 1, "surface": 1,
                                           "geometry": [0, 0, 640, 480]}}
        result = reader.read_frame(observation, None)
        self.assertEqual(result["status"], "unknown")
        self.assertEqual(result["reason"], "frame_unavailable")

    def test_early_event_builds_snapshot_and_reconciles_to_retained_png(self):
        original = next(json.loads(line) for line in
            (RUNTIME / "events.jsonl").read_text(encoding="utf-8").splitlines()
            if json.loads(line).get("event") == "observation")
        observation = dict(original)
        observation["image"] = str(RUNTIME / Path(original["image"]).name)
        readers = {name: DoomStatusNumberReader(WAD, signal_id=name)
                   for name in ("health", "ammo")}
        with Image.open(observation["image"]) as opened:
            frame = opened.convert("RGB")
        ticks = iter([observation["capture_ns"] + 1,
                      observation["capture_ns"] + 2])
        typed = extract_typed_observation(frame, {
            "id": observation["id"], "step": observation["step"],
            "sequence": observation["sequence"],
            "capture_ns": observation["capture_ns"],
            "pointer_binding": observation["pointer_binding"]}, readers,
            clock=lambda: next(ticks))
        contract = {"format": CONTRACT_FORMAT,
                    "source": {"signals": {"health": {}, "ammo": {}}}}
        snapshot = build_action_snapshot(typed, contract)
        self.assertEqual(snapshot["signals"]["health"]["value"], 97)
        self.assertEqual(snapshot["signals"]["ammo"]["value"], 48)
        reconciliation = reconcile_artifact(typed, observation, readers)
        self.assertTrue(reconciliation["matched"])
        self.assertTrue(all(reconciliation["checks"].values()))
        for field, value in (("frame_rgb_sha256", "not-a-digest"),
                             ("typed_ready_ns", observation["capture_ns"] - 1),
                             ("artifact_published", True)):
            malformed = copy.deepcopy(typed)
            malformed[field] = value
            with self.assertRaises(ValueError):
                build_action_snapshot(malformed, contract)


class DoomTypedArtifactIdentityTests(unittest.TestCase):
    def setUp(self):
        self._temporary_directory = tempfile.TemporaryDirectory()
        self.image_path = Path(self._temporary_directory.name) / "frame.png"
        frame = Image.new("RGB", (2, 2), (17, 34, 51))
        frame.save(self.image_path)
        self.typed = {
            "schema": "doom-typed-observation-v1",
            "id": 1, "step": 1, "sequence": 1, "capture_ns": 1,
            "pointer_binding": {"focus": 1, "surface": 0,
                                "geometry": [0, 0, 1, 1]},
            "frame_rgb_sha256": hashlib.sha256(
                frame.convert("RGB").tobytes()).hexdigest(),
        }
        self.observation = {
            "event": "observation", "exact": True,
            "id": 1, "step": 1, "sequence": 1, "capture_ns": 1,
            "pointer_binding": {"focus": 1, "surface": 0,
                                "geometry": [0, 0, 1, 1]},
            "image": str(self.image_path),
        }

    def tearDown(self):
        self._temporary_directory.cleanup()

    def test_exact_typed_and_full_observation_identity_still_matches(self):
        result = reconcile_artifact(self.typed, self.observation, {})
        self.assertTrue(result["matched"], result)
        self.assertTrue(all(result["checks"].values()), result)

    def test_boolean_integer_aliases_in_each_epoch_field_are_rejected(self):
        for field in ("id", "step", "sequence", "capture_ns"):
            for side in ("typed", "observation"):
                with self.subTest(field=field, side=side):
                    typed = copy.deepcopy(self.typed)
                    observation = copy.deepcopy(self.observation)
                    target = typed if side == "typed" else observation
                    target[field] = True
                    result = reconcile_artifact(typed, observation, {})
                    self.assertFalse(result["checks"]["same_epoch"],
                                     (field, side, result))
                    self.assertFalse(result["matched"], (field, side, result))

    def test_boolean_integer_aliases_inside_pointer_binding_are_rejected(self):
        cases = (("focus", True), ("surface", False),
                 (("geometry", 0), False), (("geometry", 1), False),
                 (("geometry", 2), True), (("geometry", 3), True))
        for path, alias in cases:
            if isinstance(path, str):
                path = (path,)
            for side in ("typed", "observation"):
                with self.subTest(path=path, side=side):
                    typed = copy.deepcopy(self.typed)
                    observation = copy.deepcopy(self.observation)
                    target = typed if side == "typed" else observation
                    value = target["pointer_binding"]
                    for key in path[:-1]:
                        value = value[key]
                    value[path[-1]] = alias
                    result = reconcile_artifact(typed, observation, {})
                    self.assertFalse(result["checks"]["same_binding"],
                                     (path, side, result))
                    self.assertFalse(result["matched"], (path, side, result))

    def test_missing_epoch_identity_is_not_treated_as_matching(self):
        typed = copy.deepcopy(self.typed)
        observation = copy.deepcopy(self.observation)
        typed.pop("step")
        observation.pop("step")
        result = reconcile_artifact(typed, observation, {})
        self.assertFalse(result["checks"]["same_epoch"], result)
        self.assertFalse(result["matched"], result)

    def test_missing_pointer_bindings_are_not_treated_as_matching(self):
        typed = copy.deepcopy(self.typed)
        observation = copy.deepcopy(self.observation)
        typed.pop("pointer_binding")
        observation.pop("pointer_binding")
        result = reconcile_artifact(typed, observation, {})
        self.assertFalse(result["checks"]["same_binding"], result)
        self.assertFalse(result["matched"], result)


if __name__ == "__main__":
    unittest.main()
