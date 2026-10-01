import json
import copy
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


if __name__ == "__main__":
    unittest.main()
