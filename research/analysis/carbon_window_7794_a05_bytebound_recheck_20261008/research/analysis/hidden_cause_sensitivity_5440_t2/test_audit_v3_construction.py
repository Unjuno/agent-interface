import json
import unittest
from pathlib import Path

from audit_v3 import expected_rows


class AuditConstructionTests(unittest.TestCase):
    def test_expected_rows_preserve_pair_and_world_structure(self):
        spec = json.loads((Path(__file__).parent / "cases.json").read_bytes())
        rows, truth = expected_rows(spec)
        self.assertEqual(len(rows), 20)
        self.assertEqual(len(truth), 16)
        complete = [row for row in truth if row["world"] == "complete"]
        omitted = [row for row in truth if row["world"] == "omitted"]
        self.assertEqual(sum(row["reversal"] for row in complete), 0)
        self.assertEqual(sum(row["reversal"] for row in omitted), 8)
        self.assertEqual(sum(row["decision"] == "UNIDENTIFIED" for row in omitted), 8)

    def test_expected_control_modes_are_all_present(self):
        spec = json.loads((Path(__file__).parent / "cases.json").read_bytes())
        rows, _ = expected_rows(spec)
        for mode in spec["candidate_controls"]:
            self.assertEqual(rows["pair-01:" + mode]["decision"], "UNIDENTIFIED")


if __name__ == "__main__":
    unittest.main(verbosity=2)
