import unittest

import audit
import candidate


class ContractTests(unittest.TestCase):
    def test_equal_duration_estimands_are_separately_computed(self):
        doc = candidate.run()
        self.assertEqual(audit.audit(doc), [])
        half = doc["scenarios"][0]["routes"][0]["claimed_summary"]
        self.assertEqual(half["event_coverage"], {"numerator": 2, "denominator": 4})
        self.assertEqual(half["time_coverage"], {"numerator": 20, "denominator": 40})

    def test_heterogeneous_duration_reverses_ranking(self):
        long, short = candidate.run()["scenarios"][1]["routes"]
        self.assertEqual(long["claimed_summary"]["event_coverage"], {"numerator": 1, "denominator": 11})
        self.assertEqual(long["claimed_summary"]["time_coverage"], {"numerator": 90, "denominator": 100})
        self.assertEqual(short["claimed_summary"]["event_coverage"], {"numerator": 10, "denominator": 11})
        self.assertEqual(short["claimed_summary"]["time_coverage"], {"numerator": 10, "denominator": 100})

    def test_no_onset_oracle_holds(self):
        row = candidate.run()["scenarios"][2]
        self.assertEqual(candidate.summarize(row, row["routes"][0])["status"], "HOLD_NO_ELIGIBLE_ONSET_CLOCK")

    def test_auditor_independently_accepts_candidate_output(self):
        self.assertEqual(audit.audit(candidate.run()), [])

    def test_all_four_mutations_rejected(self):
        self.assertEqual(len(audit.mutation_results(candidate.run())), 4)
        self.assertTrue(all(audit.mutation_results(candidate.run()).values()))

    def test_union_does_not_double_count_overlap(self):
        self.assertEqual(audit.union_measure([[0, 10], [5, 15]]), 15)

    def test_union_clips_to_eligible_windows(self):
        result = audit.independent_summary(True, True, [{"id": "x", "onset": 0, "expiry": 10}], ["x"], [[-4, 15]])
        self.assertEqual(result["time_coverage"], {"numerator": 10, "denominator": 10})


if __name__ == "__main__":
    unittest.main()
