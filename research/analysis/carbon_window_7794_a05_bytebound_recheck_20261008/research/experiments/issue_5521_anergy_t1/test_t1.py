import io
import json
import subprocess
import sys
import unittest
from pathlib import Path
import audit

HERE = Path(__file__).resolve().parent

class T1Tests(unittest.TestCase):
    def test_frozen_schedule_and_independent_replay_pass(self):
        run = subprocess.run([sys.executable, str(HERE / "run.py")], check=True,
                             capture_output=True, text=True)
        out = io.StringIO()
        audit.main(io.StringIO(run.stdout))
        records = [json.loads(x) for x in run.stdout.splitlines()]
        summary = records[-1]["policies"]
        self.assertEqual(summary["stateless"]["verifier_checks"], 8)
        self.assertEqual(summary["permanent"]["verifier_checks"], 4)
        self.assertEqual(summary["anergy"]["verifier_checks"], 5)
        self.assertEqual(summary["anergy"]["admitted_effects"], 3)

    def test_mutated_anergy_admission_is_rejected(self):
        run = subprocess.run([sys.executable, str(HERE / "run.py")], check=True,
                             capture_output=True, text=True)
        records = [json.loads(x) for x in run.stdout.splitlines()]
        row = next(r for r in records if r.get("policy") == "anergy" and r.get("tick") == 4 and r.get("op") == "propose")
        row["disposition"], row["effect"] = "ADMITTED", True
        mutated = "\n".join(json.dumps(r, sort_keys=True) for r in records) + "\n"
        with self.assertRaisesRegex(ValueError, "same-generation contradiction admitted"):
            audit.main(io.StringIO(mutated))

if __name__ == "__main__":
    unittest.main()
