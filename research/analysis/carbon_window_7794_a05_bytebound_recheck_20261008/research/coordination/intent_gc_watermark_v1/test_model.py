import unittest

from model import IdOnlyLedger, Receipt, WatermarkLedger

C = "content-C"
A1 = Receipt("A", 1, 1, 2, C, 1)
B2 = Receipt("B", 2, 2, 3, C, 2)
C3 = Receipt("C", 3, 3, 4, C, 3)
A1_ADAPTED = Receipt("A", 1, 4, 5, C, 4)
A4_FRESH = Receipt("A", 4, 4, 5, C, 4)
B2_CHANGED = Receipt("B", 2, 2, 4, C, 2)
SEQ5_GAP = Receipt("D", 5, 4, 5, C, 4)


def fill(ledger):
    for r in (A1, B2, C3):
        assert ledger.apply(r) == "APPLIED"
    return ledger


class LedgerTests(unittest.TestCase):
    def test_id_only_forgets_evicted_identifier(self):
        ledger = fill(IdOnlyLedger(2))
        self.assertEqual(ledger.classify(A1), "NEW_INTENT_ALLOWED")
        self.assertEqual(ledger.classify(A1_ADAPTED), "NEW_INTENT_ALLOWED")
        self.assertEqual(ledger.apply(A1_ADAPTED), "APPLIED")
        self.assertEqual(ledger.generation, 5)

    def test_watermark_rejects_expired_exact_and_changed_replay(self):
        ledger = fill(WatermarkLedger(2))
        self.assertEqual(ledger.retired_through_seq, 1)
        self.assertEqual(ledger.classify(A1), "EXPIRED_INTENT")
        self.assertEqual(ledger.classify(A1_ADAPTED), "EXPIRED_INTENT")
        self.assertEqual(ledger.generation, 4)

    def test_fresh_sequence_reuses_label_and_applies(self):
        ledger = fill(WatermarkLedger(2))
        self.assertEqual(ledger.classify(A4_FRESH), "NEW_INTENT_ALLOWED")
        self.assertEqual(ledger.apply(A4_FRESH), "APPLIED")
        self.assertEqual(ledger.generation, 5)
        self.assertEqual(ledger.retired_through_seq, 2)
        self.assertEqual([r.intent_seq for r in ledger.history], [3, 4])

    def test_retained_same_instance_changed_content_conflicts(self):
        ledger = fill(WatermarkLedger(2))
        self.assertEqual(ledger.classify(B2_CHANGED), "CONFLICT_INTENT_CONTENT")

    def test_sequence_gap_rejected(self):
        ledger = fill(WatermarkLedger(2))
        self.assertEqual(ledger.classify(SEQ5_GAP), "SEQUENCE_GAP")

    def test_retirement_state_is_scalar_and_history_bounded(self):
        ledger = fill(WatermarkLedger(2))
        snap = ledger.snapshot()
        self.assertEqual(snap["retirement_state_shape"], "scalar")
        self.assertEqual(len(snap["history"]), 2)
        self.assertIsInstance(snap["retired_through_seq"], int)


if __name__ == "__main__":
    unittest.main()
