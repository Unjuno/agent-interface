import unittest

from candidate_v2 import normalize_openttd_observer_counts


class CandidateV2Tests(unittest.TestCase):
    def test_distinguishes_raw_records_from_transition_witnesses(self):
        old = {"observer_records": 1, "observer_record_count": 263}
        fixed = normalize_openttd_observer_counts(old, raw_record_count=263,
                                                  transition_witness_count=1)
        self.assertEqual(fixed["observer_records"], 263)
        self.assertEqual(fixed["observer_record_count"], 263)
        self.assertEqual(fixed["observer_transition_witness_count"], 1)
        self.assertEqual(old["observer_records"], 1)  # predecessor stays immutable


if __name__ == "__main__":
    unittest.main()
