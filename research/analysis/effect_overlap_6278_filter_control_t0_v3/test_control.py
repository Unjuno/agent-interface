import copy
import json
import unittest

import audit
import control


class SameGraphQualificationFilterTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open("FIXTURE.json") as stream:
            cls.fixture = json.load(stream)
        cls.raw = control.run(cls.fixture)

    def test_unfiltered_advertised_edge_has_planted_positive_discriminator(self):
        totals = self.raw["arms"]["declared_graph"]["aggregate_scores"]
        self.assertEqual(totals, {"partial_overlap": 9, "disjoint_specialist": 8})

    def test_same_graph_exact_effect_filter_removes_advantage(self):
        totals = self.raw["arms"]["exact_effect_qualified_graph"]["aggregate_scores"]
        self.assertEqual(totals, {"partial_overlap": 8, "disjoint_specialist": 8})
        self.assertTrue(self.raw["diagnostic"]["apparent_advantage_disappears"])

    def test_filter_only_changes_edge_truth_eligibility(self):
        self.assertEqual(self.raw["only_changed_variable"], "exact_effect_edge_eligibility")
        self.assertEqual(self.raw["edge"]["declared_truth"], "partial")
        self.assertTrue(self.raw["edge"]["grant_present"])

    def test_both_arms_hold_budget_capacity_and_task_denominator(self):
        self.assertEqual(self.raw["same_budget"], self.fixture["budget"])
        self.assertEqual(self.raw["same_capacity"], self.fixture["portfolio_capacity"])
        for arm in self.raw["arms"].values():
            for topology in ("partial_overlap", "disjoint_specialist"):
                for scenario in self.fixture["scenarios"]:
                    rows = arm[topology][scenario["id"]]["rows"]
                    self.assertEqual({row["task"] for row in rows}, {task["id"] for task in self.fixture["tasks"]})

    def test_independent_exhaustive_reconstruction_agrees(self):
        errors, expected = audit.validate(self.raw, self.fixture)
        self.assertEqual(errors, [])
        self.assertEqual(self.raw, expected)

    def test_mutation_advantage_after_filter_rejected(self):
        mutant = copy.deepcopy(self.raw)
        mutant["arms"]["exact_effect_qualified_graph"]["aggregate_scores"]["partial_overlap"] += 1
        mutant["diagnostic"]["apparent_advantage_disappears"] = False
        errors, _ = audit.validate(mutant, self.fixture)
        self.assertTrue(errors)

    def test_mutation_of_disputed_edge_to_exact_rejected(self):
        mutant = copy.deepcopy(self.raw)
        mutant["edge"]["declared_truth"] = "exact"
        errors, _ = audit.validate(mutant, self.fixture)
        self.assertTrue(errors)

    def test_hiding_or_duplicating_offered_task_is_rejected(self):
        for mutate in ("hide", "duplicate"):
            mutant = copy.deepcopy(self.raw)
            rowset = mutant["arms"]["exact_effect_qualified_graph"]["partial_overlap"]["left_dependency_loss"]["rows"]
            if mutate == "hide":
                rowset.pop()
            else:
                rowset[-1] = copy.deepcopy(rowset[0])
            errors, _ = audit.validate(mutant, self.fixture)
            self.assertTrue(errors)


if __name__ == "__main__":
    unittest.main()
