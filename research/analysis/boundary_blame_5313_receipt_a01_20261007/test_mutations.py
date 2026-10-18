import copy
import unittest

import candidate


class ReceiptContradictionControls(unittest.TestCase):
    def setUp(self):
        self.case = candidate.load_case("request-stderr_retained-local")

    def test_source_identity_conflict_forces_unlocalized(self):
        case = copy.deepcopy(self.case)
        case["result"]["source_sha256"] = "0" * 64
        row = candidate.evaluate_case(case)
        self.assertEqual(row["blame"], "UNLOCALIZED")
        self.assertIsNone(row["blamed_component"])

    def test_receipt_child_stream_conflict_forces_unlocalized(self):
        case = copy.deepcopy(self.case)
        case["child_events"][1]["stderr_closed"] = True
        row = candidate.evaluate_case(case)
        self.assertEqual(row["blame"], "UNLOCALIZED")
        self.assertIsNone(row["blamed_component"])

    def test_wrong_stack_frame_forces_unlocalized(self):
        case = copy.deepcopy(self.case)
        case["result"]["checkpoint"]["stack"][0]["line"] += 1
        row = candidate.evaluate_case(case)
        self.assertEqual(row["blame"], "UNLOCALIZED")
        self.assertIsNone(row["blamed_component"])

    def test_missing_local_deadline_forces_unlocalized(self):
        case = copy.deepcopy(self.case)
        del case["result"]["checkpoint"]["local_deadline"]
        row = candidate.evaluate_case(case)
        self.assertEqual(row["mechanism"], "EVIDENCE_CONFLICT_OR_INCOMPLETE")
        self.assertEqual(row["blame"], "UNLOCALIZED")

    def test_missing_request_journal_forces_evidence_conflict(self):
        case = copy.deepcopy(self.case)
        case["journal"] = []
        row = candidate.evaluate_case(case)
        self.assertEqual(row["mechanism"], "EVIDENCE_CONFLICT_OR_INCOMPLETE")
        self.assertEqual(row["blame"], "UNLOCALIZED")

    def test_notification_journal_rejects_unexpected_outbound_message(self):
        case = candidate.load_case("notification-healthy")
        case["journal"].append({"direction": "sent", "message": {"method": "forged"}})
        row = candidate.evaluate_case(case)
        self.assertEqual(row["mechanism"], "EVIDENCE_CONFLICT_OR_INCOMPLETE")
        self.assertEqual(row["blame"], "UNLOCALIZED")


if __name__ == "__main__":
    unittest.main()
