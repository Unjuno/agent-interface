import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
import candidate


class A03Tests(unittest.TestCase):
    def test_repeated_disjoint_write(self):
        model = json.loads((ROOT / "model.json").read_text(encoding="utf-8"))
        rows = {r["case_id"]: r for r in candidate.run(model)}
        self.assertEqual(len(rows), 11)
        self.assertEqual(rows["two_disjoint_writes"]["compensation"]["fields_after"], {"x": 0, "y": 11})
        self.assertTrue(rows["two_disjoint_writes"]["blind_inverse"]["lost_disjoint_y"])
        self.assertEqual(rows["two_disjoint_writes"]["whole_object"], "CONFLICT")
        self.assertIs(rows["two_disjoint_writes"]["compensation"]["claims_exact_rollback"], False)

    def test_integrity_anomalies_unknown(self):
        model = json.loads((ROOT / "model.json").read_text(encoding="utf-8"))
        rows = {r["case_id"]: r for r in candidate.run(model)}
        for cid in ("sequence_gap", "out_of_order", "incomplete_coverage", "snapshot_mismatch", "unjournaled_revision"):
            self.assertEqual(rows[cid]["disposition"], "UNKNOWN")
            self.assertIsNone(rows[cid]["compensation"])


if __name__ == "__main__":
    unittest.main()
