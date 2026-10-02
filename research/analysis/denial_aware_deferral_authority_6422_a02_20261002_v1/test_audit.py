import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent


class IndependentAuditTests(unittest.TestCase):
    def test_raw_audit_reconstructs_and_rejects_five_corruptions(self):
        with tempfile.TemporaryDirectory() as temp:
            raw = Path(temp) / "raw.json"
            report = Path(temp) / "audit.json"
            subprocess.run([sys.executable, str(ROOT / "candidate.py"), "--input", str(ROOT / "fixtures.json"), "--output", str(raw)], check=True)
            run = subprocess.run([sys.executable, str(ROOT / "audit.py"), "--input", str(ROOT / "fixtures.json"), "--raw", str(raw), "--output", str(report)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            result = json.loads(report.read_text(encoding="utf-8"))
        self.assertEqual(result["status"], "PASS_METHOD_SCOPED")
        self.assertEqual(result["cases_reconstructed"], 8)
        self.assertEqual(result["baseline_unauthorized_reopens"], 3)
        self.assertEqual(result["guarded_unauthorized_reopens"], 0)
        self.assertEqual(result["effect_authorized_count"], 0)
        self.assertTrue(all(result["corruption_controls_rejected"].values()))


if __name__ == "__main__":
    unittest.main(verbosity=2)
