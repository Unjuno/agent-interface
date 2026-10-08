import unittest
import base64
import json
from pathlib import Path

import auditor
import build_fixture
import candidate

ROOT = Path(__file__).resolve().parent


class Construction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build_fixture.main()
        cls.design = json.loads((ROOT / "design.json").read_text())
        cls.sources = {frame["frame_id"]: (ROOT / frame["source"]).read_bytes()
                       for frame in cls.design["frames"]}
        cls.frames = {frame["frame_id"]: frame for frame in cls.design["frames"]}
        cls.raw = candidate.run(cls.design, cls.sources)

    def test_fixture_generation_is_deterministic_and_three_patterns_differ(self):
        first = [build_fixture.make_frame(kind) for kind in ("flat_ui", "structured_edges", "seeded_high_entropy")]
        second = [build_fixture.make_frame(kind) for kind in ("flat_ui", "structured_edges", "seeded_high_entropy")]
        self.assertEqual(first, second)
        self.assertEqual(len({__import__("hashlib").sha256(item).hexdigest() for item in first}), 3)

    def test_png_round_trip_preserves_full_frame_pixels(self):
        for kind in ("flat_ui", "structured_edges", "seeded_high_entropy"):
            pixels = build_fixture.make_frame(kind)
            encoded = candidate.encode_png(128, 96, pixels)
            self.assertEqual(encoded[:8], candidate.PNG_SIGNATURE)
            self.assertEqual(auditor.decode_png(encoded), (128, 96, pixels))

    def test_crops_have_exact_rgb_lengths_and_distinct_geometry(self):
        pixels = build_fixture.make_frame("flat_ui")
        for roi in ((0, 0, 16, 16), (16, 16, 48, 40), (32, 24, 96, 72), (60, 0, 68, 96)):
            width, height, crop = candidate.crop_rgb(pixels, 128, list(roi))
            self.assertEqual(len(crop), width * height * 3)
            self.assertEqual(auditor.decode_png(candidate.encode_png(width, height, crop)), (width, height, crop))

    def test_canonical_wire_count_includes_base64_and_all_metadata(self):
        frame = {"frame_id": "fixture", "epoch": 7}
        png = candidate.encode_png(2, 2, bytes(range(12)))
        payload = candidate.make_full(frame, 2, 2, png)
        encoded = candidate.canonical(payload)
        self.assertGreater(len(encoded), len(png))
        self.assertIn(b"frame_id", encoded)
        self.assertIn(b"png_b64", encoded)

    def test_selection_falls_back_on_full_frame_and_refuses_invalid_requests(self):
        errors = auditor.validate(self.raw, self.design, self.sources, self.frames)
        self.assertEqual(errors, [])
        valid = self.raw["rows"][:18]
        full_rois = [row for row in valid if row["request"]["region_id"] == "full_frame"]
        self.assertEqual(len(full_rois), 3)
        self.assertTrue(all(row["selected_kind"] == "FULL_FRAME" for row in full_rois))
        invalid = self.raw["rows"][18:]
        self.assertEqual(len(invalid), 5)
        self.assertTrue(all(row["focused_payload"] is None for row in invalid))

    def test_six_mutation_classes_are_rejected(self):
        cases = []
        bad_crc = json.loads(json.dumps(self.raw))
        png = bytearray(base64.b64decode(bad_crc["rows"][0]["focused_payload"]["png_b64"]))
        png[-5] ^= 1
        bad_crc["rows"][0]["focused_payload"]["png_b64"] = base64.b64encode(png).decode("ascii")
        cases.append(bad_crc)
        bad_region = json.loads(json.dumps(self.raw))
        bad_region["rows"][0]["focused_payload"]["region_id"] = "other"
        cases.append(bad_region)
        bad_stale = json.loads(json.dumps(self.raw))
        bad_stale["rows"][18]["selected_kind"] = "FOCUSED_REGION"
        cases.append(bad_stale)
        bad_bounds = json.loads(json.dumps(self.raw))
        bad_bounds["rows"][22]["selected_kind"] = "FOCUSED_REGION"
        cases.append(bad_bounds)
        bad_no_gain = json.loads(json.dumps(self.raw))
        bad_no_gain["rows"][4]["selected_kind"] = "FOCUSED_REGION"
        cases.append(bad_no_gain)
        bad_size = json.loads(json.dumps(self.raw))
        bad_size["rows"][0]["selected_bytes"] = 1
        cases.append(bad_size)
        self.assertEqual(len(cases), 6)
        self.assertTrue(all(auditor.validate(raw, self.design, self.sources, self.frames) for raw in cases))


if __name__ == "__main__":
    unittest.main()
