import copy
import json
import unittest
from pathlib import Path

import audit
import candidate

ROOT = Path(__file__).parent
VISIBLE = json.loads((ROOT / "visible.json").read_text())
TRUTH = json.loads((ROOT / "truth.json").read_text())


class T0Tests(unittest.TestCase):
    def result(self, visible=VISIBLE):
        return {"cases": {c["case_id"]: candidate.decide(c) for c in visible["cases"]}}

    def full_candidate(self):
        return {"schema": "pending-route-candidate-v1", "checkpoint": VISIBLE["update_time"], **self.result()}

    def test_five_frozen_case_expectations(self):
        result = self.result()
        for case_id, row in TRUTH["cases"].items():
            self.assertEqual(result["cases"][case_id]["classification"], row["expected"])

    def test_pending_retained_as_interval(self):
        result = self.result()
        self.assertEqual(result["cases"]["all_pending_initial_period"]["bounds"]["ROUTE_I"]["lower"], "0")
        self.assertEqual(result["cases"]["all_pending_initial_period"]["bounds"]["ROUTE_I"]["upper"], "1")

    def test_auditor_rejects_mutated_classification(self):
        got = self.full_candidate()
        got["cases"]["fast_receipt_complete_case_inversion"]["classification"] = "SELECT:FAST_ACK"
        audit_result = audit.audit(VISIBLE, TRUTH, got)
        self.assertEqual(audit_result["status"], "FAIL")

    def test_auditor_rejects_mutated_bounds(self):
        got = self.full_candidate()
        got["cases"]["all_pending_initial_period"]["bounds"]["ROUTE_I"]["upper"] = "0"
        self.assertEqual(audit.audit(VISIBLE, TRUTH, got)["status"], "FAIL")

    def test_auditor_passes_unmodified_candidate(self):
        self.assertEqual(audit.audit(VISIBLE, TRUTH, self.full_candidate())["status"], "PASS_METHOD_SCOPED")


if __name__ == "__main__":
    unittest.main()
