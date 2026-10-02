"""Construction-only behavioral test for Issue #6222's crossed audit runner."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
ALLOCATION = "CROSS-VERDICT-REPEATABILITY-6222-T0-HOST-20261001-01"
MAIN = "14b81dd1f6853623a694266b98538f812847257a"


class CrossedAuditConstructionTests(unittest.TestCase):
    def test_detects_ranking_fragility_without_promoting_shared_consensus(self):
        """The runner must expose planted flips and retain ambiguity/missingness."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            freeze = tmp_path / "freeze.json"
            output = tmp_path / "candidate.json"
            freeze.write_text(json.dumps({"allocation_id": ALLOCATION, "main_sha": MAIN}), encoding="utf-8")
            run = subprocess.run(
                [sys.executable, str(HERE / "candidate.py"), "--fixture", str(HERE / "fixture.json"), "--freeze", str(freeze), "--output", str(output)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(run.returncode, 0, run.stderr)
            result = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(result["allocation_id"], ALLOCATION)
            self.assertTrue(result["reference_deck_pass"])
            self.assertEqual(result["one_pass_rankings"]["stable"], ["A>B"])
            self.assertEqual(result["crossed_rankings"]["stable"], ["A>B"])
            self.assertEqual(result["one_pass_rankings"]["within"], ["A>B"])
            self.assertIn("B>A", result["crossed_rankings"]["within"])
            self.assertIn("B>A", result["crossed_rankings"]["setup"])
            self.assertEqual(result["shared_bias_flags"], ["shared_bias:B2"])
            self.assertFalse(result["shared_bias_is_validity_certificate"])
            self.assertGreater(result["unknown_rows_by_case"]["ambiguous"], 0)
            missing = result["score_intervals"]["missing"]["E1/S1/1"]["B"]
            self.assertEqual(missing["missing"], 1)
            self.assertLess(missing["lower"], missing["upper"])
            audit_path = tmp_path / "audit.json"
            audit_run = subprocess.run(
                [sys.executable, str(HERE / "auditor.py"), "--fixture", str(HERE / "fixture.json"), "--freeze", str(freeze), "--candidate", str(output), "--output", str(audit_path)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(audit_run.returncode, 0, audit_run.stderr)
            audit = json.loads(audit_path.read_text(encoding="utf-8"))
            self.assertEqual(audit["disposition"], "PASS_AUDIT_METHOD_SCOPED")
            self.assertEqual(audit["allocation_id_expected"], ALLOCATION)
            self.assertEqual(audit["allocation_id_observed"], ALLOCATION)
            self.assertEqual(audit["mutations_rejected"], 5)
            self.assertEqual(audit["errors"], [])


if __name__ == "__main__":
    unittest.main()
