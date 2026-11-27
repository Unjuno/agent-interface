"""Mutation checks for the independent retained-result auditor."""
import copy
import hashlib
import importlib.util
import json
import subprocess
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("retained_health_boundary_audit", HERE / "audit.py")
auditor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(auditor)
audit_payload, sha256 = auditor.audit_payload, auditor.sha256


class RetainedAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = json.loads((HERE / "results/candidate_raw.json").read_text())
        cls.freeze = json.loads((HERE / "FREEZE.json").read_text())
        # These tests audit a saved historical result, not today's controller.
        source = subprocess.check_output(
            ["git", "show", cls.freeze["base_commit"] +
             ":research/doom/map01_overlap_controller_v39.py"], cwd=HERE)
        cls.source_sha = hashlib.sha256(source).hexdigest()

    def test_retained_result_passes(self):
        result = audit_payload(self.raw, self.freeze, self.source_sha)
        self.assertEqual(result["audit"], "PASS_METHOD_SCOPED")
        self.assertEqual(result["checks_passed"], 13)

    def test_wrong_source_identity_rejected(self):
        with self.assertRaisesRegex(ValueError, "frozen controller equals inspected source"):
            audit_payload(self.raw, self.freeze, "0" * 64)

    def test_threshold_mutation_rejected(self):
        raw = copy.deepcopy(self.raw)
        raw["hard_minimum"] = 87
        with self.assertRaisesRegex(ValueError, "source health and effective floor"):
            audit_payload(raw, self.freeze, self.source_sha)

    def test_observation_order_mutation_rejected(self):
        raw = copy.deepcopy(self.raw)
        raw["observations"].reverse()
        with self.assertRaisesRegex(ValueError, "ordered boundary observations"):
            audit_payload(raw, self.freeze, self.source_sha)

    def test_release_mutation_rejected(self):
        raw = copy.deepcopy(self.raw)
        raw["cover_terminal"]["release"]["keys_down"] = ["fire"]
        with self.assertRaisesRegex(ValueError, "matching terminal and verified empty release"):
            audit_payload(raw, self.freeze, self.source_sha)

    def test_final_admission_authority_mutations_rejected(self):
        ready = copy.deepcopy(self.raw)
        ready["final_admission"]["status"] = "READY_FOR_ACTION_VALIDITY"
        with self.assertRaisesRegex(ValueError, "final gate rejects invalidated answer"):
            audit_payload(ready, self.freeze, self.source_sha)

        authorized = copy.deepcopy(self.raw)
        authorized["final_admission"]["input_authority_admitted"] = True
        with self.assertRaisesRegex(ValueError, "final gate rejects invalidated answer"):
            audit_payload(authorized, self.freeze, self.source_sha)


if __name__ == "__main__":
    unittest.main(verbosity=2)
