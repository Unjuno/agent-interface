import unittest
from pathlib import Path

from research.live_control.inkscape_red_target_planner_v1 import prepare
from research.live_control.inkscape_selection_frame_probe_v1 import load_exact_frame
from research.live_control.semantic_probe_runtime_v1 import SemanticProbeRegistry


ROOT = Path(__file__).resolve().parent
RESULT = ROOT / "results/release-prepared-selection-live-04"


class SemanticProbeBackendV1Tests(unittest.TestCase):
    def setUp(self):
        self.registry = SemanticProbeRegistry()
        self.plan = prepare(RESULT/"001.png", [520, 330, 720, 470])

    def test_registration_is_no_authority_and_copied(self):
        receipt = self.registry.register("select", self.plan)
        self.plan["target"]["center"][0] = -1
        self.assertEqual(receipt["status"], "REGISTERED_NO_AUTHORITY")
        self.assertFalse(receipt["grants_input_authority"])
        self.assertEqual(self.registry._plans["select"]["target"]["center"],
                         [619, 390])

    def test_probe_preserves_false_then_true_semantics(self):
        self.registry.register("select", self.plan)
        first = self.registry.probe("select", 0, 4, 1,
                                    load_exact_frame(RESULT/"004.png"))
        useful = self.registry.probe("select", 1, 5, 2,
                                     load_exact_frame(RESULT/"005.png"))
        self.assertFalse(first["score"]["success"])
        self.assertTrue(useful["score"]["success"])
        self.assertEqual(first["state"], "PROVISIONAL_AWAITING_EXACT_ARTIFACT")
        self.assertFalse(first["grants_input_authority"])

    def test_unregistered_action_has_no_probe(self):
        self.assertIsNone(self.registry.probe(
            "other", 0, 1, 1, load_exact_frame(RESULT/"004.png")))

    def test_duplicate_registration_is_rejected(self):
        self.registry.register("select", self.plan)
        with self.assertRaises(ValueError):
            self.registry.register("select", self.plan)


if __name__ == "__main__":
    unittest.main()
