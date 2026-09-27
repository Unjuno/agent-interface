from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from audit import _call_errors, expected_scene, median_center_error
from engine import BenchmarkSession, EpisodeSpec, StageSpec, generate_episode
from renderer import render_base, render_pair
from runner import prompt_for


class TargetLocalizationEncodingTest(unittest.TestCase):
    def test_even_sample_median_averages_the_two_middle_values(self):
        self.assertEqual(median_center_error(list(range(1, 13))), 6.5)

    def test_rendering_is_deterministic_and_arms_share_truth(self):
        raw1, grid1, truth1 = render_pair(8866601, 0.35)
        raw2, grid2, truth2 = render_pair(8866601, 0.35)
        self.assertEqual((raw1, grid1, truth1), (raw2, grid2, truth2))
        self.assertNotEqual(hashlib.sha256(raw1).digest(), hashlib.sha256(grid1).digest())
        self.assertEqual(raw1[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(truth1["seed"], 8866601)

    def test_raw_pair_arm_matches_raw_renderer(self):
        raw, _, _ = render_pair(8866602, 0.35)
        raw_again, _ = render_base(8866602, 0.35)
        self.assertEqual(raw, raw_again)

    def test_grid_overlay_is_drawn_over_scene_geometry(self):
        import struct
        import zlib
        def decode(png):
            offset = 8
            compressed = bytearray()
            while offset < len(png):
                size = struct.unpack(">I", png[offset:offset + 4])[0]
                kind = png[offset + 4:offset + 8]
                if kind == b"IDAT":
                    compressed.extend(png[offset + 8:offset + 8 + size])
                offset += 12 + size
            return zlib.decompress(compressed)

        found_overlay_pixel = False
        for seed in range(8866601, 8866613):
            raw, grid, _ = render_pair(seed, 0.35)
            raw_pixels, grid_pixels = decode(raw), decode(grid)
            for y in range(80, 460):
                for x in range(0, 640, 80):
                    pixel = y * (640 * 3 + 1) + 1 + x * 3
                    base = tuple(raw_pixels[pixel:pixel + 3])
                    treatment = tuple(grid_pixels[pixel:pixel + 3])
                    if base not in {(17, 19, 24), (66, 72, 84)} and treatment == (49, 54, 63):
                        found_overlay_pixel = True
                        break
                if found_overlay_pixel:
                    break
            if found_overlay_pixel:
                break
        self.assertTrue(found_overlay_pixel, "no foreground grid pixel crossed an object")

    def test_grid_axis_labels_use_legible_scaled_glyphs(self):
        import struct
        import zlib
        _, grid, _ = render_pair(8866601, 0.35)
        offset = 8
        compressed = bytearray()
        while offset < len(grid):
            size = struct.unpack(">I", grid[offset:offset + 4])[0]
            if grid[offset + 4:offset + 8] == b"IDAT":
                compressed.extend(grid[offset + 8:offset + 8 + size])
            offset += 12 + size
        pixels = zlib.decompress(compressed)
        x, y = 2, 99  # first lit pixel of the 2x-scaled "0" at source origin
        offset = y * (640 * 3 + 1) + 1 + x * 3
        self.assertEqual(tuple(pixels[offset:offset + 3]), (120, 128, 141))

    def test_expected_scene_uses_only_target_stage(self):
        session, truth = expected_scene(8866603)
        self.assertEqual(len(session.spec.stages), 1)
        self.assertEqual(session.stage.kind, "target")
        target_id = session.stage.payload["target_id"]
        target = session._object_by_id(target_id)
        self.assertEqual((target.color, target.shape), (truth["target"]["color"], truth["target"]["shape"]))

    def test_model_prompt_has_task_and_coordinate_contract_only(self):
        prompt = prompt_for("TARGET: click the orange diamond.")
        self.assertIn("orange diamond", prompt)
        self.assertIn("source-image pixel coordinates", prompt.lower())
        for forbidden in ("8866600", "8866601", "target_id", "prepared_id", "seed"):
            self.assertNotIn(forbidden, prompt)

    def test_model_request_binding_rejects_missing_or_corrupt_image(self):
        from audit import MODEL, MODEL_DIGEST
        record = {"seed": 8866601, "arm": "RAW", "order": 0, "model": MODEL, "model_digest": MODEL_DIGEST,
                  "prompt": "p", "image_path": "raw.png", "image_sha256": "bad", "request_sha256": "bad",
                  "request": {"model": MODEL, "prompt": "p", "images": [], "options": {"temperature": 0, "seed": 424242, "num_predict": 128}},
                  "proposal": {"color": "red", "shape": "circle", "x": 1.0, "y": 2.0}}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "raw.png"
            path.write_bytes(b"png")
            errors = _call_errors(record, Path(directory), 8866601, "RAW", 0, "p")
        self.assertIn("image_hash", errors)
        self.assertIn("request_image_count", errors)

    def test_non_base64_request_is_reported_not_crash(self):
        from audit import MODEL, MODEL_DIGEST
        record = {"seed": 8866601, "arm": "RAW", "order": 0, "model": MODEL, "model_digest": MODEL_DIGEST,
                  "prompt": "p", "image_path": "raw.png", "image_sha256": "bad", "request_sha256": "bad",
                  "request": {"model": MODEL, "prompt": "p", "images": ["%%%"], "options": {"temperature": 0, "seed": 424242, "num_predict": 128}},
                  "proposal": {"color": "red", "shape": "circle", "x": 1.0, "y": 2.0}}
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / "raw.png").write_bytes(b"png")
            errors = _call_errors(record, Path(directory), 8866601, "RAW", 0, "p")
        self.assertIn("request_image_encoding", errors)

    def test_raw_response_model_mismatch_is_rejected(self):
        from audit import MODEL, MODEL_DIGEST
        image = b"png"
        proposal = {"color": "red", "shape": "circle", "x": 1.0, "y": 2.0}
        record = {"schema": "arena-v0-grid-localization-call-v1", "difficulty": 0.35,
                  "seed": 8866601, "arm": "RAW", "order": 0, "model": MODEL,
                  "model_digest": MODEL_DIGEST, "prompt": "p", "image_path": "raw.png",
                  "image_sha256": hashlib.sha256(image).hexdigest(), "request_sha256": "bad",
                  "request": {"model": MODEL, "prompt": "p", "images": ["cG5n"], "stream": False,
                              "format": {"type": "object"},
                              "options": {"temperature": 0, "seed": 424242, "num_predict": 128}},
                  "proposal": proposal,
                  "response": {"model": "other", "response": '{"color":"red","shape":"circle","x":1,"y":2}'},
                  "wall_seconds": 1.0}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "raw.png").write_bytes(image)
            errors = _call_errors(record, root, 8866601, "RAW", 0, "p")
        self.assertIn("raw_response_model_identity", errors)

    def test_engine_hit_gate_is_used_for_proposal_scoring(self):
        episode = generate_episode(8866604, 0.35)
        stage = next(item for item in episode.stages if item.kind == "target")
        session = BenchmarkSession(EpisodeSpec(episode.schema, episode.seed, episode.difficulty, (StageSpec("target", stage.payload),)))
        target = session._object_by_id(stage.payload["target_id"])
        hit = session._object_at(target.x, target.y)
        self.assertIsNotNone(hit)
        self.assertEqual(hit.object_id, target.object_id)


if __name__ == "__main__":
    unittest.main(verbosity=2)
