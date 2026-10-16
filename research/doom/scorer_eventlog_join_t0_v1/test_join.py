import unittest

from candidate import classify_intent
from run import MAX_GAP_NS, fixtures


class FileJoinTests(unittest.TestCase):
    def test_all_frozen_file_level_cases(self):
        for case_id, events, samples, expected in fixtures():
            with self.subTest(case=case_id):
                observed = classify_intent(events, samples, "recover-1", max_gap_ns=MAX_GAP_NS)
                self.assertEqual(observed["decision"], expected)
                self.assertFalse(observed["causal_attribution"])

    def test_positive_result_exposes_the_joined_boundaries(self):
        case_id, events, samples, _ = fixtures()[0]
        result = classify_intent(events, samples, "recover-1", max_gap_ns=MAX_GAP_NS)
        self.assertEqual((result["accepted_ns"], result["first_input_ns"],
                          result["baseline_ns"], result["positive_sample_ns"]),
                         (100, 120, 110, 130))

    def test_stale_baseline_would_misclassify_progress_seen_before_input(self):
        case_id, events, samples, _ = next(row for row in fixtures()
                                           if row[0] == "freshest_pre_input_baseline")
        result = classify_intent(events, samples, "recover-1", max_gap_ns=MAX_GAP_NS)
        self.assertEqual(result["reason"], "no_bounded_post_input_progress")


if __name__ == "__main__":
    unittest.main()
