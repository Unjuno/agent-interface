import copy
import json
import unittest
from pathlib import Path

from audit import audit
from candidate import preflight


class RawAuditTests(unittest.TestCase):
    def setUp(self):
        self.cases = json.loads((Path(__file__).parent / "cases.json").read_text())
        self.raw = {"schema": "verifier_registry_raw.v5", "rows": [
            {**case, "observed": preflight(case["ir"], case["assignments"],
                                           case["registry_snapshot"], case["resources"])}
            for case in self.cases
        ]}

    def test_raw_rows_are_recomputed_from_frozen_inputs_without_candidate_import(self):
        self.assertEqual(audit(self.raw, self.cases), {
            "status": "PASS_HOST_CONSTRUCTION_ONLY", "cases": 7, "dispatch_count": 0,
        })

    def test_changed_observed_decision_is_rejected(self):
        raw = copy.deepcopy(self.raw)
        raw["rows"][1]["observed"]["decisions"][0]["status"] = "UNAVAILABLE"
        with self.assertRaisesRegex(ValueError, "disagrees"):
            audit(raw, self.cases)

    def test_changed_raw_assignment_is_rejected_against_frozen_case(self):
        raw = copy.deepcopy(self.raw)
        raw["rows"][1]["assignments"][0]["estimated_cost"] = 1
        with self.assertRaisesRegex(ValueError, "differs"):
            audit(raw, self.cases)


if __name__ == "__main__":
    unittest.main()
