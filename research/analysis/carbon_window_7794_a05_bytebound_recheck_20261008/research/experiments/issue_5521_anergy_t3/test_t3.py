import copy
import io
import json
from pathlib import Path
import subprocess
import sys
import unittest
import audit

HERE = Path(__file__).resolve().parent

class T3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        proc = subprocess.run([sys.executable, str(HERE / "run.py")], check=True, capture_output=True, text=True)
        cls.records = [json.loads(line) for line in proc.stdout.splitlines()]

    def test_matched_arms_and_process_restart_audit(self):
        self.assertEqual(audit.validate(self.records), {
            "clear": {"verifier_checks": 6, "admitted_effects": 4},
            "tombstone": {"verifier_checks": 5, "admitted_effects": 3}})
        exits = [r for r in self.records if r["type"] == "process_exit"]
        self.assertEqual(len(exits), 6)
        self.assertEqual(len({r["pid"] for r in exits}), 6)

    def test_disposition_swap_mutation_is_rejected(self):
        rows = copy.deepcopy(self.records)
        clear = next(r for r in rows if r.get("policy") == "clear" and r.get("type") == "transition" and r["tick"] == 9)
        tomb = next(r for r in rows if r.get("policy") == "tombstone" and r.get("type") == "transition" and r["tick"] == 9)
        clear["disposition"], tomb["disposition"] = tomb["disposition"], clear["disposition"]
        with self.assertRaisesRegex(ValueError, "clear expiry outcome"):
            audit.validate(rows)

    def test_expiry_generation_mutation_is_rejected(self):
        rows = copy.deepcopy(self.records)
        freeze = rows[0]
        freeze["events"][7]["gen"] = 1
        with self.assertRaisesRegex(ValueError, "frozen schedule"):
            audit.validate(rows)

if __name__ == "__main__":
    unittest.main()
