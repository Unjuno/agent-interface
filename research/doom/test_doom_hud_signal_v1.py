import copy
import json
from pathlib import Path
import tempfile
import unittest

from PIL import Image

from research.doom.doom_hud_signal_v1 import DoomStatusNumberReader


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
RESULT = ROOT / "results/map01-fixed-threat-v28-live-01"
CROSS_RESULT = ROOT / "results/map01-cover-threat-v23-live-02"
WAD = REPO / "_vizdoom/vizdoom/freedoom2.wad"


class DoomHudSignalTests(unittest.TestCase):
    def observations(self):
        return [json.loads(line) for line in (RESULT / "runtime/events.jsonl").read_text().splitlines()
                if json.loads(line).get("event") == "observation"]

    def reader(self):
        return DoomStatusNumberReader(
            WAD, image_resolver=lambda value: RESULT / "runtime" / Path(value).name)

    def test_retained_exact_health_sequence(self):
        observations = self.observations()
        values = {row["sequence"]: self.reader().read(row)["value"]
                  for row in observations if row["sequence"] in (1, 11, 33, 36, 37, 51, 60, 68, 70)}
        self.assertEqual(values, {1: 100, 11: 97, 33: 100, 36: 93, 37: 93,
                                  51: 87, 60: 81, 68: 79, 70: 73})

    def test_independent_retained_decision_frames_match_manual_review(self):
        index = json.loads((CROSS_RESULT / "decision-frame-index.json").read_text())
        audit = json.loads((CROSS_RESULT / "audit.json").read_text())
        observations = {row["sequence"]: row for row in (
            json.loads(line) for line in
            (CROSS_RESULT / "runtime/events.jsonl").read_text().splitlines())
            if row.get("event") == "observation"}
        actual = []
        reader = DoomStatusNumberReader(WAD)
        for item in index:
            sequence = int(Path(item["original"]).stem)
            observation = copy.deepcopy(observations[sequence])
            observation["image"] = str(CROSS_RESULT / item["retained"])
            reading = reader.read(observation)
            self.assertEqual(reading["status"], "observed")
            actual.append(reading["value"])
        self.assertEqual(actual, audit["visual_transcription"]["health"])

    def test_reader_follows_bound_window_geometry(self):
        source = self.observations()[0]
        with Image.open(RESULT / "runtime/001.png") as image, tempfile.TemporaryDirectory() as directory:
            moved = Image.new("RGB", (1300, 820), "black")
            moved.paste(image, (5, 7))
            target = Path(directory) / "moved.png"
            moved.save(target)
            observation = copy.deepcopy(source)
            observation["image"] = str(target)
            observation["pointer_binding"]["geometry"][0] += 5
            observation["pointer_binding"]["geometry"][1] += 7
            reading = DoomStatusNumberReader(WAD).read(observation)
        self.assertEqual((reading["status"], reading["value"]), ("observed", 100))

    def test_bad_environment_and_observation_fail_closed(self):
        with self.assertRaises(ValueError):
            DoomStatusNumberReader(WAD, expected_wad_sha256="0" * 64)
        with self.assertRaises(ValueError):
            DoomStatusNumberReader(WAD, signal_id="ammo")
        observation = copy.deepcopy(self.observations()[0])
        observation["pointer_binding"]["geometry"][2] = 1
        self.assertEqual(self.reader().read(observation)["status"], "unknown")
        observation = copy.deepcopy(self.observations()[0])
        observation["image"] = "missing.png"
        self.assertEqual(self.reader().read(observation)["reason"], "image_unavailable")


if __name__ == "__main__":
    unittest.main()
