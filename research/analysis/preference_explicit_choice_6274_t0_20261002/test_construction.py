import copy
import json
import unittest
from pathlib import Path

import candidate
import audit


FIXTURE = json.loads((Path(__file__).parent / "fixture.json").read_text(encoding="utf-8"))


class PreferenceChoiceConstruction(unittest.TestCase):
    def test_weak_order_counts(self):
        self.assertEqual(len(list(candidate.ordered_partitions(["a", "b"]))), 3)
        self.assertEqual(len(list(candidate.ordered_partitions(["a", "b", "c"]))), 13)
        self.assertEqual(len(list(candidate.ordered_partitions(["a", "b", "c", "d"]))), 75)

    def test_common_effect_and_requester_fastest_is_dominated(self):
        result = candidate.evaluate(FIXTURE, "complete_conflict")
        self.assertEqual(result["eligible"], ["conflict", "d_route", "quick", "review"])
        self.assertEqual(result["requester_fastest"], "quick")
        self.assertEqual(result["profile"]["verified_dominated_by"]["quick"], ["review"])
        self.assertEqual(result["profile"]["possible_frontier"], ["conflict", "review"])
        self.assertEqual(result["decision_status"], "HANDOFF_MULTIPLE_OR_POSSIBLE_FRONTIER")
        self.assertEqual(result["borda"]["winner"], "review")

    def test_partial_frontier_completion_and_revoked_grant(self):
        result = candidate.evaluate(FIXTURE, "partial_with_revoked_grant")
        self.assertEqual(result["profile"]["completion_count"], 3)
        self.assertEqual(result["profile"]["possible_frontier"], ["conflict", "quick", "review"])
        self.assertEqual(result["profile"]["certain_frontier"], ["conflict", "quick"])
        self.assertEqual(result["profile"]["unresolved"], ["review"])
        self.assertNotIn("d_route", result["eligible"])

    def test_nontradeable_filter_precedes_preference_frontier(self):
        result = candidate.evaluate(FIXTURE, "protected_nontradeable")
        self.assertNotIn("quick", result["eligible"])
        self.assertIn("nontradeable:collaborator_b:private-review-content",
                      result["excluded_reasons"]["quick"])
        mutation = candidate.mutate(FIXTURE)["majority_overrides_nontradeable"]
        self.assertIn("quick", mutation["eligible"])
        self.assertEqual(mutation["requester_fastest"], "quick")

    def test_explicit_delegate_may_choose_but_conflict_case_cannot(self):
        result = candidate.evaluate(FIXTURE, "delegated_choice")
        self.assertEqual(result["delegated_decision_maker"], "collaborator_c")
        self.assertEqual(result["delegated_choice"], "conflict")
        self.assertIsNone(candidate.evaluate(FIXTURE, "complete_conflict")["delegated_choice"])

    def test_all_equal_preserves_every_alternative_without_unique_choice(self):
        result = candidate.evaluate(FIXTURE, "all_equal")
        self.assertEqual(result["profile"]["possible_frontier"],
                         ["conflict", "d_route", "quick", "review"])
        self.assertEqual(result["profile"]["certain_frontier"], result["profile"]["possible_frontier"])
        self.assertIsNone(result["delegated_choice"])

    def test_mutation_probes_change_the_correct_certificate(self):
        baseline = candidate.evaluate(FIXTURE, "partial_with_revoked_grant")
        mutations = candidate.mutate(FIXTURE)
        self.assertNotEqual(mutations["consent_as_indifference"]["profile"]["possible_frontier"],
                            baseline["profile"]["possible_frontier"])
        self.assertNotEqual(mutations["fabricated_missing_rank"]["profile"]["possible_frontier"],
                            baseline["profile"]["possible_frontier"])
        self.assertIn("quick", mutations["majority_overrides_nontradeable"]["eligible"])
        self.assertEqual(mutations["undominated_set_called_unique"]["decision_status"],
                         "UNIQUE_COLLECTIVE_OPTIMUM")

    def test_input_is_not_mutated_by_evaluation(self):
        fixture = copy.deepcopy(FIXTURE)
        before = copy.deepcopy(fixture)
        candidate.run(fixture)
        self.assertEqual(fixture, before)

    def test_independent_oracle_agrees_on_construction_fixture(self):
        result = candidate.run(copy.deepcopy(FIXTURE))
        checked = audit.verify(FIXTURE, result)
        self.assertEqual(checked["status"], "PASS_METHOD_SCOPED", checked["errors"])
        self.assertEqual(checked["mutation_controls_rejected"], 4)
        self.assertEqual(result["summary"]["protected_quick_ranked_first_by"], 2)


if __name__ == "__main__":
    unittest.main()
