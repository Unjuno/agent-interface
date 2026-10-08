import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("assay_audit", HERE / "audit.py")
auditor = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(auditor)
FIXTURE = json.loads((HERE / "fixtures" / "sequence.json").read_text(encoding="utf-8"))


def candidate_rows():
    with tempfile.TemporaryDirectory() as temp:
        output = Path(temp) / "rendered.json"
        proc = subprocess.run(
            [sys.executable, str(HERE / "candidate.py"), "--input",
             str(HERE / "fixtures" / "sequence.json"), "--output", str(output)],
            capture_output=True, text=True, check=False)
        if proc.returncode:
            raise AssertionError(proc.stderr)
        return json.loads(output.read_text(encoding="utf-8"))


class IndependentAuditConstructionTests(unittest.TestCase):
    def test_clean_candidate_reconstructs_against_fixture_truth(self):
        rendered = candidate_rows()
        result = auditor.audit(FIXTURE, rendered)
        self.assertEqual(result["status"], "PASS_METHOD_SCOPED")
        self.assertEqual(result["baseline_errors"], [])

    def test_all_frozen_corruptions_are_rejected(self):
        rendered = candidate_rows()
        result = auditor.audit(FIXTURE, rendered)
        self.assertEqual(result["mutation_controls"]["total"], 6)
        self.assertEqual(result["mutation_controls"]["rejected"], 6)
        self.assertTrue(all(result["mutation_controls"]["cases"].values()))

    def test_missing_batch_expiry_fails_closed(self):
        rendered = candidate_rows()
        rendered["arms"]["bounded_batch"]["batches"][0]["items"][0]["expiry"] = None
        errors = auditor.discrepancies(FIXTURE, rendered)
        self.assertIn("batch:scope_or_expiry_not_bound_per_effect", errors)


if __name__ == "__main__":
    unittest.main(verbosity=2)
