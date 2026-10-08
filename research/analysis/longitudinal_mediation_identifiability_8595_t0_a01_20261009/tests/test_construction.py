import importlib.util
from fractions import Fraction
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

candidate = load("candidate")
auditor = load("auditor")

class ConstructionTests(unittest.TestCase):
    def test_gformula_recovers_zero_and_known_effect_on_disjoint_toy(self):
        rows = []
        for a in (0, 1):
            for d in (0, 1):
                for l in (0, 1):
                    for m in (0, 1):
                        for y in (0, 1):
                            rows.append({"a":a,"d":d,"l":l,"m":m,"y":y if m else y})
        estimate, status = candidate.gformula(rows, True)
        self.assertEqual(status, "ESTIMATED")
        self.assertEqual(estimate, 0.0)
        self.assertEqual(auditor.gformula(rows, True), (0, "ESTIMATED"))

    def test_missing_post_assignment_stratum_fails_closed(self):
        rows=[]
        for d in (0,1):
            for m in (0,1):
                for y in (0,1):
                    rows.append({"a":0,"d":d,"l":0,"m":m,"y":y})
                    rows.append({"a":1,"d":d,"l":1,"m":m,"y":y})
        self.assertEqual(candidate.gformula(rows, True), (None, "NOT_IDENTIFIABLE_POSITIVITY"))
        self.assertEqual(auditor.gformula(rows, True), (None, "NOT_IDENTIFIABLE_POSITIVITY"))

    def test_zero_mass_target_stratum_does_not_hide_missing_source_support(self):
        rows=[]
        for d in (0,1):
            for m in (0,1):
                for y in (0,1):
                    rows.append({"a":0,"d":d,"l":1,"m":m,"y":y})
                    rows.append({"a":1,"d":d,"l":0,"m":m,"y":y})
        expected = (None, "NOT_IDENTIFIABLE_POSITIVITY")
        self.assertEqual(candidate.gformula(rows, True), expected)
        self.assertEqual(auditor.gformula(rows, True), expected)

    def test_hidden_pair_builder_has_distinct_observed_world_support(self):
        c, h = candidate.hidden_pair()
        self.assertEqual(candidate.observed_table(c), candidate.observed_table(h))
        self.assertEqual(len(c), 80)
        self.assertEqual(len(h), 80)
        self.assertAlmostEqual(candidate.total_effect(c), 0.4)
        self.assertAlmostEqual(candidate.total_effect(h), 0.4)


    def test_naive_post_assignment_adjustment_can_invent_a_pathway(self):
        rows=[]
        for d in (0,1):
            for a in (0,1):
                for l in (0,1):
                    if a == 0:
                        m1 = 5 if l == 0 else 15
                        n = 20
                    else:
                        m1 = 10 if l == 0 else 19
                        n = 20
                    for index in range(n):
                        m = int(index < m1)
                        rows.append({"a":a,"d":d,"l":l,"m":m,"y":l})
        correct, status = candidate.gformula(rows, True)
        naive, naive_status = candidate.gformula(rows, False)
        self.assertEqual(status, "ESTIMATED")
        self.assertEqual(naive_status, "ESTIMATED")
        self.assertAlmostEqual(correct, 0.0)
        # Independent count arithmetic: psi(g0)=119/319, psi(g1)=1/2.
        expected_naive = Fraction(1, 2) - Fraction(119, 319)
        self.assertAlmostEqual(naive, float(expected_naive), places=12)
        self.assertEqual(auditor.gformula(rows, True), (0, "ESTIMATED"))
        self.assertEqual(auditor.gformula(rows, False)[0], expected_naive)

    def test_oracle_component_interaction_is_not_mediator_pathway(self):
        q=lambda a,m:(1+a+2*m)/8
        interaction=q(1,1)-q(1,0)-q(0,1)+q(0,0)
        self.assertEqual(interaction,0.0)
        self.assertEqual((1/6)*(2/8),1/24)
        self.assertNotEqual(interaction,(1/6)*(2/8))

if __name__ == "__main__":
    unittest.main()
