import json
import unittest
from pathlib import Path

from candidate import evaluate


class FrozenCaseConstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = json.loads(Path("cases.json").read_text(encoding="utf-8"))
        cls.results = {row["id"]: evaluate(row) for row in cls.cases}

    def test_preregistered_family_has_eight_unique_cases(self):
        self.assertEqual(len(self.cases), 8)
        self.assertEqual(len(self.results), 8)

    def test_positive_control_certifies_but_unsafe_coupling_is_refused(self):
        self.assertEqual(self.results["C01_uncoupled_positive"]["disposition"], "CERTIFIED")
        unsafe = self.results["C02_cross_coupled_unstable"]
        self.assertEqual(unsafe["disposition"], "NO_COMPOSITION_CERTIFICATE")
        self.assertTrue(unsafe["crosses_feature_limit"])
        self.assertTrue(all(unsafe["subsystem_checks"].values()))

    def test_delay_jitter_release_and_conservative_boundary_cases_stay_explicit(self):
        delayed = self.results["C03_delayed_jitter_shared_actuator_stable"]
        self.assertEqual(delayed["delay_max"], 2)
        self.assertEqual(delayed["disposition"], "CERTIFIED")
        self.assertEqual(self.results["C04_unit_eigenvalue_boundary"]["gain_envelope_status"], "BOUNDED_NONCONVERGENT_ENVELOPE")
        self.assertEqual(self.results["C05_stable_conservative_reject"]["gain_envelope_status"], "STABLE_ENVELOPE")
        self.assertEqual(self.results["C05_stable_conservative_reject"]["disposition"], "NO_COMPOSITION_CERTIFICATE")
        self.assertEqual(self.results["C06_release_lag_included"]["disposition"], "NO_COMPOSITION_CERTIFICATE")

    def test_hold_cap_and_disturbance_escape_are_not_certified(self):
        self.assertFalse(self.results["C07_held_input_cap_refusal"]["hold_contract_valid"])
        self.assertEqual(self.results["C07_held_input_cap_refusal"]["disposition"], "NO_COMPOSITION_CERTIFICATE")
        disturbance = self.results["C08_estimator_disturbance_feature_escape"]
        self.assertTrue(disturbance["crosses_feature_limit"])
        self.assertEqual(disturbance["disposition"], "NO_COMPOSITION_CERTIFICATE")


if __name__ == "__main__":
    unittest.main()
