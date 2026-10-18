import unittest
from auditor import plant as audit_plant, audit
from runner import plant as candidate_plant, trial, P as PROTOCOL


class T0bTests(unittest.TestCase):
    def test_independent_fixture_reconstruction(self):
        for c in PROTOCOL["conditions"]:
            for seed in (4000, 4007, 4029):
                self.assertEqual(audit_plant(seed,c),candidate_plant(seed,c))

    def test_trace_mutation_is_rejected(self):
        rows=[trial(seed,c,arm) for c in PROTOCOL["conditions"]
              for seed in range(PROTOCOL["heldout_seeds"][0],PROTOCOL["heldout_seeds"][1]+1)
              for arm in PROTOCOL["arms"]]
        self.assertFalse(audit(rows)["errors"])
        rows[0]["actions"][0][0]+=0.25
        self.assertTrue(audit(rows)["errors"])


if __name__=="__main__": unittest.main()
