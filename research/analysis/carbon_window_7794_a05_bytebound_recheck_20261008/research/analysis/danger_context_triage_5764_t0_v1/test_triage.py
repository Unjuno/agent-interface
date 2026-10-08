import unittest

from audit import audit_selection
from runner import rank_optional


class TriageContractTests(unittest.TestCase):
    def test_mandatory_events_are_outside_the_optional_budget(self):
        rows = [
            {"event_id": "a", "mandatory": True, "novelty": 0, "effect": 0,
             "severity": 3, "actionable": True, "failure": True},
            {"event_id": "b", "mandatory": False, "novelty": 1, "effect": 0,
             "severity": 1, "actionable": False, "failure": False},
            {"event_id": "c", "mandatory": False, "novelty": 0, "effect": 1,
             "severity": 1, "actionable": True, "failure": True},
        ]
        chosen = rank_optional(rows, "DUAL", budget=1)
        result = audit_selection(rows, chosen, budget=1)
        self.assertEqual(result["mandatory_selected"], ["a"])
        self.assertEqual(result["optional_selected"], ["c"])
        self.assertEqual(result["optional_budget_used"], 1)

    def test_unknown_effect_is_not_treated_as_negative_and_ties_are_stable(self):
        rows = [
            {"event_id": "z", "mandatory": False, "novelty": 1, "effect": None,
             "severity": 1, "actionable": False, "truth": 1},
            {"event_id": "a", "mandatory": False, "novelty": 1, "effect": None,
             "severity": 1, "actionable": False, "truth": 0},
        ]
        self.assertEqual(rank_optional(rows, "DUAL", 1), ["a"])

    def test_effect_linkage_does_not_leak_to_a_temporal_neighbor(self):
        rows = [
            {"event_id": "linked", "action_id": "act-1", "effect_action_id": "act-1",
             "time": 10, "mandatory": False, "novelty": 0, "effect": 1,
             "severity": 1, "actionable": True, "truth": 1},
            {"event_id": "neighbor", "action_id": "act-2", "effect_action_id": "act-1",
             "time": 10, "mandatory": False, "novelty": 1, "effect": 0,
             "severity": 1, "actionable": False, "truth": 0},
        ]
        chosen = rank_optional(rows, "DUAL", 1)
        self.assertEqual(chosen, ["linked"])

    def test_severity_only_baseline_is_available_as_a_distinct_comparator(self):
        rows = [
            {"event_id": "low-harm", "mandatory": False, "novelty": 0, "effect": 1,
             "severity": 1, "actionable": True, "truth": 1},
            {"event_id": "high-benign", "mandatory": False, "novelty": 1, "effect": 0,
             "severity": 3, "actionable": False, "failure": False},
        ]
        self.assertEqual(rank_optional(rows, "5435_SEVERITY_ONLY", 1), ["high-benign"])

    def test_5435_identity_batch_keeps_first_low_score_entity_and_mandatory_rows(self):
        rows = [
            {"event_id": "hard", "entity_id": "h", "signature": "safety",
             "mandatory": True, "novelty": 0, "effect": 0, "severity": 3,
             "actionable": True, "score": 0.99, "failure": True},
            {"event_id": "first", "entity_id": "x", "signature": "refresh",
             "mandatory": False, "novelty": 0, "effect": 0, "severity": 1,
             "actionable": True, "score": 0.05, "failure": True},
            {"event_id": "copy", "entity_id": "x", "signature": "refresh",
             "mandatory": False, "novelty": 1, "effect": 0, "severity": 1,
             "actionable": True, "score": 0.05, "failure": True},
            {"event_id": "other", "entity_id": "y", "signature": "refresh",
             "mandatory": False, "novelty": 1, "effect": 0, "severity": 1,
             "actionable": False, "score": 0.05, "failure": False},
        ]
        self.assertEqual(rank_optional(rows, "5435_SAFE_IDENTITY_BATCH", 2), ["first", "other"])

    def test_outcome_audit_uses_full_population_denominator(self):
        rows = [
            {"event_id": "fail", "mandatory": False, "novelty": 0, "effect": 1,
             "severity": 1, "actionable": True, "failure": True},
            {"event_id": "benign", "mandatory": False, "novelty": 1, "effect": 0,
             "severity": 1, "actionable": False, "failure": False},
        ]
        result = audit_selection(rows, ["fail"], budget=1)
        self.assertEqual(result["population_size"], 2)
        self.assertEqual(result["optional_failure_total"], 1)
        self.assertEqual(result["optional_failures_found"], 1)
        self.assertEqual(result["optional_failures_missed"], 0)


if __name__ == "__main__":
    unittest.main()
