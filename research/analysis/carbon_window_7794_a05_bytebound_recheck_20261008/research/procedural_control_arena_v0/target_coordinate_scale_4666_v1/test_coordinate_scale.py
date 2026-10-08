from __future__ import annotations

import base64
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from audit import _call_errors, _in_bounds, expected_scene
from renderer import render_base
from runner import MODEL, MODEL_DIGEST, prompt_for, source_pixel_proposal


class CoordinateScaleTest(unittest.TestCase):
    def test_raw_stimulus_is_deterministic(self):
        a, ta = render_base(8866621, 0.35)
        b, tb = render_base(8866621, 0.35)
        self.assertEqual((a, ta), (b, tb))
        self.assertEqual(a[:8], b"\x89PNG\r\n\x1a\n")

    def test_arms_share_the_same_source_frame_and_target(self):
        _, truth = render_base(8866622, 0.35)
        self.assertEqual(truth["instruction"], "TARGET: click the " + truth["target"]["color"] + " " + truth["target"]["shape"] + ".")
        self.assertEqual((truth["seed"], truth["difficulty"]), (8866622, 0.35))

    def test_prompts_change_coordinate_units_not_target_wording(self):
        pixel = prompt_for("TARGET: click the blue square.", "PIXEL")
        norm = prompt_for("TARGET: click the blue square.", "NORM01")
        self.assertIn("blue square", pixel)
        self.assertIn("blue square", norm)
        self.assertIn("pixel coordinates", pixel)
        self.assertIn("normalized source-image coordinates", norm)
        for forbidden in ("8866621", "target_id", "prepared_id", "seed"):
            self.assertNotIn(forbidden, pixel + norm)

    def test_posthoc_mapping_uses_pixel_center_ranges(self):
        proposal = {"color": "blue", "shape": "square", "x": 0.5, "y": 1.0}
        mapped = source_pixel_proposal(proposal, "NORM01")
        self.assertEqual(mapped, {"color": "blue", "shape": "square", "x": 319.5, "y": 479.0})
        self.assertEqual(source_pixel_proposal(proposal, "PIXEL"), proposal)

    def test_out_of_range_values_are_not_clipped_or_counted_in_bounds(self):
        proposal = {"color": "blue", "shape": "square", "x": 1.2, "y": -0.1}
        self.assertEqual(source_pixel_proposal(proposal, "NORM01")["x"], 1.2 * 639)
        self.assertFalse(_in_bounds(proposal, "NORM01"))

    def test_expected_scene_scores_engine_target(self):
        session, truth = expected_scene(8866623)
        target_id = session.stage.payload["target_id"]
        target = session._object_by_id(target_id)
        self.assertEqual((target.color, target.shape), (truth["target"]["color"], truth["target"]["shape"]))
        self.assertIs(session._object_at(target.x, target.y), target)

    def test_auditor_accepts_exact_source_bound_raw_response(self):
        image = b"test-image-bytes"
        prompt = prompt_for("TARGET: click the blue square.", "PIXEL")
        proposal = {"color": "blue", "shape": "square", "x": 10, "y": 20}
        response_text = json.dumps(proposal)
        body = {"model": MODEL, "prompt": prompt, "images": [base64.b64encode(image).decode()],
                "stream": False, "format": {"type": "object", "properties": {
                    "color": {"type": "string"}, "shape": {"type": "string"},
                    "x": {"type": "number"}, "y": {"type": "number"}},
                    "required": ["color", "shape", "x", "y"]},
                "options": {"temperature": 0, "seed": 424242, "num_predict": 128}}
        record = {"schema": "arena-v0-coordinate-scale-call-v1", "difficulty": 0.35,
                  "seed": 8866621, "arm": "PIXEL", "order": 0, "model": MODEL,
                  "model_digest": MODEL_DIGEST, "prompt": prompt, "image_path": "raw.png",
                  "image_sha256": hashlib.sha256(image).hexdigest(),
                  "request_sha256": hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
                  "request": body, "response": {"model": MODEL, "response": response_text},
                  "proposal": proposal, "source_pixel_proposal": proposal, "wall_seconds": 1.0}
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "raw.png").write_bytes(image)
            self.assertEqual(_call_errors(record, root, 8866621, "PIXEL", 0, prompt), [])

    def test_auditor_rejects_raw_response_model_mismatch(self):
        image = b"test-image-bytes"
        prompt = prompt_for("TARGET: click the blue square.", "PIXEL")
        proposal = {"color": "blue", "shape": "square", "x": 10, "y": 20}
        body = {"model": MODEL, "prompt": prompt, "images": [base64.b64encode(image).decode()],
                "stream": False, "format": {"type": "object"},
                "options": {"temperature": 0, "seed": 424242, "num_predict": 128}}
        record = {"schema": "arena-v0-coordinate-scale-call-v1", "difficulty": 0.35,
                  "seed": 8866621, "arm": "PIXEL", "order": 0, "model": MODEL,
                  "model_digest": MODEL_DIGEST, "prompt": prompt, "image_path": "raw.png",
                  "image_sha256": hashlib.sha256(image).hexdigest(),
                  "request_sha256": hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
                  "request": body, "response": {"model": "wrong", "response": json.dumps(proposal)},
                  "proposal": proposal, "source_pixel_proposal": proposal, "wall_seconds": 1.0}
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "raw.png").write_bytes(image)
            errors = _call_errors(record, root, 8866621, "PIXEL", 0, prompt)
        self.assertIn("raw_response_model", errors)


if __name__ == "__main__":
    unittest.main(verbosity=2)
