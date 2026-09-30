import unittest

import audit
import candidate


class BeliefSupervisorTests(unittest.TestCase):
    def test_indistinguishable_fresh_and_stale_disables_commit(self):
        self.assertNotIn("COMMIT", candidate.safe_actions())

    def test_common_safe_revalidation_remains_enabled(self):
        self.assertIn("REVALIDATE", candidate.safe_actions())

    def test_every_enabled_action_is_safe_for_each_belief_member(self):
        edges = {(s, e): d for s, e, d in candidate.PLANT}
        for event in candidate.safe_actions():
            for state in candidate.BELIEF:
                self.assertIn((state, event), edges)
                self.assertNotIn(edges[(state, event)], candidate.UNSAFE)

    def test_exhaustive_maximal_oracle_agrees_with_candidate(self):
        _, _, maximal = candidate.enumerate_subsets()
        expected = {event for _, event, _ in next(iter(maximal))}
        self.assertEqual(candidate.safe_actions(), expected)

    def test_independent_literal_audit_accepts_candidate(self):
        self.assertEqual(audit.assess(candidate.result()), [])

    def test_independent_audit_rejects_all_preregistered_corruptions(self):
        raw = candidate.result()
        rejected, total = audit.corruption_controls(raw)
        self.assertEqual((rejected, total), (4, 4))


if __name__ == "__main__":
    unittest.main()
