#!/usr/bin/env python3
import hashlib
import unittest

from auditor import decode_png
from candidate import bounds_for, canonical, pixel_digest


class PngPayloadConstructionTest(unittest.TestCase):
    def test_archived_frame_pixel_digests_match_frozen_design(self):
        import json
        from pathlib import Path
        from PIL import Image
        import candidate
        design = json.loads((Path(candidate.__file__).parent / "design.json").read_text())
        repo = Path(candidate.__file__).resolve().parents[3]
        self.assertEqual(len(design["frames"]), 21)
        all_cases = []
        for frame in design["frames"]:
            with Image.open(repo / frame["source_png_path"]) as image:
                image.load()
                self.assertEqual(image.mode, "RGB")
                self.assertEqual(image.size, (1280, 800))
                pixels = image.tobytes()
                self.assertEqual(pixel_digest(*image.size, image.mode, pixels),
                                 frame["source_pixel_sha256"])
                self.assertEqual(decode_png((repo / frame["source_png_path"]).read_bytes()),
                                 (1280, 800, pixels))
            all_cases.extend(candidate.expected_cases(frame, 1280, 800, design))
        self.assertEqual(len(all_cases), design["expected_case_count"])
        self.assertEqual(len({item["case_id"] for item in all_cases}), 441)

    def test_frozen_roi_grid_has_unique_in_bounds_requests(self):
        from candidate import expected_cases
        frame = {"frame_id": "fixture", "epoch": 1}
        design = {"area_sizes_pixels": {"small": [320, 200], "medium": [640, 400]},
                  "placements": ["center", "top_left", "top_right", "bottom_left", "bottom_right"]}
        cases = expected_cases(frame, 1280, 800, design)
        self.assertEqual(len(cases), 11)
        bounds = [tuple(case["request"]["bounds"]) for case in cases]
        self.assertEqual(len(bounds), len(set(bounds)))
        for x0, y0, x1, y1 in bounds:
            self.assertTrue(0 <= x0 < x1 <= 1280)
            self.assertTrue(0 <= y0 < y1 <= 800)

    def test_pillow_output_reconstructs_and_mutation_is_rejected(self):
        from candidate import Frame, encode_artifact
        pixels = bytes((i * 19) % 256 for i in range(8 * 6 * 3))
        with __import__("tempfile").TemporaryDirectory() as temporary:
            from pathlib import Path
            output = Path(temporary) / "image.png"
            png = encode_artifact(pixels, 8, 6, "RGB", output)
            self.assertEqual(decode_png(png), (8, 6, pixels))
            broken = bytearray(png)
            broken[-5] ^= 1
            with self.assertRaises(ValueError):
                decode_png(bytes(broken))

    def test_canonical_payload_size_counts_base64_and_metadata(self):
        import base64
        payload = {"kind": "FULL_FRAME", "png_b64": base64.b64encode(b"PNG").decode("ascii")}
        self.assertEqual(len(canonical(payload)), len(b'{"kind":"FULL_FRAME","png_b64":"UE5H"}'))

    def test_runtime_encoder_source_imports(self):
        import candidate
        self.assertTrue(callable(candidate.ImageArtifactSink))
        self.assertEqual(candidate.PILLOW_VERSION, "12.3.0")

    def test_runner_persists_exact_child_exit_code(self):
        import sys
        import tempfile
        from pathlib import Path
        from formal_runner import capture_process
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            stdout, stderr = root / "out", root / "err"
            code, error = capture_process(
                [sys.executable, "-c", "import sys; print('captured'); sys.exit(7)"],
                root, stdout, stderr)
            self.assertEqual(code, 7)
            self.assertIsNone(error)
            self.assertEqual(stdout.read_text().strip(), "captured")
            self.assertEqual(stderr.read_bytes(), b"")


if __name__ == "__main__":
    unittest.main()
