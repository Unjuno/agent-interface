import json
import unittest
from fractions import Fraction
from pathlib import Path

import auditor
import candidate


ROOT = Path(__file__).resolve().parent
FIXTURE_BYTES = (ROOT / "trace_fixture.json").read_bytes()
FIXTURE = json.loads(FIXTURE_BYTES)


class MethodConstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = candidate.calculate(FIXTURE, FIXTURE_BYTES)

    def test_primary_selection_and_rank_reversal(self):
        primary = self.result["primary"]
        self.assertEqual(primary["recovery_demand_mix"], {"easy": "1/5", "hard": "4/5"})
        self.assertEqual(primary["recovery_unconditional"], {"A": "108/125", "B": "69/100"})
        self.assertEqual(primary["recovery_conditional"], {"A": "129/250", "B": "33/50"})
        self.assertGreater(Fraction(primary["recovery_unconditional"]["A"]), Fraction(primary["recovery_unconditional"]["B"]))
        self.assertLess(Fraction(primary["recovery_conditional"]["A"]), Fraction(primary["recovery_conditional"]["B"]))

    def test_joint_and_naive_estimators_are_distinct(self):
        primary = self.result["primary"]
        self.assertEqual(primary["joint_system_outcome"], {"A": "1129/1250", "B": "233/250"})
        self.assertEqual(primary["naive_joint_using_unconditional_recovery"], {"A": "608/625", "B": "469/500"})

    def test_no_selection_control_is_invariant(self):
        control = self.result["controls"]["no_selection"]
        self.assertEqual(control["recovery_demand_mix"], {"easy": "4/5", "hard": "1/5"})
        self.assertEqual(control["recovery_conditional"], control["recovery_unconditional"])

    def test_equal_sensitivity_control_preserves_ranking(self):
        control = self.result["controls"]["equal_sensitivity"]
        self.assertGreater(Fraction(control["recovery_unconditional"]["A"]), Fraction(control["recovery_unconditional"]["B"]))
        self.assertGreater(Fraction(control["recovery_conditional"]["A"]), Fraction(control["recovery_conditional"]["B"]))

    def test_independent_oracle_and_all_mutation_controls(self):
        self.assertEqual(auditor.audit(self.result, FIXTURE, FIXTURE_BYTES), [])
        rejected = auditor.mutation_checks(self.result, FIXTURE, FIXTURE_BYTES)
        self.assertEqual(set(rejected), {
            "swap_conditional_unconditional",
            "drop_hard_regime",
            "reset_demand_to_initial_mix",
            "count_safe_stop_as_success",
        })
        self.assertTrue(all(rejected.values()))


if __name__ == "__main__":
    unittest.main()
