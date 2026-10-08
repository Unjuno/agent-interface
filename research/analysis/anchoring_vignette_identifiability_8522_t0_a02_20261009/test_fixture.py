from __future__ import annotations

import json
import subprocess
import sys
import tempfile
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

    def test_candidate_input_does_not_contain_auditor_truth(self):
        self.assertNotIn("true_contrast", json.dumps(self.data, sort_keys=True))
        self.assertNotIn("observed_input_sha256", json.dumps(self.data, sort_keys=True))

    def test_candidate_and_auditor_cli_from_repository_root(self):
        repo_root = ROOT.parents[2]
        with tempfile.TemporaryDirectory(prefix="8522-a02-cli-") as temp:
            candidate_path = Path(temp) / "candidate.json"
            audit_path = Path(temp) / "audit.json"
            candidate_run = subprocess.run(
                [sys.executable, str(ROOT / "candidate.py"), str(ROOT / "candidate_input.json"), str(candidate_path)],
                cwd=repo_root, capture_output=True, text=True, check=False,
            )
            self.assertEqual(candidate_run.returncode, 0, candidate_run.stderr)
            self.assertTrue(candidate_path.is_file())
            auditor_run = subprocess.run(
                [sys.executable, str(ROOT / "auditor.py"), str(ROOT / "candidate_input.json"),
                 str(candidate_path), str(ROOT / "oracle.json"), str(audit_path)],
                cwd=repo_root, capture_output=True, text=True, check=False,
            )
            self.assertEqual(auditor_run.returncode, 0, auditor_run.stderr)
            self.assertEqual(json.loads(audit_path.read_text())["disposition"], "HOLD_NOT_IDENTIFIED")


if __name__ == "__main__":
    unittest.main()
