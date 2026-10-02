import unittest

from audit import independently_audit
from candidate import MAX_GAP, N, T, admissible, audit_metrics


class FiniteScheduleAuditTests(unittest.TestCase):
    def test_independent_counts_and_phase_miss_vectors_match(self):
        candidate = audit_metrics()
        audit = independently_audit()
        self.assertEqual(candidate["admissible_schedule_count"], audit["schedule_count"])
        for width, row in candidate["duration_results"].items():
            checked = audit["results"][width]
            self.assertEqual(row["miss_numerator_by_phase"], checked["miss_count_by_phase"])
            self.assertEqual(row["periodic_all_four_miss_phases"],
                             checked["periodic_miss_phase_count"])

    def test_every_admitted_cycle_respects_frozen_gap_cap(self):
        from itertools import product
        cycles = [s for s in product(range(T), repeat=N) if admissible(s)]
        self.assertEqual(12546, len(cycles))
        self.assertTrue(all(T + s[(i + 1) % N] - s[i] <= MAX_GAP
                            for s in cycles for i in range(N)))

    def test_phase_locked_periodic_control_repeats_miss_for_unlucky_phases(self):
        result = audit_metrics()["duration_results"]
        self.assertEqual([11, 10, 9],
                         [result[str(d)]["periodic_all_four_miss_phases"]
                          for d in (1, 2, 3)])


if __name__ == "__main__":
    unittest.main()
