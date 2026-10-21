import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SOURCE = Path(__file__).with_name("candidate.py")
AUDITOR = Path(__file__).with_name("auditor.py")
FIXED_SPEC = Path(__file__).with_name("spec.json")


class CandidateCliTests(unittest.TestCase):
    def test_full_frozen_spec_candidate_and_auditor_clis_write_auditable_outputs(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            candidate_output = root / "candidate.json"
            audit_output = root / "audit.json"
            candidate_run = subprocess.run([sys.executable, str(SOURCE), "--input", str(FIXED_SPEC), "--output", str(candidate_output)], capture_output=True, text=True)
            self.assertEqual(candidate_run.returncode, 0, candidate_run.stderr)
            self.assertEqual(candidate_run.stdout.strip(), "CANDIDATE_COMPLETE cards=24")
            audit_run = subprocess.run([sys.executable, str(AUDITOR), "--spec", str(FIXED_SPEC), "--candidate", str(candidate_output), "--output", str(audit_output)], capture_output=True, text=True)
            self.assertEqual(audit_run.returncode, 0, audit_run.stderr)
            self.assertEqual(audit_run.stdout.strip(), "AUDIT_COMPLETE PASS errors=0")
            result = json.loads(audit_output.read_text(encoding="utf-8"))
            self.assertEqual((result["cards_reconstructed"], result["comprehension_keys"]), (24, 120))

    def test_cli_reads_spec_writes_auditable_json_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            spec = root / "spec.json"
            output = root / "result.json"
            spec.write_text(json.dumps({"families": [{"id": "F", "operation": "save", "target": "D", "status": "pending", "evidence": "not sent"}]}), encoding="utf-8")
            command = [sys.executable, str(SOURCE), "--input", str(spec), "--output", str(output)]
            first = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(first.stdout.strip(), "CANDIDATE_COMPLETE cards=3")
            result = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(len(result), 3)
            self.assertEqual([len(card["options"]) for card in result], [2, 3, 4])
            second = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(second.returncode, 0)
            self.assertIn("FileExistsError", second.stderr)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), result)


if __name__ == "__main__":
    unittest.main()
