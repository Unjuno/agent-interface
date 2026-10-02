"""Pre-formal construction checks; these do not create formal output files."""
from fractions import Fraction as F
import unittest

import auditor
import candidate


class Construction(unittest.TestCase):
    def test_correctly_saturated_routes_and_counterfactual(self):
        fresh = candidate.trajectory("fresh_saturated")
        delayed = candidate.trajectory("delayed_saturated")
        history = candidate.trajectory("history_saturated")
        counter = candidate.trajectory("unbounded_delayed_counterfactual")
        self.assertTrue(all(abs(F(x)) <= F(1, 2) for r in (fresh, delayed, history) for x in r["inputs"]))
        self.assertEqual(fresh["states"], history["states"])
        self.assertEqual(delayed["first_forbidden_step"], None)
        self.assertEqual(counter["first_forbidden_step"], 5)
        self.assertFalse(counter["actuation_admissible"])

    def test_auditor_reconstructs_independently(self):
        self.assertEqual(candidate.trajectory("delayed_saturated"), auditor.reconstruct("delayed_saturated"))


if __name__ == "__main__": unittest.main()
