import json
import unittest
from pathlib import Path
import struct
import zlib

from png_decode import region_label

ROOT = Path(__file__).parent


class FrozenDesignTests(unittest.TestCase):
    def test_schedule_has_24_per_state_and_round_robin_prefix(self):
        schedule = json.loads((ROOT / "schedule.json").read_text())
        self.assertEqual(72, len(schedule["captures"]))
        counts = {state: 0 for state in ("s0", "s1", "s2")}
        for item in schedule["captures"]:
            counts[item["state"]] += 1
        self.assertEqual({"s0": 24, "s1": 24, "s2": 24}, counts)
        self.assertEqual(["s0", "s1", "s2"] * 17, [x["state"] for x in schedule["captures"][:51]])

    def test_three_states_are_pixel_and_accessibility_distinct(self):
        fixture = json.loads((ROOT / "states.json").read_text())
        self.assertEqual(3, len({(tuple(s["left_rgb"]), tuple(s["right_rgb"])) for s in fixture["states"]}))
        self.assertEqual(3, len({(s["left"], s["right"]) for s in fixture["states"]}))
        self.assertEqual(960, fixture["viewport"]["width"])
        self.assertEqual({"x": 180, "y": 260, "width": 1, "height": 1}, fixture["pixel_regions"]["left_roi_png"][0])
        self.assertEqual({"x": 660, "y": 260, "width": 1, "height": 1}, fixture["pixel_regions"]["full_png"][1])

    def test_loss_tables_have_one_row_per_state_and_four_actions(self):
        fixture = json.loads((ROOT / "states.json").read_text())
        self.assertEqual(4, len(fixture["actions"]))
        for problem in fixture["decision_problems"].values():
            self.assertEqual(3, len(problem["loss"]))
            self.assertTrue(all(len(row) == 4 for row in problem["loss"]))
        self.assertEqual(fixture["decision_problems"]["choose_left"]["loss"][1], fixture["decision_problems"]["choose_left"]["loss"][2])
        self.assertEqual(fixture["decision_problems"]["choose_right"]["loss"][0], fixture["decision_problems"]["choose_right"]["loss"][1])

    def test_expected_relations_encode_two_incomparable_rois(self):
        fixture = json.loads((ROOT / "states.json").read_text())
        rel = fixture["expected_relations"]
        self.assertFalse(rel["left_roi_png"]["right_roi_png"])
        self.assertFalse(rel["right_roi_png"]["left_roi_png"])
        self.assertTrue(rel["left_roi_png"]["mutation_delta"])
        self.assertTrue(rel["full_png"]["accessibility_snapshot"])

    def test_independent_png_decoder_reads_exact_rgb_and_rejects_unknown(self):
        def png(rgb):
            raw = b"\x00" + bytes(rgb)
            def chunk(tag, body):
                import binascii
                return struct.pack(">I", len(body)) + tag + body + struct.pack(">I", binascii.crc32(tag + body) & 0xffffffff)
            return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")
        palette = [[230, 57, 70], [42, 157, 143], [69, 123, 157]]
        self.assertEqual("rgb:230,57,70", region_label(png(palette[0]), {"x": 0, "y": 0, "width": 1, "height": 1}, palette))
        self.assertEqual("unresolved", region_label(png([0, 0, 0]), {"x": 0, "y": 0, "width": 1, "height": 1}, palette))


if __name__ == "__main__":
    unittest.main()
