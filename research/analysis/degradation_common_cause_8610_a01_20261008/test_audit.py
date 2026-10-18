import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


HERE = Path(__file__).parent


class IndependentDegradationAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temporary.name)
        cls.spec_path = HERE / "spec.json"
        cls.candidate_path = cls.root / "candidate.json"
        run = subprocess.run(
            [sys.executable, str(HERE / "candidate.py"), "--spec", str(cls.spec_path), "--output", str(cls.candidate_path)],
            capture_output=True,
            text=True,
        )
        if run.returncode != 0:
            raise AssertionError(run.stderr)
        cls.specification = json.loads(cls.spec_path.read_text(encoding="utf-8"))
        cls.candidate = json.loads(cls.candidate_path.read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def run_audit(self, candidate):
        source = self.root / "candidate-mutated.json"
        output = self.root / "audit.json"
        source.write_text(json.dumps(candidate), encoding="utf-8")
        if output.exists():
            output.unlink()
        return subprocess.run(
            [sys.executable, str(HERE / "auditor.py"), "--spec", str(self.spec_path), "--candidate", str(source), "--output", str(output)],
            capture_output=True,
            text=True,
        ), output

    def test_auditor_reconstructs_safe_incremental_modes_and_rejects_unsafe_control(self):
        run, output = self.run_audit(self.candidate)
        self.assertEqual(run.returncode, 0, run.stderr)
        result = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(result["audit_integrity"], "PASS")
        self.assertEqual(result["cases_reconstructed"], 9)
        self.assertEqual(result["additional_supported_outcomes"], 11)
        self.assertEqual(result["unsafe_control_rejections"], 3)
        self.assertEqual(result["authority_inflation"], 0)
        self.assertEqual(result["false_effect_claims"], 0)
        self.assertEqual(result["release_obligations_verified"], 9)
        self.assertEqual(result["dispatches"], 0)

    def test_rejects_missing_supported_contract_operation(self):
        altered = copy.deepcopy(self.candidate)
        altered["cases"][1]["contract"].pop()
        run, _ = self.run_audit(altered)
        self.assertNotEqual(run.returncode, 0)

    def test_rejects_stale_semantics_admitted_as_fresh(self):
        altered = copy.deepcopy(self.candidate)
        row = {"operation": "present_semantics", "source": "semantic_observation", "claim": "SEMANTIC_VERIFIED", "freshness": "CURRENT"}
        altered["cases"][6]["contract"].append(row)
        run, _ = self.run_audit(altered)
        self.assertNotEqual(run.returncode, 0)

    def test_rejects_false_effect_claim_and_hidden_raw_fallback(self):
        altered = copy.deepcopy(self.candidate)
        altered["cases"][0]["contract"][0]["claim"] = "EFFECT_VERIFIED"
        run, _ = self.run_audit(altered)
        self.assertNotEqual(run.returncode, 0)
        altered = copy.deepcopy(self.candidate)
        altered["cases"][0]["contract"][1]["source"] = "raw_observation"
        run, _ = self.run_audit(altered)
        self.assertNotEqual(run.returncode, 0)

    def test_rejects_authority_enlargement_and_lost_release_obligation(self):
        altered = copy.deepcopy(self.candidate)
        altered["cases"][0]["contract"].append({"operation": "dispatch_action", "source": "planner", "claim": "ACTION_AUTHORIZED", "freshness": "CURRENT"})
        run, _ = self.run_audit(altered)
        self.assertNotEqual(run.returncode, 0)
        altered = copy.deepcopy(self.candidate)
        altered["cases"][7]["release_obligation"] = "NONE"
        run, _ = self.run_audit(altered)
        self.assertNotEqual(run.returncode, 0)


if __name__ == "__main__":
    unittest.main()
