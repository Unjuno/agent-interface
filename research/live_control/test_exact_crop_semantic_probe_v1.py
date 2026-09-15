import unittest
from pathlib import Path

from research.live_control.exact_crop_semantic_probe_v1 import (
    reconcile_artifact, score_path)
from research.live_control.semantic_probe_runtime_v2 import SemanticProbeRegistry
from research.live_control.inkscape_selection_frame_probe_v1 import load_exact_frame


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT/"results"
CONTRACT = {"schema": "exact-rgb-crop-semantic-probe-v1",
    "probe_id": "chromium_submission_title", "box": [15, 170, 330, 215],
    "expected_crop_sha256": "879ad35b666f63b1c9a401c359bd563c52170146b3e4ca5c7314448fdfb5784c",
    "success_reason": "submission_title_exactly_visible",
    "grants_input_authority": False}
POSITIVES = [
    RESULTS/"browser-combined-live-01/runtime/011.png",
    RESULTS/"browser-emission-live-01/runtime/016.png",
    RESULTS/"compiled-gui-interface-live-04/2-positive/runtime/020.png",
    RESULTS/"compiled-gui-interface-live-05/2-positive/runtime/021.png",
]
NEGATIVES = [
    RESULTS/"compiled-gui-interface-live-05/2-positive/runtime/012.png",
    RESULTS/"compiled-gui-interface-live-05/1-changed-target/runtime/021.png",
]


class ExactCropSemanticProbeV1Tests(unittest.TestCase):
    def test_four_independent_success_frames_match(self):
        for path in POSITIVES:
            with self.subTest(path=path):
                result = score_path(CONTRACT, path)
                self.assertTrue(result["success"])
                self.assertFalse(result["grants_input_authority"])
                self.assertTrue(reconcile_artifact(result, path)["matches"])

    def test_unsubmitted_and_blank_frames_reject(self):
        for path in NEGATIVES:
            with self.subTest(path=path):
                self.assertFalse(score_path(CONTRACT, path)["success"])

    def test_typed_registry_emits_crop_probe(self):
        registry = SemanticProbeRegistry()
        receipt = registry.register("submit", CONTRACT)
        event = registry.probe("submit", 0, 1, 1, load_exact_frame(POSITIVES[0]))
        self.assertEqual(receipt["contract_schema"], CONTRACT["schema"])
        self.assertTrue(event["score"]["success"])
        self.assertFalse(event["grants_input_authority"])

    def test_registry_still_accepts_selection_contract(self):
        from research.live_control.inkscape_red_target_planner_v1 import prepare
        source = RESULTS/"release-prepared-selection-live-05/001.png"
        selected = RESULTS/"release-prepared-selection-live-05/005.png"
        contract = prepare(source, [520, 330, 720, 470])
        registry = SemanticProbeRegistry(); registry.register("selection", contract)
        event = registry.probe("selection", 0, 1, 1, load_exact_frame(selected))
        self.assertTrue(event["score"]["success"])


if __name__ == "__main__":
    unittest.main()
