import unittest
from pathlib import Path

from research.live_control.inkscape_red_target_planner_v1 import prepare
from research.live_control.inkscape_selection_scorer_v1 import score


ROOT = Path(__file__).resolve().parent
UNSELECTED = ROOT / "results/release-planner-overlap-live-01/002.png"
SELECTED = ROOT / "results/selection-readiness-ink-01/runtime/014.png"


class InkscapeSelectionScorerTests(unittest.TestCase):
    def test_retained_unselected_image_refuses(self):
        plan = prepare(UNSELECTED, [520, 330, 720, 470])
        result = score(plan, UNSELECTED)
        self.assertFalse(result["success"])
        self.assertEqual(result["dark_pixels"],
                         {"left": 0, "right": 0, "top": 0, "bottom": 0})

    def test_independent_retained_selected_image_passes(self):
        plan = prepare(SELECTED, [560, 330, 760, 470])
        result = score(plan, SELECTED)
        self.assertTrue(result["success"])
        self.assertEqual(result["dark_pixels"],
                         {"left": 197, "right": 197, "top": 67, "bottom": 67})
        self.assertFalse(result["grants_input_authority"])


if __name__ == "__main__": unittest.main()
