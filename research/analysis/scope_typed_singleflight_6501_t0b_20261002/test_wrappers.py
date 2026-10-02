"""Construction tests for T0b's raw-artifact command wrappers."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class WrapperOutputTests(unittest.TestCase):
    def test_candidate_wrapper_writes_valid_json_with_one_real_lf(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "candidate.json"
            process = subprocess.run(
                [sys.executable, "-B", "run_candidate.py", str(output)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(process.returncode, 0, process.stderr)
            raw_bytes = output.read_bytes()
            self.assertTrue(raw_bytes.endswith(bytes((10,))))
            self.assertFalse(raw_bytes.endswith(bytes((92, 110))))
            parsed = json.loads(raw_bytes)
            self.assertEqual(len(parsed["cases"]), 10)

    def test_auditor_wrapper_emits_a_parseable_pass_receipt(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            candidate = Path(temp_dir) / "candidate.json"
            audit = Path(temp_dir) / "audit.json"
            made = subprocess.run(
                [sys.executable, "-B", "run_candidate.py", str(candidate)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(made.returncode, 0, made.stderr)
            checked = subprocess.run(
                [sys.executable, "-B", "run_auditor.py", str(candidate), str(audit)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(checked.returncode, 0, checked.stderr)
            self.assertEqual(json.loads(audit.read_bytes())["status"], "PASS_METHOD_SCOPED")


if __name__ == "__main__":
    unittest.main(verbosity=2)
