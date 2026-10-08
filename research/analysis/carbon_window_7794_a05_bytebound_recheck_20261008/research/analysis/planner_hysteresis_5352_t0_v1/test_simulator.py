import unittest

from simulator import decode_symbol, encode_trace, run_policy, traces


class HysteresisConstructionTests(unittest.TestCase):
    def test_symbol_encoding_is_bijective(self):
        values = [decode_symbol(i) for i in range(20)]
        self.assertEqual(len(set(values)), 20)
        self.assertEqual(values[0], (0, False, False))
        self.assertEqual(values[19], (4, True, True))

    def test_raw_threshold_boundary(self):
        self.assertEqual(run_policy((3,), "raw"), (1,))  # fresh risk .7
        self.assertEqual(run_policy((2,), "raw"), (0,))  # fresh risk .5

    def test_critical_and_stale_are_same_row_overrides(self):
        for symbol in range(20):
            _, stale, critical = decode_symbol(symbol)
            if stale or critical:
                for policy in ("raw", "fixed_hysteresis", "minimum_dwell"):
                    self.assertEqual(run_policy((symbol,), policy), (1,), (symbol, policy))

    def test_hysteresis_enter_hold_exit_boundaries(self):
        self.assertEqual(run_policy((3, 2, 2, 1), "fixed_hysteresis"), (1, 1, 1, 0))

    def test_stale_clears_hysteresis_state_after_override(self):
        self.assertEqual(run_policy((3, 2, 8, 2), "fixed_hysteresis"), (1, 1, 1, 0))

    def test_dwell_holds_two_following_fresh_rows(self):
        self.assertEqual(run_policy((3, 0, 0, 0), "minimum_dwell"), (1, 1, 1, 0))

    def test_canonical_encoding_and_exhaustive_denominator(self):
        self.assertEqual(encode_trace((0, 19, 14)), "0JE")
        self.assertEqual(sum(1 for _ in traces()), 8420)

    def test_bad_symbols_and_policy_names_fail_closed(self):
        with self.assertRaises(ValueError):
            decode_symbol(20)
        with self.assertRaises(ValueError):
            run_policy((0,), "unknown")


if __name__ == "__main__":
    unittest.main()
