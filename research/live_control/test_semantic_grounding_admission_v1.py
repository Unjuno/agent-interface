import unittest
from pathlib import Path

from research.live_control.semantic_grounding_admission_v1 import admit
from research.live_control.semantic_repair_model_v2 import classify


ROOT = Path(__file__).resolve().parent


class SemanticGroundingAdmissionTests(unittest.TestCase):
    def test_completed_grounding_is_eligible_but_grants_no_input(self):
        outcome = classify(ROOT / "results/compiled-gui-interface-live-05/2-positive/grounding-model")
        receipt = admit(outcome)
        self.assertEqual(receipt["status"], "TASK_MUTATION_ELIGIBLE")
        self.assertTrue(receipt["task_mutation_eligible"])
        self.assertIsNotNone(receipt["grounding_reference"])
        self.assertFalse(receipt["grants_input_authority"])
        self.assertTrue(receipt["ordinary_executor_admission_required"])

    def test_capacity_outcome_defers_without_reference_or_authority(self):
        outcome = classify(ROOT / "results/matched-semantic-repair-live-01/arm-01-local/initial-model")
        receipt = admit(outcome)
        self.assertEqual(receipt["status"], "TASK_DEFERRED")
        self.assertFalse(receipt["task_mutation_eligible"])
        self.assertIsNone(receipt["grounding_reference"])
        self.assertIsNone(receipt["model_call_id"])
        self.assertFalse(receipt["grants_semantic_authority"])
        self.assertFalse(receipt["grants_input_authority"])

    def test_authority_escalation_is_rejected(self):
        outcome = classify(ROOT / "results/matched-semantic-repair-live-01/arm-01-local/initial-model")
        outcome["grants_input_authority"] = True
        with self.assertRaisesRegex(ValueError, "grant no authority"):
            admit(outcome)


if __name__ == "__main__":
    unittest.main()
