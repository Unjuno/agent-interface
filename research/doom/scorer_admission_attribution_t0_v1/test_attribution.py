import unittest

from candidate import classify_progress


class AdmissionAttributionTests(unittest.TestCase):
    def test_observed_delta_cannot_distinguish_pre_admission_from_recovery_kill(self):
        # The scorer has the same observations in both worlds. Only the hidden
        # true kill time differs, so no event-time attribution is possible.
        samples = [(100, 0), (200, 1)]
        worlds = {"before_admission": 140, "during_recovery": 180}
        observed = {name: (samples, 150, 160) for name in worlds}
        self.assertEqual(observed["before_admission"], observed["during_recovery"])
        self.assertLess(worlds["before_admission"], 150)
        self.assertGreaterEqual(worlds["during_recovery"], 160)
        self.assertEqual(
            classify_progress(samples, 150, 160, max_gap_ns=100),
            {"decision": "POST_CANCELLATION_COOCCURRENCE", "reason": "no_post_admission_pre_input_baseline"},
        )

    def test_baseline_after_admission_before_input_and_bounded_positive_sample_qualify(self):
        samples = [(100, 0), (155, 0), (205, 1)]
        self.assertEqual(
            classify_progress(samples, 150, 160, max_gap_ns=100),
            {"decision": "ADMISSION_BRACKETED_PROGRESS", "baseline_ns": 155, "positive_sample_ns": 205, "gap_ns": 50},
        )

    def test_no_pre_input_baseline_is_rejected(self):
        self.assertEqual(
            classify_progress([(100, 0), (170, 0), (200, 1)], 150, 160, max_gap_ns=100),
            {"decision": "POST_CANCELLATION_COOCCURRENCE", "reason": "no_post_admission_pre_input_baseline"},
        )

    def test_unbounded_positive_sample_is_rejected(self):
        self.assertEqual(
            classify_progress([(100, 0), (155, 0), (300, 1)], 150, 160, max_gap_ns=100),
            {"decision": "POST_CANCELLATION_COOCCURRENCE", "reason": "positive_sample_gap_exceeded"},
        )

    def test_any_missed_polling_period_is_rejected(self):
        self.assertEqual(
            classify_progress([(100, 0), (155, 0), (205, 1)], 150, 160, max_gap_ns=100, missed_periods=1),
            {"decision": "POST_CANCELLATION_COOCCURRENCE", "reason": "missed_sample_periods"},
        )

    def test_sample_order_and_admission_bracket_are_validated(self):
        for samples, admitted, first_input in (
            ([(155, 0), (154, 1)], 150, 160),
            ([(155, 0), (205, 1)], 160, 160),
            ([(155, 0), (205, 1)], 150, 150),
        ):
            with self.subTest(samples=samples, admitted=admitted, first_input=first_input):
                result = classify_progress(samples, admitted, first_input, max_gap_ns=100)
                self.assertEqual(result["decision"], "POST_CANCELLATION_COOCCURRENCE")


if __name__ == "__main__":
    unittest.main()
