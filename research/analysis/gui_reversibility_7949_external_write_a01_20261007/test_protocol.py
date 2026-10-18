import json
import unittest
from pathlib import Path

import candidate

ROOT = Path(__file__).parent


class ProtocolTests(unittest.TestCase):
    def setUp(self):
        self.model = json.loads((ROOT / "model.json").read_text(encoding="utf-8"))

    def test_frozen_case_dispositions(self):
        rows = {r["case_id"]: r for r in candidate.run(self.model)}
        self.assertEqual(len(rows), 10)
        self.assertEqual(rows["disjoint_y_write"]["compensation"]["fields_after"], {"x": 0, "y": 9})
        self.assertTrue(rows["disjoint_y_write"]["blind_inverse"]["lost_disjoint_y"])
        self.assertEqual(rows["disjoint_y_write"]["whole_object"], "CONFLICT")
        for cid in ("same_field_write", "aba_same_final_value", "object_replaced"):
            self.assertIsNone(rows[cid]["compensation"])
        for cid in ("sequence_gap", "out_of_order", "incomplete_coverage", "snapshot_mismatch", "unjournaled_revision"):
            self.assertEqual(rows[cid]["disposition"], "UNKNOWN")
            self.assertIsNone(rows[cid]["compensation"])

    def test_snapshot_mutation_yields_unknown(self):
        case = next(c for c in self.model["cases"] if c["id"] == "disjoint_y_write")
        changed = json.loads(json.dumps(case))
        changed["snapshot"]["fields"]["y"] = 0
        self.assertEqual(candidate.evaluate(changed, self.model)["disposition"], "UNKNOWN")

    def test_gap_mutation_yields_unknown(self):
        case = next(c for c in self.model["cases"] if c["id"] == "disjoint_y_write")
        changed = json.loads(json.dumps(case))
        changed["events"][0]["seq"] = 2
        self.assertEqual(candidate.evaluate(changed, self.model)["disposition"], "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
