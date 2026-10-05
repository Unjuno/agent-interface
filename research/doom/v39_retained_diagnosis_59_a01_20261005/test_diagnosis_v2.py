"""Regression for distinct policy and running-action invalidation evidence."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRODUCER = HERE / "analyze_v2.py"
LEGACY_RESULT = HERE / "RESULT.json"


class DiagnosisV2Tests(unittest.TestCase):
    def test_decision_three_keeps_action_revocation_and_release_separate(self):
        legacy_before = LEGACY_RESULT.read_bytes()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "RESULT_V2.json"
            completed = subprocess.run(
                [sys.executable, "-B", str(PRODUCER), "--output-path", str(output)],
                cwd=ROOT, text=True, capture_output=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            result = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(result["schema"], "issue59-v39-retained-diagnosis-result-v2")
        decision = result["decisions"][3]
        self.assertIsNone(decision["policy_invalidation"])
        self.assertEqual(decision["running_action_invalidation"]["kind"], "action_validity")
        self.assertEqual(decision["running_action"]["id"], "plan-3-primary-0-1")
        self.assertEqual(
            decision["running_action"]["partial_execution"]["status"],
            "cancelled_action_not_current",
        )
        lifecycle = decision["running_action"]["lifecycle"]
        self.assertEqual(lifecycle["accepted"]["accepted_ns"], 55531896125154)
        self.assertTrue(lifecycle["cancel_requested"]["matched"])
        self.assertTrue(lifecycle["input_released"]["owner_release"]["verified"])
        self.assertEqual(lifecycle["input_released"]["owner_release"]["keys_down"], [])
        self.assertEqual(lifecycle["input_released"]["owner_release"]["buttons_down"], [])
        self.assertEqual(lifecycle["terminal"]["status"], "cancelled")
        self.assertEqual(lifecycle["terminal"]["steps_completed"], 0)
        self.assertFalse(lifecycle["input_released"]["owner_release"]["grants_input_authority"])
        self.assertEqual(LEGACY_RESULT.read_bytes(), legacy_before)

    def test_producer_refuses_to_overwrite_an_existing_output(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "RESULT_V2.json"
            original = b"preserve this first result\n"
            output.write_bytes(original)
            completed = subprocess.run(
                [sys.executable, "-B", str(PRODUCER), "--output-path", str(output)],
                cwd=ROOT, text=True, capture_output=True,
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("already exists", completed.stderr + completed.stdout)
            self.assertEqual(output.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
