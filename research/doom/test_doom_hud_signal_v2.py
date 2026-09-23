import copy
import json
from pathlib import Path
import sys
import unittest


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ROOT = HERE / "results/map01-soft-context-v31-live-01"
WAD = REPO / "_vizdoom/vizdoom/freedoom2.wad"
sys.path.insert(0, str(HERE))
from doom_hud_signal_v2 import DoomStatusNumberReader


class DoomHudSignalV2Tests(unittest.TestCase):
    @classmethod
    def observations(cls):
        return [json.loads(line) for line in
                (ROOT / "runtime/events.jsonl").read_text().splitlines()
                if json.loads(line).get("event") == "observation"]

    def reader(self, signal_id):
        return DoomStatusNumberReader(
            WAD, signal_id=signal_id,
            image_resolver=lambda value: ROOT / "runtime" / Path(value).name)

    def test_all_retained_v31_frames_have_exact_health_and_ammo(self):
        observations = self.observations()
        for signal_id in ("health", "ammo"):
            signals = [self.reader(signal_id).read(row) for row in observations]
            self.assertEqual(len(signals), 247)
            self.assertTrue(all(row["status"] == "observed" for row in signals))
            self.assertTrue(all(row["signal_id"] == signal_id for row in signals))

    def test_ammo_matches_independent_manual_decision_review(self):
        expected = {1: 48, 33: 48, 59: 47, 92: 47,
                    139: 46, 181: 45, 227: 45, 233: 45}
        observations = {row["sequence"]: row for row in self.observations()}
        actual = {sequence: self.reader("ammo").read(observations[sequence])["value"]
                  for sequence in expected}
        self.assertEqual(actual, expected)

    def test_signal_anchor_and_geometry_fail_closed(self):
        with self.assertRaises(ValueError):
            DoomStatusNumberReader(WAD, signal_id="armor")
        with self.assertRaises(ValueError):
            DoomStatusNumberReader(WAD, signal_id="ammo", local_anchor=(11, 411))
        observation = copy.deepcopy(self.observations()[0])
        observation["pointer_binding"]["geometry"][2] = 1
        self.assertEqual(self.reader("ammo").read(observation)["status"], "unknown")


if __name__ == "__main__":
    unittest.main()
