import sys
import unittest
from pathlib import Path

import audit_successor
import candidate


HERE = Path(__file__).resolve().parent
SIMULATOR = HERE.parent / "safety_backpressure_5372_t1_v1" / "simulate.py"


class SuccessorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = candidate.all_records(SIMULATOR)

    def test_allocation02_uses_frozen_source_and_audits(self):
        self.assertEqual(self.records[0]["allocation"], candidate.ALLOCATION)
        self.assertEqual(audit_successor.audit_successor(self.records), [])

    def test_wrong_allocation_rejected(self):
        rows = [dict(record) for record in self.records]
        rows[0]["allocation"] = "allocation-01"
        self.assertTrue(audit_successor.audit_successor(rows))

    def test_base_gate_corruptions_still_rejected(self):
        rows = [dict(record) for record in self.records]
        target = next(row for row in rows if row["type"] == "safety_done")
        rows.remove(target)
        self.assertTrue(audit_successor.audit_successor(rows))


if __name__ == "__main__":
    unittest.main()
