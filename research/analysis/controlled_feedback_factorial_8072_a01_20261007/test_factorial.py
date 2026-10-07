import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import candidate
import audit


class FactorialConstructionTests(unittest.TestCase):
    def test_complete_crossed_design_and_matched_query_counts(self):
        rows = [candidate.run_cell(seed, feedback, updater)
                for seed in range(100) for feedback in candidate.FEEDBACKS for updater in candidate.UPDATERS]
        self.assertEqual(len(rows), 400)
        self.assertEqual(len({(r["seed"], r["feedback"], r["updater"]) for r in rows}), 400)
        self.assertEqual({r["query_count"] for r in rows}, {5})

    def test_feedback_and_update_factors_are_crossed(self):
        rows = {(r["seed"], r["feedback"], r["updater"]): r
                for r in (candidate.run_cell(7, f, u) for f in candidate.FEEDBACKS for u in candidate.UPDATERS)}
        self.assertEqual(set(rows), {(7, f, u) for f in candidate.FEEDBACKS for u in candidate.UPDATERS})
        for updater in candidate.UPDATERS:
            full = rows[(7, "FULL", updater)]
            controlled = rows[(7, "CONTROLLED", updater)]
            self.assertEqual(full["updater"], controlled["updater"])
            self.assertEqual(full["query_count"], controlled["query_count"])

    def test_safety_veto_and_fresh_firewall_are_exact(self):
        for feedback in candidate.FEEDBACKS:
            for updater in candidate.UPDATERS:
                row = candidate.run_cell(11, feedback, updater)
                self.assertEqual(row["safety_veto_count"], 1)
                self.assertTrue(row["candidate_locked_before_fresh"])
                self.assertTrue(row["raw_released_after_lock"])
                self.assertFalse(any(t["fresh_read"] for t in row["trace"]))
                self.assertTrue(row["trace"][2]["disclosed_exactly"])

    def test_independent_reconstruction_and_mutations(self):
        rows = [candidate.run_cell(seed, feedback, updater)
                for seed in range(100) for feedback in candidate.FEEDBACKS for updater in candidate.UPDATERS]
        self.assertEqual(audit.reconstruct(rows), [])
        self.assertEqual(audit.mutation_checks(rows), [])


if __name__ == "__main__":
    unittest.main()
