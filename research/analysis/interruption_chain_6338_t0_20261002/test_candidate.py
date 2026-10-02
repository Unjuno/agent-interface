import unittest
from candidate import run_policy
from cases import CASES


class CandidateConstructionTests(unittest.TestCase):
    def case(self, name):
        return next(c for c in CASES["cases"] if c["id"] == name)

    def test_exogenous_burst_remains_unlinked_under_all_real_policies(self):
        c = self.case("exogenous_burst")
        for policy in ("emit_each", "duplicate_batch", "source_linked"):
            row = run_policy(c, policy)
            self.assertEqual(row["notice_count"], 3)
            self.assertEqual(sum(e.get("parent") is not None for e in c["events"]), 0)

    def test_source_linked_reduces_only_same_scope_revision(self):
        c = self.case("two_generation_chain")
        emitted = run_policy(c, "emit_each")
        linked = run_policy(c, "source_linked")
        self.assertEqual(emitted["notice_count"], 3)
        self.assertEqual(linked["notice_count"], 2)
        self.assertEqual((emitted["max_card_chain_length"], linked["max_card_chain_length"]), (3, 2))
        self.assertEqual(emitted["trace_span_to_quiescence"], linked["trace_span_to_quiescence"])

    def test_exact_duplicate_batch_does_not_merge_revised_target(self):
        self.assertEqual(run_policy(self.case("identical_duplicates"), "duplicate_batch")["notice_count"], 1)
        self.assertEqual(run_policy(self.case("target_revision"), "duplicate_batch")["notice_count"], 2)

    def test_cross_principal_attempt_is_not_delivered(self):
        row = run_policy(self.case("cross_principal_attempt"), "source_linked")
        self.assertIsNone(row["event_card"]["p1"])
        self.assertEqual(row["notice_count"], 1)

    def test_hard_alerts_are_never_deduplicated(self):
        row = run_policy(self.case("urgent_hard_alert"), "duplicate_batch")
        self.assertEqual(row["hard_alert_count"], 2)

    def test_opaque_control_reduces_cards_but_loses_correctness(self):
        c = self.case("opaque_negative_control")
        ordinary = run_policy(c, "emit_each")
        opaque = run_policy(c, "opaque_consolidation")
        self.assertEqual((ordinary["notice_count"], ordinary["correct_effects"]), (3, 3))
        self.assertEqual((opaque["notice_count"], opaque["correct_effects"]), (1, 0))


if __name__ == "__main__":
    unittest.main()
