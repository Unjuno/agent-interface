from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from test_audit import AuditTests
from audit_v2 import audit


class CorrectedScoringTests(unittest.TestCase):
    def run_fixture(self, mutate):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            AuditTests().make_fixture(root)
            mutate(root)
            return audit(root)

    def test_one_valid_low_iou_box_is_a_scored_miss_and_gate_still_passes(self):
        def mutate(root):
            path = root / "formal" / "positive-01.json"
            record = json.loads(path.read_text())
            record["response"]["message"]["content"] = json.dumps({"present": True, "box": [30, 30, 40, 40]})
            path.write_text(json.dumps(record))
        result = self.run_fixture(mutate)
        self.assertEqual(result["decision"], "PASS_DIAGNOSTIC_SCOPED")
        self.assertEqual(result["positive_hits"], 5)
        self.assertEqual(result["errors"], [])

    def test_two_valid_low_iou_boxes_fail_capability_gate(self):
        def mutate(root):
            for case_id in ("positive-01", "positive-02"):
                path = root / "formal" / f"{case_id}.json"
                record = json.loads(path.read_text())
                record["response"]["message"]["content"] = json.dumps({"present": True, "box": [30, 30, 40, 40]})
                path.write_text(json.dumps(record))
        result = self.run_fixture(mutate)
        self.assertEqual(result["decision"], "FAIL_EASY_LAYOUT_CAPABILITY_NOT_ESTABLISHED")
        self.assertEqual(result["positive_hits"], 4)

    def test_malformed_positive_box_remains_a_hold(self):
        def mutate(root):
            path = root / "formal" / "positive-01.json"
            record = json.loads(path.read_text())
            record["response"]["message"]["content"] = json.dumps({"present": True, "box": [30, 30, 20, 40]})
            path.write_text(json.dumps(record))
        result = self.run_fixture(mutate)
        self.assertEqual(result["decision"], "HOLD_AUDIT_OR_GPU_GATE")
        self.assertIn("positive_box_malformed:positive-01", result["errors"])


if __name__ == "__main__":
    unittest.main(verbosity=2)

