import unittest

from boundary_check import CASES, candidate, independent_oracle


class EndpointBoundaryRecordTests(unittest.TestCase):
    def test_five_frozen_cases_retain_two_expected_disagreements(self):
        results = [
            (name, candidate(interval, available), independent_oracle(interval, available))
            for name, interval, available in CASES
        ]
        self.assertEqual(len(results), 5)
        self.assertEqual(
            [name for name, got, want in results if got != want],
            ["touches_upper_endpoint", "point_at_decision"],
        )

    def test_candidate_and_oracle_agree_off_the_exact_upper_boundary(self):
        for name, interval, available in CASES:
            if name in {"touches_upper_endpoint", "point_at_decision"}:
                continue
            with self.subTest(case=name):
                self.assertEqual(
                    candidate(interval, available),
                    independent_oracle(interval, available),
                )

    def test_candidate_does_not_inherit_oracle_conservatism_silently(self):
        self.assertEqual(candidate([80, 100], 100), "CONTINUE")
        self.assertEqual(
            independent_oracle([80, 100], 100), "YIELD_CAPTURE_ORDER_UNKNOWN"
        )


if __name__ == "__main__":
    unittest.main()
