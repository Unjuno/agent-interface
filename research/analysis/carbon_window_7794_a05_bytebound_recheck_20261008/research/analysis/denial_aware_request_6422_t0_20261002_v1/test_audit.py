import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent


class IndependentAuditContractTests(unittest.TestCase):
    def test_auditor_rejects_raw_that_drops_the_frozen_denial_corpus(self):
        with tempfile.TemporaryDirectory() as temp:
            raw = Path(temp) / "raw.json"
            report = Path(temp) / "audit.json"
            raw.write_text(json.dumps({
                "schema": "denial-aware-candidate-output-v1",
                "fixture_sha256": "0" * 64,
                "case_count": 0,
                "rows": [],
            }), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(ROOT / "audit.py"),
                 "--input", str(ROOT / "fixtures.json"),
                 "--raw", str(raw), "--output", str(report)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 1, result.stderr or result.stdout)
            observed = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(observed["status"], "AUDIT_REJECTED")
            self.assertIn("ROW_COUNT_MISMATCH", observed["errors"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
