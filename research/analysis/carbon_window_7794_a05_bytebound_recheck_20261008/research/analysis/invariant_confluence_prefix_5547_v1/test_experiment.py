import unittest

import experiment


class InvariantConfluenceTests(unittest.TestCase):
    def test_unknown_schema_fails_closed(self):
        self.assertEqual(experiment.transition(experiment.INITIAL, ("UNKNOWN_SCHEMA", "x")), None)
        self.assertEqual(experiment.execute()["classifications"]["UNKNOWN_SCHEMA"], "coordination_required")

    def test_preregistered_conflict_families_are_exact(self):
        result = experiment.execute()
        self.assertEqual({tuple(x) for x in result["actual_conflict_families"]},
                         experiment.EXPECTED_CONFLICT_FAMILIES)

    def test_serial_baseline_preserves_invariants(self):
        self.assertTrue(experiment.execute()["serial_baseline_invariant_safe"])

    def test_safe_operation_pairs_are_join_closed(self):
        self.assertTrue(experiment.execute()["safe_operation_pairs_invariant_safe"])

    def test_join_is_commutative_for_every_enumerated_pair(self):
        self.assertTrue(experiment.execute()["all_join_argument_orders_equal"])

    def test_exactly_two_operation_families_are_classified_safe(self):
        classes = experiment.execute()["classifications"]
        self.assertEqual({k for k, v in classes.items() if v == "monotone_safe"},
                         {"ADD_EVIDENCE", "REVOKE_CLAIM"})

    def test_quota_and_effect_counterexamples_exist(self):
        conflicts = {tuple(x) for x in experiment.execute()["actual_conflict_families"]}
        self.assertIn(("RESERVE_QUOTA", "RESERVE_QUOTA"), conflicts)
        self.assertIn(("COMMIT_EFFECT", "COMMIT_EFFECT"), conflicts)


if __name__ == "__main__":
    unittest.main()
