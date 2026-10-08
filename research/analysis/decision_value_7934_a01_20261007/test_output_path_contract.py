"""Regression contract for the one-shot formal output-path launch failure."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent


class FormalOutputPathContractTests(unittest.TestCase):
    def test_candidate_fails_closed_without_creating_missing_parent(self):
        model = ROOT / "fixtures" / "candidate_model.json"
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "not-created" / "candidate.json"
            result = subprocess.run(
                [sys.executable, "-B", str(ROOT / "candidate.py"), str(model), str(output)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("FileNotFoundError", result.stderr)
            self.assertFalse(output.parent.exists())

    def test_precreated_output_parent_accepts_formal_result(self):
        model = ROOT / "fixtures" / "candidate_model.json"
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "formal" / "candidate.json"
            output.parent.mkdir()
            result = subprocess.run(
                [sys.executable, "-B", str(ROOT / "candidate.py"), str(model), str(output)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["schema"], "decision-value-7934-candidate-raw-v1")
            self.assertEqual(len(payload["cases"]), 6)
