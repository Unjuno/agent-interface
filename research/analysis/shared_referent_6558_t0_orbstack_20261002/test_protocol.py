import importlib.util
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).parent
spec = importlib.util.spec_from_file_location("candidate", ROOT / "candidate.py")
candidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)


class ProtocolConstructionTests(unittest.TestCase):
    def setUp(self):
        self.fixture = json.loads((ROOT / "fixtures.json").read_text())
        self.truth = json.loads((ROOT / "oracle.json").read_text())["intended_object"]
        self.rows = [candidate.run_case(c) for c in self.fixture["cases"]]

    def audit(self, rows):
        with tempfile.TemporaryDirectory() as tmp:
            raw = pathlib.Path(tmp) / "candidate.json"
            report = pathlib.Path(tmp) / "audit.json"
            raw.write_text(json.dumps({"rows": rows}))
            result = subprocess.run([sys.executable, str(ROOT / "auditor.py"), str(ROOT / "fixtures.json"), str(ROOT / "oracle.json"), str(raw), str(report)], capture_output=True, text=True)
            return result.returncode, json.loads(report.read_text())

    def test_candidate_handles_rebind_and_unknown(self):
        by_id = {r["case_id"]: r for r in self.rows}
        self.assertEqual(by_id["sort-reuses-node"]["scoped_restatement"]["object"], "invoice-A")
        self.assertIsNone(by_id["missing-distinguishing-property"]["scoped_restatement"]["object"])
        self.assertEqual(by_id["zoom-only-benign"]["scoped_restatement"]["asks"], 0)
        self.assertFalse(by_id["attention-is-not-authority"]["authority_granted_by_cue"])

    def test_independent_audit_accepts_unmutated_rows(self):
        code, report = self.audit(self.rows)
        self.assertEqual((code, report["status"], report["errors"]), (0, "PASS_METHOD_SCOPED", []))

    def test_audit_rejects_target_mutation(self):
        rows = json.loads(json.dumps(self.rows))
        rows[2]["scoped_restatement"]["object"] = "invoice-B"
        code, report = self.audit(rows)
        self.assertNotEqual(code, 0)
        self.assertIn("SCOPED_RECONSTRUCTION:sort-reuses-node", report["errors"])

    def test_audit_rejects_authority_laundering_mutation(self):
        rows = json.loads(json.dumps(self.rows))
        rows[8]["authority_granted_by_cue"] = True
        code, report = self.audit(rows)
        self.assertNotEqual(code, 0)
        self.assertTrue(any(e.startswith("AUTHORITY_LAUNDERING:") for e in report["errors"]))

    def test_audit_rejects_missing_row(self):
        code, report = self.audit(self.rows[:-1])
        self.assertNotEqual(code, 0)
        self.assertIn("ROW_COUNT", report["errors"])


if __name__ == "__main__":
    unittest.main()
