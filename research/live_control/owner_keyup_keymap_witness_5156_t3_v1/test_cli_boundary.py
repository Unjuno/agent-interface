import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
DRIVER = HERE / "run_cli_construction_experiment.py"


class RawOnlyCliBoundaryTests(unittest.TestCase):
    def test_candidate_and_raw_only_auditor_run_once_in_distinct_processes(self):
        with tempfile.TemporaryDirectory() as temporary:
            results = Path(temporary) / "construction-cli-01"
            completed = subprocess.run(
                [sys.executable, "-B", str(DRIVER), "--results", str(results)],
                cwd=HERE, capture_output=True, text=True, timeout=15, check=False)
            self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)

            run = json.loads((results / "RUN.json").read_text(encoding="utf-8"))
            audit = json.loads((results / "audit.json").read_text(encoding="utf-8"))
            raw = (results / "raw.jsonl").read_bytes()
            self.assertEqual(run["disposition"], "PASS_SYNTHETIC_RAW_ONLY_CLI_BOUNDARY")
            self.assertEqual(run["candidate_invocations"], 1)
            self.assertEqual(run["auditor_invocations"], 1)
            self.assertEqual(run["audit_returncode"], 0)
            self.assertNotEqual(run["candidate_pid"], run["auditor_pid"])
            self.assertEqual(audit["status"], "PASS_SYNTHETIC_RAW_ONLY_CLI_BOUNDARY")
            self.assertIn("no X server", audit["scope"])
            self.assertEqual(audit["raw_sha256"], hashlib.sha256(raw).hexdigest())
            self.assertEqual(sum(1 for line in raw.splitlines()
                                 if json.loads(line).get("event") == "keymap_snapshot"), 9)
            previous_run = (results / "RUN.json").read_bytes()
            previous_raw = raw
            retry = subprocess.run(
                [sys.executable, "-B", str(DRIVER), "--results", str(results)],
                cwd=HERE, capture_output=True, text=True, timeout=15, check=False)
            self.assertNotEqual(retry.returncode, 0)
            self.assertEqual((results / "RUN.json").read_bytes(), previous_run)
            self.assertEqual((results / "raw.jsonl").read_bytes(), previous_raw)


if __name__ == "__main__":
    unittest.main()
