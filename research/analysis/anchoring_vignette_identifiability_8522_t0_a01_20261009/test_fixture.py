from __future__ import annotations

import json
import unittest
from pathlib import Path

import auditor
import candidate


ROOT = Path(__file__).resolve().parent


class FixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "candidate_input.json").read_text())
        cls.oracle = json.loads((ROOT / "oracle.json").read_text())

    def test_assumption_satisfied_conditional_estimate_recovers_truth(self):
        row = candidate.analyze(self.data["cases"][0], self.data["spec"])
        self.assertAlmostEqual(row["contrast_conditional"], 0.6, delta=0.002)
        self.assertEqual(row["model_fit_gate"], "CONDITIONAL_FIT")
        self.assertFalse(row["calibrated_claim_permitted"])

    def test_detectable_nonuniform_vignette_shift_fails_fit_gate(self):
        row = candidate.analyze(self.data["cases"][1], self.data["spec"])
        self.assertGreater(row["max_anchor_residuals"]["comparison"], 0.01)
        self.assertEqual(row["model_fit_gate"], "REJECT_MISFIT")

    def test_auditor_reconstructs_candidate_independently(self):
        expected = [auditor.reconstruct(case, self.data["spec"]) for case in self.data["cases"]]
        actual = [candidate.analyze(case, self.data["spec"]) for case in self.data["cases"]]
        for want, got in zip(expected, actual):
            for key, value in want.items():
                self.assertTrue(auditor.close(value, got[key]), (key, value, got[key]))

    def test_two_latent_worlds_share_exact_observed_input_but_not_truth(self):
        worlds = self.oracle["worlds"]
        self.assertEqual(worlds[0]["observed_input_sha256"], worlds[1]["observed_input_sha256"])
        self.assertEqual([w["true_contrast"] for w in worlds], [0.6, 0.0])


if __name__ == "__main__":
    unittest.main()
