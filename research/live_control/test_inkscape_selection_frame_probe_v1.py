import unittest
from pathlib import Path

from research.live_control.inkscape_red_target_planner_v1 import prepare
from research.live_control.inkscape_selection_frame_probe_v1 import (
    load_exact_frame, reconcile_artifact, score_frame)
from research.live_control.inkscape_selection_scorer_v2 import score


ROOT = Path(__file__).resolve().parent
RESULT = ROOT / "results/release-prepared-selection-live-04"
SEMANTIC_FIELDS = ("success", "reason", "expected_target", "observed_support",
                   "edge_delta", "red_coverage_ratio", "zones", "dark_pixels",
                   "target_identity_valid", "selection_handles_visible")


class InkscapeSelectionFrameProbeV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = prepare(RESULT / "001.png", [520, 330, 720, 470])

    def assert_semantically_equal(self, path):
        prior = score(self.plan, path)
        current = score_frame(self.plan, load_exact_frame(path))
        self.assertEqual({key: prior[key] for key in SEMANTIC_FIELDS},
                         {key: current[key] for key in SEMANTIC_FIELDS})
        self.assertTrue(reconcile_artifact(current, path)["matches"])
        return current

    def test_first_feedback_remains_unselected(self):
        self.assertFalse(self.assert_semantically_equal(RESULT / "004.png")["success"])

    def test_first_useful_feedback_remains_selected(self):
        self.assertTrue(self.assert_semantically_equal(RESULT / "005.png")["success"])

    def test_reconciliation_rejects_a_different_exact_frame(self):
        result = score_frame(self.plan, load_exact_frame(RESULT / "004.png"))
        receipt = reconcile_artifact(result, RESULT / "005.png")
        self.assertFalse(receipt["matches"])
        self.assertEqual(receipt["status"], "REJECTED_FRAME_MISMATCH")


if __name__ == "__main__":
    unittest.main()
