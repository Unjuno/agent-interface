import unittest

from .matrix_gate import CASES, EXPECTED, audit_order, gate


def receipt(case):
    item = {
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
        "replay_allowed": False,
    }
    if case == "AMBIGUOUS_DELIVERY":
        item["delivery"] = {"status": "ambiguous", "reason": "delivery_not_observable"}
    if case == "TERMINAL_CLEANUP_FAILURE":
        item["cleanup"] = {
            "status": "failed",
            "failure_reason": "fixture_release_ack_timeout",
            "release_verified": True,
        }
    return item


class FormalMatrixGateTests(unittest.TestCase):
    def test_fixed_order_and_outcome_distinctions(self):
        receipts = [receipt(case) for case in CASES]
        self.assertEqual(audit_order(receipts), (True, "fixed_order"))
        self.assertEqual(
            tuple(gate(item).outcome for item in receipts),
            tuple(EXPECTED[case] for case in CASES),
        )
        self.assertTrue(all(gate(item).ready for item in receipts))

    def test_wrong_order_is_not_acceptance(self):
        receipts = [receipt(case) for case in reversed(CASES)]
        self.assertEqual(audit_order(receipts), (False, "case_order"))

    def test_ambiguous_requires_explicit_no_replay_evidence(self):
        item = receipt("AMBIGUOUS_DELIVERY")
        self.assertTrue(gate(item).ready)
        self.assertEqual(gate(item).reason, "ambiguous_no_replay")
        item.pop("delivery")
        self.assertFalse(gate(item).ready)
        item = receipt("AMBIGUOUS_DELIVERY")
        item["replay_count"] = 1
        self.assertEqual(gate(item).reason, "ambiguous_replay")

    def test_cleanup_failure_requires_failure_and_release_truth(self):
        item = receipt("TERMINAL_CLEANUP_FAILURE")
        self.assertTrue(gate(item).ready)
        item["cleanup"].pop("failure_reason")
        self.assertFalse(gate(item).ready)
        item = receipt("TERMINAL_CLEANUP_FAILURE")
        item["cleanup"]["release_verified"] = False
        self.assertEqual(gate(item).reason, "cleanup_release_truth")


if __name__ == "__main__":
    unittest.main()
