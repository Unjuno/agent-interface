"""Mutation checks for the independent retained-result auditor."""
import copy
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from audit import audit_payload, sha256


class RetainedAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = json.loads((HERE / "results/candidate_raw.json").read_text())
        cls.freeze = json.loads((HERE / "FREEZE.json").read_text())
        cls.source_sha = sha256(HERE.parent / "map01_overlap_controller_v39.py")

    def test_retained_result_passes(self):
        result = audit_payload(self.raw, self.freeze, self.source_sha)
        self.assertEqual(result["audit"], "PASS_METHOD_SCOPED")
        self.assertEqual(result["checks_passed"], 13)

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


if __name__ == "__main__":
    unittest.main(verbosity=2)
