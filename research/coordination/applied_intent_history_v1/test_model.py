import unittest
from model import Receipt, SingleSlotLedger, BoundedHistoryLedger

C = "content-C"
A = Receipt("intent-A", 1, 2, C, 1)
B = Receipt("intent-B", 2, 3, C, 2)
C3 = Receipt("intent-C", 3, 4, C, 3)
A_CONFLICT = Receipt("intent-A", 1, 3, C, 1)


class LedgerTests(unittest.TestCase):
    def test_single_slot_overwrites_old_intent(self):
        x = SingleSlotLedger()
        x.apply(A); x.apply(B)
        self.assertEqual(x.recover(A), "UNKNOWN_INTENT_NOT_RETAINED")

    def test_bounded_two_retains_a(self):
        x = BoundedHistoryLedger(capacity=2)
        x.apply(A); x.apply(B)
        self.assertEqual(x.recover(A), "ALREADY_COMMITTED_SELF")

    def test_same_id_changed_content_conflicts(self):
        x = BoundedHistoryLedger(capacity=2)
        x.apply(A); x.apply(B)
        self.assertEqual(x.recover(A_CONFLICT), "CONFLICT_INTENT_CONTENT")

    def test_capacity_two_evicts_a_after_c(self):
        x = BoundedHistoryLedger(capacity=2)
        x.apply(A); x.apply(B); x.apply(C3)
        self.assertEqual(x.recover(A), "UNKNOWN_INTENT_EVICTED")
        self.assertEqual(x.recover(B), "ALREADY_COMMITTED_SELF")

    def test_retained_duplicate_conflict_rejected_on_apply(self):
        x = BoundedHistoryLedger(capacity=2)
        x.apply(A)
        with self.assertRaises(ValueError):
            x.apply(Receipt("intent-A", 2, 3, C, 2))


if __name__ == "__main__":
    unittest.main()
