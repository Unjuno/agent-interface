import copy
import json
import unittest
from pathlib import Path

from audit_stdlib import audit, audit_bytes


ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "intent_alignment_3442_pilot_01" / "RESULT.json"


class AuditStdlibTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = RESULT.read_bytes()
        cls.obj = json.loads(cls.raw)

    def test_unchanged_result_reconstructs_recorded_hold(self):
        out = audit_bytes(self.raw, __import__("hashlib").sha256(self.raw).hexdigest())
        self.assertEqual(out["audit"], "PASS", out)
        self.assertEqual(out["decision_recomputed"], "HOLD_OR_FAIL_GATE_MISS")

    def test_wrong_result_digest_is_rejected(self):
        out = audit_bytes(self.raw, "0" * 64)
        self.assertEqual(out["errors"], ["result_sha256_mismatch"])

    def test_altered_retained_prediction_is_rejected(self):
        obj = copy.deepcopy(self.obj)
        obj["test_rows"][0][3] = (obj["test_rows"][0][3] + 1) % 4
        self.assertIn("baseline_predictions_not_reproduced", audit(obj)["errors"])

    def test_forged_gate_is_rejected(self):
        obj = copy.deepcopy(self.obj)
        obj["gates"]["conditioned_accuracy_ge_0_95"] = True
        self.assertIn("gate_mismatch", audit(obj)["errors"])

    def test_forged_outcome_is_rejected(self):
        obj = copy.deepcopy(self.obj)
        obj["outcome"] = "PASS_INTENT_CONDITIONING_SYNTHETIC_SCOPED"
        self.assertIn("outcome_mismatch", audit(obj)["errors"])

    def test_pair_order_corruption_is_rejected(self):
        obj = copy.deepcopy(self.obj)
        obj["test_rows"][0], obj["test_rows"][1] = obj["test_rows"][1], obj["test_rows"][0]
        self.assertTrue(any("paired_" in error for error in audit(obj)["errors"]))


if __name__ == "__main__":
    unittest.main()
