import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent

class MethodTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p = subprocess.run([sys.executable, str(HERE / "candidate.py")], check=True, capture_output=True, text=True)
        cls.rows = [json.loads(line) for line in p.stdout.splitlines()]

    def check_audit(self, rows):
        with tempfile.NamedTemporaryFile("w", encoding="utf-8") as f:
            f.write("\n".join(json.dumps(x) for x in rows))
            f.flush()
            return subprocess.run([sys.executable, str(HERE / "audit.py"), f.name], capture_output=True, text=True)

    def test_preregistered_distinctions(self):
        p = self.check_audit(self.rows)
        self.assertEqual(p.returncode, 0, p.stderr)
        result = json.loads(p.stdout)
        self.assertEqual(result["rows"], 12)
        self.assertEqual(result["old_aoi"], 5)
        self.assertEqual(result["old_aoii"], 0)
        self.assertEqual(result["fresh_wrong_aoi"], 1)
        self.assertEqual(result["fresh_wrong_aoii"], 2)
        self.assertEqual(result["rapid_reversal_aoii"], 1)

    def test_truth_mutation_rejected(self):
        rows = copy.deepcopy(self.rows)
        row = next(r for r in rows if r.get("type") == "delivery" and r["case"] == "old_unchanged")
        row["incorrect"] = True
        self.assertNotEqual(self.check_audit(rows).returncode, 0)

    def test_missing_truth_cannot_be_zero(self):
        rows = copy.deepcopy(self.rows)
        row = next(r for r in rows if r.get("type") == "delivery" and r["case"] == "missing_truth")
        row["incorrect"] = False
        self.assertNotEqual(self.check_audit(rows).returncode, 0)

    def test_generation_mutation_rejected(self):
        rows = copy.deepcopy(self.rows)
        row = next(r for r in rows if r.get("type") == "delivery" and r["case"] == "generation_change")
        row["generation_match"] = True
        self.assertNotEqual(self.check_audit(rows).returncode, 0)

    def test_authority_mutation_rejected(self):
        rows = copy.deepcopy(self.rows)
        row = next(r for r in rows if r.get("type") == "delivery")
        row["authority"] = True
        self.assertNotEqual(self.check_audit(rows).returncode, 0)

if __name__ == "__main__":
    unittest.main()
