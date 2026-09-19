import unittest

from model import IncarnationFencedLedger, Receipt, ResettableSequenceLedger


def r(inc, label, seq, f, t, rev):
    return Receipt(inc, label, seq, f, t, "content-C", rev)


class LedgerTests(unittest.TestCase):
    def test_reset_baseline_revives_seq_one(self):
        x = ResettableSequenceLedger(2)
        for rec in (r(1, "A", 1, 1, 2, 1), r(1, "B", 2, 2, 3, 2), r(1, "C", 3, 3, 4, 3)):
            self.assertEqual(x.apply(rec), "APPLIED")
        x.restart_reset_namespace()
        replay = r(1, "A", 1, 4, 5, 4)
        self.assertEqual(x.classify(replay), "NEW_INTENT_ALLOWED")
        self.assertEqual(x.apply(replay), "APPLIED")
        self.assertEqual(x.generation, 5)

    def test_old_incarnation_rejected_after_install(self):
        x = IncarnationFencedLedger(1, 2)
        for rec in (r(1, "A", 1, 1, 2, 1), r(1, "B", 2, 2, 3, 2), r(1, "C", 3, 3, 4, 3)):
            self.assertEqual(x.apply(rec), "APPLIED")
        self.assertEqual(x.install_incarnation(2), "INCARNATION_INSTALLED")
        self.assertEqual(x.classify(r(1, "A", 1, 4, 5, 4)), "STALE_ISSUER_INCARNATION")
        self.assertEqual(x.writes, 3)

    def test_new_incarnation_seq_one_allowed(self):
        x = IncarnationFencedLedger(1, 2)
        for rec in (r(1, "A", 1, 1, 2, 1), r(1, "B", 2, 2, 3, 2), r(1, "C", 3, 3, 4, 3)):
            x.apply(rec)
        x.install_incarnation(2)
        fresh = r(2, "A", 1, 4, 5, 4)
        self.assertEqual(x.classify(fresh), "NEW_INTENT_ALLOWED")
        self.assertEqual(x.apply(fresh), "APPLIED")

    def test_retained_same_instance_changed_content_conflicts(self):
        x = IncarnationFencedLedger(2, 2)
        fresh = r(2, "A", 1, 1, 2, 1)
        self.assertEqual(x.apply(fresh), "APPLIED")
        changed = r(2, "A", 1, 2, 3, 2)
        self.assertEqual(x.classify(changed), "CONFLICT_INTENT_CONTENT")

    def test_future_incarnation_is_not_auto_installed(self):
        x = IncarnationFencedLedger(2, 2)
        self.assertEqual(x.classify(r(3, "A", 1, 1, 2, 1)), "UNINSTALLED_ISSUER_INCARNATION")

    def test_sequence_gap_fails_closed(self):
        x = IncarnationFencedLedger(2, 2)
        self.assertEqual(x.classify(r(2, "B", 2, 1, 2, 1)), "SEQUENCE_GAP")

    def test_nonconsecutive_incarnation_install_rejected(self):
        x = IncarnationFencedLedger(1, 2)
        self.assertEqual(x.install_incarnation(3), "INCARNATION_INSTALL_REJECTED")
        self.assertEqual(x.current_incarnation, 1)
