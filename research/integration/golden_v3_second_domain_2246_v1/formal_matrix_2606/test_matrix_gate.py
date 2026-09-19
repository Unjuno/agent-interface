import unittest

from .matrix_gate import CASES, EXPECTED, audit_order, gate


def receipt(case):
    return {
        "case": case,
        "session_id": "gtk-formal-session",
        "window_id": "0x42",
        "observation_revision": 3,
        "binding_revision": 3,
        "input_ledger": [],
        "effect_receipt": {"artifact_sha256": "a" * 64},
        "cleanup": {"status": "clean"},
        "authority_grants": 0,
        "replay_count": 0,
    }


class FormalMatrixGateTests(unittest.TestCase):
    def test_fixed_order_and_outcome_distinctions(self):
        receipts = [receipt(case) for case in CASES]
        self.assertEqual(audit_order(receipts), (True, "fixed_order"))
        self.assertEqual(
            tuple(gate(item).outcome for item in receipts),
            tuple(EXPECTED[case] for case in CASES),
        )

    def test_wrong_order_is_not_acceptance(self):
        receipts = [receipt(case) for case in reversed(CASES)]
        self.assertEqual(audit_order(receipts), (False, "case_order"))

    def test_ambiguous_delivery_cannot_replay(self):
        item = receipt("AMBIGUOUS_DELIVERY")
        self.assertFalse(gate(item).ready)
        self.assertEqual(gate(item).reason, "ambiguous_no_replay")
        item["replay_count"] = 1
        self.assertEqual(gate(item).reason, "ambiguous_replay")

    def test_cleanup_failure_is_not_success(self):
        item = receipt("TERMINAL_CLEANUP_FAILURE")
        item["cleanup"] = {"status": "failed"}
        result = gate(item)
        self.assertFalse(result.ready)
        self.assertEqual(result.outcome, "CLEANUP_FAILURE")


if __name__ == "__main__":
    unittest.main()
