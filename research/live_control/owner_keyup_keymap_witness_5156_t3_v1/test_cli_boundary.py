import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from test_audit_formal_x11 import fixture_rows


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
            self.assertEqual(run["candidate_fixture_source_sha256"],
                             hashlib.sha256((HERE / "test_audit_formal_x11.py").read_bytes()).hexdigest())
            self.assertEqual(run["experiment_driver_sha256"],
                             hashlib.sha256(DRIVER.read_bytes()).hexdigest())
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

    def test_synthetic_mode_fails_closed_when_provenance_marker_is_removed(self):
        with tempfile.TemporaryDirectory() as temporary:
            raw = Path(temporary) / "marker-removed.jsonl"
            audit_path = Path(temporary) / "audit.json"
            records = fixture_rows()
            records[0].pop("synthetic_only")
            raw.write_text("".join(json.dumps(row) + "\n" for row in records), encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, "-B", str(HERE / "audit_formal_x11.py"), str(raw),
                 str(HERE / "EXPECTED.json"), str(audit_path), "synthetic-cli"],
                cwd=HERE, capture_output=True, text=True, timeout=10, check=False)
            result = json.loads(audit_path.read_text(encoding="utf-8"))
            self.assertNotEqual(completed.returncode, 0)
            self.assertEqual(result["status"], "FAIL_AUDIT")
            self.assertTrue(any("requires exactly one fixture marked synthetic_only=true" in error
                                for error in result["errors"]))
            self.assertIn("synthetic JSONL", result["scope"])

    def test_formal_mode_rejects_synthetic_provenance_marker(self):
        with tempfile.TemporaryDirectory() as temporary:
            raw = Path(temporary) / "synthetic.jsonl"
            audit_path = Path(temporary) / "audit.json"
            raw.write_text("".join(json.dumps(row) + "\n" for row in fixture_rows()),
                           encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, "-B", str(HERE / "audit_formal_x11.py"), str(raw),
                 str(HERE / "EXPECTED.json"), str(audit_path), "formal-x11"],
                cwd=HERE, capture_output=True, text=True, timeout=10, check=False)
            result = json.loads(audit_path.read_text(encoding="utf-8"))
            self.assertNotEqual(completed.returncode, 0)
            self.assertEqual(result["status"], "FAIL_AUDIT")
            self.assertTrue(any("formal-x11 mode requires exactly one explicit formal-x11 fixture" in error
                                for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
