import copy
import unittest

import audit_core
import candidate


def built_raw():
    rows = []
    for case_id in candidate.CASE_IDS:
        case = candidate.load_case(case_id)
        decision = candidate.evaluate_case(case)
        rows.append({"id": case_id, "input_sha256": case["input_hashes"],
                     "classification": {k: v for k, v in decision.items() if k != "id"}})
    return {"cases": rows, "formal_native_or_model_replays": 0}


class IndependentAuditMutationTests(unittest.TestCase):
    def test_independent_reader_accepts_current_receipt_evaluations(self):
        result = audit_core.audit(built_raw())
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["case_count"], 8)
        self.assertEqual(result["scoped_mechanism_localization"], 2)
        self.assertEqual(result["unsafe_component_blames"], 0)

    def test_auditor_rejects_forged_component_blame(self):
        raw = built_raw()
        raw["cases"][6]["classification"]["blame"] = "BACKEND_NONCONFORMANCE"
        raw["cases"][6]["classification"]["blamed_component"] = "child"
        result = audit_core.audit(raw)
        self.assertEqual(result["status"], "FAIL")
        self.assertIn("request-stderr_retained-local:classification_mismatch", result["errors"])

    def test_auditor_rejects_missing_case_and_changed_input_identity(self):
        raw = built_raw()
        raw["cases"].pop()
        self.assertIn("case_roster_or_order", audit_core.audit(raw)["errors"])
        raw = built_raw()
        raw["cases"][0]["input_sha256"] = {}
        self.assertIn("request-healthy:input_sha256_mismatch", audit_core.audit(raw)["errors"])

    def test_auditor_rejects_changed_retained_receipt_byte(self):
        raw = built_raw()
        key = "research/live_control/appserver_closed_diagnostic_59_20261003_01a0ff52/construction01/request-healthy/result.json"
        raw["cases"][0]["input_sha256"][key] = "0" * 64
        result = audit_core.audit(raw)
        self.assertEqual(result["status"], "FAIL")
        self.assertIn("request-healthy:input_sha256_mismatch", result["errors"])


if __name__ == "__main__":
    unittest.main()
