import copy
import unittest

from audit import audit_candidate


CONTAINER_ID = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
ROWS = [
    {"case_id": "empty-array", "container_id": CONTAINER_ID, "query_exit_code": 0, "raw_response": "[]", "absence_verified": True, "reason": "empty_array"},
    {"case_id": "empty-array-whitespace", "container_id": CONTAINER_ID, "query_exit_code": 0, "raw_response": " [ \n ] ", "absence_verified": True, "reason": "empty_array"},
    {"case_id": "remaining-row", "container_id": CONTAINER_ID, "query_exit_code": 0, "raw_response": '[{"id":"' + CONTAINER_ID + '"}]', "absence_verified": False, "reason": "container_row_remains"},
    {"case_id": "malformed-json", "container_id": CONTAINER_ID, "query_exit_code": 0, "raw_response": "not-json: diagnostic survives", "absence_verified": False, "reason": "cleanup_response_invalid"},
    {"case_id": "query-error", "container_id": CONTAINER_ID, "query_exit_code": 7, "raw_response": "permission denied for exact filter", "absence_verified": False, "reason": "scoped_query_failed"},
    {"case_id": "json-null", "container_id": CONTAINER_ID, "query_exit_code": 0, "raw_response": "null", "absence_verified": False, "reason": "json_null_is_not_empty_array"},
]


class CleanupReceiptAuditTests(unittest.TestCase):
    def test_independent_audit_accepts_the_six_frozen_literal_cases(self):
        report = audit_candidate(ROWS)
        self.assertEqual(report["status"], "PASS_CLEANUP_RECEIPT_CONTRACT_SCOPED")
        self.assertEqual(report["rows"], 6)
        self.assertEqual(report["mutations_rejected"], 4)

    def test_audit_rejects_absence_claim_when_a_row_remains(self):
        rows = copy.deepcopy(ROWS)
        rows[2]["absence_verified"] = True
        with self.assertRaises(ValueError):
            audit_candidate(rows)

    def test_audit_rejects_lost_raw_response(self):
        rows = copy.deepcopy(ROWS)
        rows[3]["raw_response"] = ""
        with self.assertRaises(ValueError):
            audit_candidate(rows)

    def test_audit_rejects_lost_container_identity(self):
        rows = copy.deepcopy(ROWS)
        rows[0]["container_id"] = ""
        with self.assertRaises(ValueError):
            audit_candidate(rows)

    def test_audit_rejects_query_error_as_absence(self):
        rows = copy.deepcopy(ROWS)
        rows[4]["absence_verified"] = True
        with self.assertRaises(ValueError):
            audit_candidate(rows)


if __name__ == "__main__":
    unittest.main()
