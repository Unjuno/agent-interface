import copy
import unittest

import candidate


class RealReceiptInterpretationTests(unittest.TestCase):
    def test_healthy_and_closed_both_controls_do_not_receive_fault_blame(self):
        for case_id in ("request-healthy", "notification-healthy",
                        "request-closed_both", "notification-closed_both"):
            with self.subTest(case_id=case_id):
                row = candidate.evaluate_case(candidate.load_case(case_id))
                self.assertEqual(row["blame"], "NONE")
                self.assertIn(row["mechanism"], {"EXPECTED_RETURN", "EXPECTED_CLOSED_TRANSPORT_ERROR"})

    def test_deadline_receipt_localizes_read_mechanism_but_abstains_from_fault_blame(self):
        for case_id in ("request-stderr_retained-local", "notification-stderr_retained-local"):
            with self.subTest(case_id=case_id):
                row = candidate.evaluate_case(candidate.load_case(case_id))
                self.assertEqual(row["mechanism"], "DEADLINE_EXPIRED_DURING_DIAGNOSTIC_READ")
                self.assertEqual(row["mechanism_boundary"], "APP_SERVER_CLIENT_DIAGNOSTIC_READ")
                self.assertEqual(row["blame"], "UNLOCALIZED")
                self.assertIsNone(row["blamed_component"])

    def test_uninstrumented_retained_stderr_is_not_upgraded_to_deadline_breach(self):
        row = candidate.evaluate_case(candidate.load_case("request-stderr_retained"))
        self.assertEqual(row["mechanism"], "BLOCKED_DIAGNOSTIC_READ_OBSERVED")
        self.assertEqual(row["blame"], "UNLOCALIZED")


if __name__ == "__main__":
    unittest.main()
