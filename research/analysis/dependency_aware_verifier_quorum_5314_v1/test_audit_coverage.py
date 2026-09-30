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

    def test_v2_rejects_forged_declared_domains_in_the_frozen_base(self):
        raw = json.loads(json.dumps(self.raw))
        raw["rows"][0]["declared_labels"][0] = "forged-independent-domain"
        result = audit_v2.audit(raw)
        self.assertTrue(any("declared_labels_disagree_with_verified" in error for error in result["discrepancies"]))

    def test_v2_rejects_unknown_metadata_in_the_frozen_base(self):
        raw = json.loads(json.dumps(self.raw))
        raw["rows"][0]["metadata_known"][0] = False
        result = audit_v2.audit(raw)
        self.assertTrue(any("unknown_metadata_in_frozen_universe" in error for error in result["discrepancies"]))

    def test_v2_accepts_the_frozen_raw_after_all_eight_controls_reject(self):
        source_auditor = self.study / "audit_v2.py"
        with tempfile.TemporaryDirectory(prefix="quorum-audit-gate-") as temporary:
            target = Path(temporary)
            shutil.copyfile(source_auditor, target / "audit_v2.py")
            shutil.copyfile(self.study / "raw.json", target / "raw.json")
            result = subprocess.run(
                [sys.executable, str(target / "audit_v2.py")],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            audit = json.loads(result.stdout)
            self.assertEqual(audit["mutation_controls_total"], 8)
            self.assertEqual(audit["disposition"], "PASS_FINITE_CONTRACT_ONLY")

    def test_v2_can_write_successor_output_without_overwriting_prior_audit(self):
        source_auditor = self.study / "audit_v2.py"
        with tempfile.TemporaryDirectory(prefix="quorum-audit-preserve-") as temporary:
            target = Path(temporary)
            script = target / "audit_v2.py"
            raw_path = target / "raw.json"
            prior = target / "audit_v2.json"
            successor = target / "audit_v2_final.json"
            shutil.copyfile(source_auditor, script)
            shutil.copyfile(self.study / "raw.json", raw_path)
            prior.write_text("retained earlier HOLD output", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(script), str(raw_path), str(successor)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(successor.exists())
            self.assertEqual(prior.read_text(encoding="utf-8"), "retained earlier HOLD output")

    def test_all_v2_mutation_controls_reject_the_corruption(self):
        controls = audit_v2.run_controls(self.raw)
        self.assertEqual(len(controls), 8)
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
