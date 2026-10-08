import unittest
from fractions import Fraction

from simulator import analyze, simulate_cell


class GuardProposalRiskTests(unittest.TestCase):
    def test_guard_efficacy_does_not_determine_adaptive_end_to_end_harm(self):
        result = analyze()
        fixed = result["cells"]["fixed_conservative_guard_on"]
        adaptive = result["cells"]["guard_induced_aggressive_guard_on"]
        self.assertEqual(fixed["task_harm_fraction"], Fraction(33, 512))
        self.assertEqual(adaptive["task_harm_fraction"], Fraction(117, 512))
        self.assertEqual(adaptive["task_harm_fraction"] - fixed["task_harm_fraction"], Fraction(21, 128))
        self.assertEqual(adaptive["risky_rejection_rate"], Fraction(3, 4))
        self.assertGreater(adaptive["task_harm_fraction"], fixed["task_harm_fraction"])
        self.assertGreater(adaptive["unfinished_fraction"], fixed["unfinished_fraction"])
        self.assertTrue(result["controls"]["compensation_detected"])

    def test_null_adaptation_is_not_mislabeled_as_compensation(self):
        result = analyze()
        self.assertEqual(result["controls"]["null"]["risky_proposal_fraction"], Fraction(1, 4))
        self.assertFalse(result["controls"]["null"]["compensation_detected"])

    def test_protective_adaptation_is_not_mislabeled_as_compensation(self):
        result = analyze()
        self.assertEqual(result["controls"]["protective"]["risky_proposal_fraction"], Fraction(0, 1))
        self.assertFalse(result["controls"]["protective"]["compensation_detected"])

    def test_every_cell_preserves_all_launched_denominator_and_cost_fields(self):
        result = analyze()
        for cell in result["cells"].values():
            self.assertEqual(cell["all_launched_weight"], Fraction(1, 1))
            self.assertIn("proposal_refusal_fraction", cell)
            self.assertEqual(cell["proposal_refusal_fraction"], cell["expected_refusals_per_launch"] / cell["expected_proposals_per_launch"])
            self.assertIn("per_admitted_action_harm_fraction", cell)
            self.assertIn("task_harm_fraction", cell)
            self.assertIn("unfinished_fraction", cell)
            self.assertIn("expected_proposals_per_launch", cell)
            self.assertIn("expected_retries_per_launch", cell)
            self.assertIn("proposal_work_units_per_launch", cell)

    def test_guard_confusion_matrix_is_explicit_and_normalized(self):
        summary = simulate_cell(risky_probability=Fraction(1, 4), guard_on=True)
        self.assertEqual(summary["guard_true_positive_fraction"], Fraction(3, 4))
        self.assertEqual(summary["guard_false_positive_fraction"], Fraction(1, 4))

    def test_fixture_parameters_drive_the_tree_not_hidden_defaults(self):
        fixture = {
            "max_proposals_per_episode": 2,
            "worlds": [{"true_harmful": True, "weight": "3/4"}, {"true_harmful": False, "weight": "1/4"}],
            "guard_confusion": {"true_positive_reject": "1/2", "false_positive_reject": "1/4"},
            "policies": {"conservative_risky_probability": "1/4", "compensated_risky_probability": "3/4", "protective_risky_probability": "0"},
            "harm_materiality_margin": "1/10",
        }
        changed = analyze(fixture)
        self.assertEqual(changed["cells"]["guard_induced_aggressive_guard_on"]["risky_rejection_rate"], Fraction(1, 2))


if __name__ == "__main__":
    unittest.main()
