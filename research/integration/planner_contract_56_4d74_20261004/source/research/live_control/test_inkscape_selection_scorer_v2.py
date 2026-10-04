import unittest
from pathlib import Path

from research.live_control.inkscape_red_target_planner_v1 import prepare
from research.live_control.inkscape_selection_scorer_v2 import score


ROOT = Path(__file__).resolve().parent


class InkscapeSelectionScorerV2Tests(unittest.TestCase):
    def test_unselected_target_has_identity_but_no_handles(self):
        image = ROOT / "results/release-planner-overlap-live-01/002.png"
        result = score(prepare(image, [520, 330, 720, 470]), image)
        self.assertTrue(result["target_identity_valid"])
        self.assertFalse(result["selection_handles_visible"])
        self.assertFalse(result["success"])

    def test_v1_failed_rectangle_tool_overlay_is_valid_selection(self):
        source = ROOT / "results/release-prepared-selection-live-01/001.png"
        selected = ROOT / "results/release-prepared-selection-live-01/004.png"
        result = score(prepare(source, [520, 330, 720, 470]), selected)
        self.assertTrue(result["success"])
        self.assertEqual(result["edge_delta"], [1, 1, 0, 0])
        self.assertGreater(result["red_coverage_ratio"], .8)
        self.assertEqual(result["dark_pixels"],
                         {"left": 23, "right": 46, "top": 21, "bottom": 12})

    def test_independent_selector_overlay_also_passes(self):
        selected = ROOT / "results/selection-readiness-ink-01/runtime/014.png"
        result = score(prepare(selected, [560, 330, 760, 470]), selected)
        self.assertTrue(result["success"])
        self.assertEqual(result["dark_pixels"],
                         {"left": 197, "right": 197, "top": 67, "bottom": 67})


if __name__ == "__main__": unittest.main()
