import unittest
from pathlib import Path

from research.live_control.matched_semantic_repair_live_v2 import noncompletion_summary
from research.live_control.semantic_grounding_admission_v1 import admit
from research.live_control.semantic_repair_model_v2 import classify


ROOT = Path(__file__).resolve().parent


class MatchedSemanticRepairV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        outcome = classify(ROOT / "results/matched-semantic-repair-live-01/arm-01-local/initial-model")
        cls.admission = admit(outcome)

    def arm(self, stage):
        value = {"status": "TASK_DEFERRED", "passed": False,
                 "comparison_eligible": False, "retry_count": 0}
        value[stage] = self.admission
        return value

    def test_initial_capacity_stops_before_comparison(self):
        result = noncompletion_summary(self.arm("initial_admission"))
        self.assertEqual(result["status"], "DEFERRED")
        self.assertEqual(result["stage"], "initial_grounding")
        self.assertFalse(result["comparison_eligible"])
        self.assertFalse(result["grants_input_authority"])

    def test_later_capacity_is_not_counted_as_sample(self):
        result = noncompletion_summary(self.arm("reacquisition_admission"))
        self.assertEqual(result["stage"], "reacquisition")
        self.assertFalse(result["comparison_eligible"])
        self.assertFalse(result["grants_semantic_authority"])

    def test_noncompleted_arm_cannot_claim_comparison_eligibility(self):
        arm = self.arm("initial_admission")
        arm["comparison_eligible"] = True
        with self.assertRaisesRegex(ValueError, "typed noncompletion"):
            noncompletion_summary(arm)


if __name__ == "__main__":
    unittest.main()
