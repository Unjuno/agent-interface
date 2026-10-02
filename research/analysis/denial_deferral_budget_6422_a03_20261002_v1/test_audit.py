import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent


class IndependentBudgetAuditTests(unittest.TestCase):
    def test_raw_oracle_reconstructs_budget_boundary_and_corruptions(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw, report = Path(tmp) / "raw.json", Path(tmp) / "audit.json"
            candidate = subprocess.run([sys.executable, str(ROOT / "candidate.py"), "--input", str(ROOT / "fixtures.json"), "--output", str(raw)], capture_output=True, text=True)
            self.assertEqual(candidate.returncode, 0, candidate.stdout + candidate.stderr)
            audit = subprocess.run([sys.executable, str(ROOT / "audit.py"), "--input", str(ROOT / "fixtures.json"), "--raw", str(raw), "--output", str(report)], capture_output=True, text=True)
            self.assertEqual(audit.returncode, 0, audit.stdout + audit.stderr)
            result = json.loads(report.read_text(encoding="utf-8"))
        self.assertEqual(result["status"], "PASS_METHOD_SCOPED")
        self.assertEqual(result["cases_reconstructed"], 9)
        self.assertEqual(result["unbounded_repeat_eligibilities"], 1)
        self.assertEqual(result["bounded_repeat_presentations"], 0)
        self.assertEqual(result["bounded_first_presentations"], 2)
        self.assertEqual(result["bounded_evidence_replay_holds"], 1)
        self.assertEqual(result["effect_authorized_count"], 0)
        self.assertEqual(len(result["corruption_controls_rejected"]), 5)
        self.assertTrue(all(result["corruption_controls_rejected"].values()))


if __name__ == "__main__":
    unittest.main(verbosity=2)
