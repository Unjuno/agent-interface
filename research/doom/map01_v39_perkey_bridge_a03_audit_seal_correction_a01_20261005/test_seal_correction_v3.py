from __future__ import annotations
import hashlib
import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
A03 = HERE.parent / "map01_v39_perkey_bridge_a03_down_cleanup_race_20261005"
V2_FREEZE = A03 / "FREEZE-AUDIT-V2.json"
V2_TEST = A03 / "test_a03_v2.py"
V3_FREEZE = HERE / "FREEZE-AUDIT-V3.json"

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

class AuditSealCorrectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.freeze = json.loads(V3_FREEZE.read_text(encoding="utf-8"))
        cls.prior = json.loads(V2_FREEZE.read_text(encoding="utf-8"))

    def test_v3_binds_exact_retained_v2_test_bytes(self):
        self.assertEqual(V2_TEST.stat().st_size, self.freeze["test_source_bytes"])
        self.assertEqual(sha256(V2_TEST), self.freeze["test_source_sha256"])
        self.assertEqual(sha256(V2_FREEZE), self.freeze["predecessor_freeze_sha256"])
        validator = HERE / "test_seal_correction_v3.py"
        self.assertEqual(validator.stat().st_size, self.freeze["validator_source_bytes"])
        self.assertEqual(sha256(validator), self.freeze["validator_source_sha256"])

    def test_v2_mismatch_is_retained_and_explicitly_superseded(self):
        actual = sha256(V2_TEST)
        self.assertEqual(self.prior["test_source_sha256"], self.freeze["superseded_v2_claim_sha256"])
        self.assertNotEqual(self.prior["test_source_sha256"], actual)
        self.assertEqual(actual, self.freeze["test_source_sha256"])
        self.assertEqual(self.freeze["supersedes"], "FREEZE-AUDIT-V2.json")
        self.assertEqual(self.freeze["candidate_invocations"], 0)
        self.assertEqual(self.freeze["scope"], "audit-seal correction only; retained candidate/raw/result/freeze are unchanged")

if __name__ == "__main__":
    unittest.main(verbosity=2)
