"""Mutation controls for the versioned full-result audit."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
AUDITOR = HERE / "audit_v2.py"
RESULT = HERE / "RESULT.json"


def run_auditor(result_path=None):
    command = [sys.executable, "-B", str(AUDITOR)]
    if result_path is not None:
        command.extend(["--result-path", str(result_path)])
    return subprocess.run(command, cwd=ROOT, text=True, capture_output=True)


class FullResultAuditTests(unittest.TestCase):
    def test_frozen_result_passes(self):
        completed = run_auditor()
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("AUDIT_V2_PASS", completed.stdout)

    def test_tampered_derived_fields_are_rejected(self):
        mutations = {
            "terminal status": lambda result: result["decisions"][0].__setitem__(
                "cover_terminal_status", "active"),
            "accept timestamp": lambda result: result["decisions"][0].__setitem__(
                "cover_accept_ns", 1),
            "aggregate deaths": lambda result: result["aggregate_score"].__setitem__(
                "deaths", 99),
            "physical occupancy scope": lambda result: result["limitations"].__setitem__(
                "physical_key_occupancy", True),
            "model wait": lambda result: result["decisions"][0].__setitem__(
                "model_wait_ms", 0.0),
            "boolean timestamp alias": lambda result: result["decisions"][0].__setitem__(
                "cover_accept_ns", True),
        }
        original = json.loads(RESULT.read_text(encoding="utf-8"))
        for label, mutate in mutations.items():
            with self.subTest(field=label), tempfile.TemporaryDirectory() as directory:
                changed = json.loads(json.dumps(original))
                mutate(changed)
                changed_path = Path(directory) / "RESULT.json"
                changed_path.write_text(
                    json.dumps(changed, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                completed = run_auditor(changed_path)
                self.assertNotEqual(completed.returncode, 0, label)
                self.assertIn("RESULT_MISMATCH", completed.stderr + completed.stdout)


if __name__ == "__main__":
    unittest.main()
