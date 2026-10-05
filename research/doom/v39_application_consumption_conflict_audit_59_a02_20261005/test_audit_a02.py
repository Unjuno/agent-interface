import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
AUDITOR = ROOT / "audit_a02.py"
INPUT = ROOT / "input" / "A01.json"


class ChronologyAuditTests(unittest.TestCase):
    def test_raw_audit_recomputes_chronology_and_rejects_balanced_mutation(self):
        with tempfile.TemporaryDirectory() as output_dir:
            completed = subprocess.run(
                [sys.executable, str(AUDITOR), "--input", str(INPUT),
                 "--output-dir", output_dir],
                text=True, capture_output=True, check=False)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            report = json.loads(completed.stdout)
            self.assertEqual(report["status"], "PASS_RAW_CHRONOLOGY_MUTATION_REJECTED")
            self.assertEqual(report["original"]["status"], "PASS")
            self.assertEqual(report["mutated"]["status"], "REJECTED")
            self.assertEqual(report["mutated"]["chronology_mismatches"], 4)
            self.assertEqual(report["mutated"]["counts"], {
                "baseline": {"ordered": 15, "incomplete": 85},
                "candidate": {"ordered": 15, "incomplete": 85},
            })

            mutated = json.loads((Path(output_dir) / "mutated-A01.json").read_text())
            for implementation in ("baseline", "candidate"):
                mismatches = [row for row in mutated["interval_sweep"][implementation]["cases"]
                              if row["expected_ordered"] is not
                              (row["down"][1] < row["up"][0])]
                self.assertEqual(len(mismatches), 2, implementation)


if __name__ == "__main__":
    unittest.main()
