from __future__ import annotations

import unittest

from audit_correction import first_break_even


class BreakEvenCorrectionTests(unittest.TestCase):
    def test_initialization_is_charged_only_to_reuse(self):
        self.assertEqual(first_break_even([50, 50, 50], [1, 1, 1], 100), 3)

    def test_non_crossing_is_censored_after_horizon(self):
        self.assertEqual(first_break_even([1, 1], [5, 5], 100), 3)

    def test_mismatched_paired_lengths_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "paired_request_count_mismatch"):
            first_break_even([10], [], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
