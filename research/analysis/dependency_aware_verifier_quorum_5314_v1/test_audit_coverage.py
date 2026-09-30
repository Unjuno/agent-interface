"""Regression probe: an auditor must reject a raw file with an omitted case."""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import audit_v2


class CoverageGateRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.study = Path(__file__).parent
        cls.raw = json.loads((cls.study / "raw.json").read_text(encoding="utf-8"))

    def test_v2_rejects_an_omitted_case(self):
        raw = json.loads(json.dumps(self.raw))
        raw["rows"].pop()
        result = audit_v2.audit(raw)
        self.assertIn("coverage_missing_cases:1", result["discrepancies"])

    def test_v2_rejects_a_duplicated_case(self):
        raw = json.loads(json.dumps(self.raw))
        raw["rows"].append(json.loads(json.dumps(raw["rows"][0])))
        result = audit_v2.audit(raw)
        self.assertTrue(any("duplicate_case" in error for error in result["discrepancies"]))

    def test_all_v2_mutation_controls_reject_the_corruption(self):
        controls = audit_v2.run_controls(self.raw)
        self.assertEqual(len(controls), 6)
        self.assertTrue(all(control["rejected"] for control in controls))

    def test_v1_gap_reproduction_records_the_old_auditors_false_pass(self):
        study = Path(__file__).parent
        source_auditor = study / "independent_audit.py"
        with tempfile.TemporaryDirectory(prefix="quorum-audit-gap-") as temporary:
            target = Path(temporary)
            shutil.copyfile(source_auditor, target / "audit_under_test.py")
            raw = json.loads(json.dumps(self.raw))
            raw["rows"].pop()
            (target / "raw.json").write_text(json.dumps(raw), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(target / "audit_under_test.py")],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            old_audit = json.loads(result.stdout)
            self.assertEqual(old_audit.get("disposition"), "PASS_FINITE_CONTRACT_ONLY")


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]])
