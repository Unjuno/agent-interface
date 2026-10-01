"""Host construction tests for the separate candidate and raw-auditor CLIs."""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parent
FIXTURE = Path(os.environ["W2_TRACE_FIXTURE"])
EXPECTED_FIXTURE_SHA256 = "6a693f06b1b4be15a8da35ec3aaf806d7fb3601091c8ef638c516069d1b4e95f"


class BindingGateCliTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="w2-binding-cli-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def _run(self, name, mutations=()):
        out = self.root / name
        command = [sys.executable, str(ROOT / "binding_gate_cli.py"), "--traces", str(FIXTURE), "--output-dir", str(out)]
        for mutation in mutations:
            command += ["--open-binding", mutation]
        candidate = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(candidate.returncode, 0, candidate.stderr)
        report_path = out / "candidate-report.json"
        trace_path = out / "effective-traces.json"
        audit_path = out / "audit.json"
        auditor = subprocess.run([
            sys.executable, str(ROOT / "audit_binding_gate.py"),
            "--traces", str(trace_path), "--candidate-report", str(report_path), "--out", str(audit_path),
        ], capture_output=True, text=True)
        return out, candidate, auditor

    @staticmethod
    def _rows(report, case_id):
        case = next(c for c in report["cases"] if c["case_id"] == case_id)
        return [r["status"] for r in case["binding_decisions"]]

    def test_baseline_candidate_and_independent_audit(self):
        out, candidate, auditor = self._run("baseline")
        self.assertEqual(auditor.returncode, 0, auditor.stderr)
        report = json.loads((out / "candidate-report.json").read_text())
        audit = json.loads((out / "audit.json").read_text())
        self.assertEqual(hashlib.sha256(FIXTURE.read_bytes()).hexdigest(), EXPECTED_FIXTURE_SHA256)
        self.assertEqual(report["case_count"], 8)
        self.assertEqual(audit["disposition"], "PASS_BINDING_RAW_AUDIT_SCOPED")
        self.assertEqual(audit["candidate_oracle_disagreements"], 0)
        self.assertEqual(self._rows(report, "release-before-terminal"), ["HOLD_MISSING_LEASE_ACTUATION"] * 2)

    def test_four_matched_versioned_cases_pass_raw_audit(self):
        mutations = ["release-before-terminal=A4", "overlapping-key-holds=A5", "missing-and-out-of-order-edge=A6", "held-input-no-effect=A8"]
        out, _, auditor = self._run("matched", mutations)
        self.assertEqual(auditor.returncode, 0, auditor.stderr)
        report = json.loads((out / "candidate-report.json").read_text())
        for case_id in ("release-before-terminal", "overlapping-key-holds", "missing-and-out-of-order-edge", "held-input-no-effect"):
            with self.subTest(case_id=case_id):
                self.assertTrue(all(x == "AUTHORIZED_MATCH" for x in self._rows(report, case_id)))

    def test_foreign_actuation_and_missing_binding_are_audited(self):
        for name, mutation, expected in (
            ("foreign", "release-before-terminal=FOREIGN-ACTUATION", "REJECT_ACTUATION_MISMATCH"),
            ("missing", "release-before-terminal=MISSING", "HOLD_MISSING_LEASE_ACTUATION"),
        ):
            with self.subTest(name=name):
                out, _, auditor = self._run(name, [mutation])
                self.assertEqual(auditor.returncode, 0, auditor.stderr)
                report = json.loads((out / "candidate-report.json").read_text())
                self.assertTrue(all(x == expected for x in self._rows(report, "release-before-terminal")))

    def test_raw_auditor_rejects_tampered_candidate_disposition(self):
        out, _, _ = self._run("tamper-source")
        report_path = out / "candidate-report.json"
        report = json.loads(report_path.read_text())
        target = next(c for c in report["cases"] if c["case_id"] == "release-before-terminal")
        target["binding_decisions"][0]["status"] = "AUTHORIZED_MATCH"
        report_path.write_text(json.dumps(report), encoding="utf-8")
        result = subprocess.run([
            sys.executable, str(ROOT / "audit_binding_gate.py"),
            "--traces", str(out / "effective-traces.json"),
            "--candidate-report", str(report_path), "--out", str(out / "tamper-audit.json"),
        ], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("candidate_raw_disagreement:release-before-terminal", result.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
