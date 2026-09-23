import unittest
from pathlib import Path

import numpy as np

from research.live_control.inkscape_selection_frame_probe_v1 import ExactFrame, load_exact_frame
from research.live_control.semantic_probe_runtime_v3 import SemanticProbeRegistry
from research.live_control.target_relative_crop_semantic_probe_v1 import score_frame


ROOT = Path(__file__).resolve().parent
IMAGE = ROOT/"results/chromium-semantic-probe-transfer-live-02/012.png"
SOURCE = {"focus": 6291459, "surface": 6291459, "geometry": [10, 10, 1050, 780]}
CONTRACT = {"schema": "target-relative-rgb-crop-semantic-probe-v1",
    "probe_id": "submission", "target_reference": "submission_heading",
    "coordinate_frame": "window_content", "source_surface": 6291459,
    "source_geometry": [10, 10, 1050, 780], "box_in_frame": [5, 160, 320, 205],
    "expected_crop_sha256": "879ad35b666f63b1c9a401c359bd563c52170146b3e4ca5c7314448fdfb5784c",
    "success_reason": "submission_title_exactly_visible",
    "allowed_transformations": ["window_translation"], "grants_input_authority": False}


class TargetRelativeCropTests(unittest.TestCase):
    def test_source_geometry_matches(self):
        result = score_frame(CONTRACT, load_exact_frame(IMAGE), SOURCE)
        self.assertTrue(result["success"])
        self.assertEqual(result["resolved_box"], [15, 170, 330, 215])
        self.assertEqual(result["binding_status"], "CURRENT_EXACT")

    def test_translation_tracks_same_surface(self):
        frame = load_exact_frame(IMAGE)
        source = np.frombuffer(frame.pixels, np.uint8).reshape(frame.height, frame.width, 3)
        shifted = np.zeros_like(source); shifted[28:, 21:] = source[:-28, :-21]
        moved = ExactFrame(frame.width, frame.height, frame.mode, shifted.tobytes())
        binding = {"focus": 6291459, "surface": 6291459,
                   "geometry": [31, 38, 1050, 780]}
        result = score_frame(CONTRACT, moved, binding)
        self.assertTrue(result["success"])
        self.assertEqual(result["translation"], [21, 28])
        self.assertEqual(result["resolved_box"], [36, 198, 351, 243])

    def test_resize_and_surface_change_refuse(self):
        frame = load_exact_frame(IMAGE)
        resized = {**SOURCE, "geometry": [10, 10, 930, 780]}
        other = {**SOURCE, "surface": 7, "focus": 7}
        self.assertEqual(score_frame(CONTRACT, frame, resized)["reason"],
                         "surface_size_changed")
        self.assertEqual(score_frame(CONTRACT, frame, other)["reason"], "surface_changed")

    def test_registry_copies_and_passes_binding(self):
        contract = {**CONTRACT, "source_geometry": list(CONTRACT["source_geometry"])}
        registry = SemanticProbeRegistry(); receipt = registry.register("submit", contract)
        contract["source_geometry"][0] = -1
        event = registry.probe("submit", 0, 1, 1, load_exact_frame(IMAGE), SOURCE)
        self.assertEqual(receipt["contract_schema"], CONTRACT["schema"])
        self.assertTrue(event["score"]["success"])
        self.assertFalse(event["grants_input_authority"])


if __name__ == "__main__": unittest.main()
