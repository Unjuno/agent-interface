"""Deterministic pacing construction tests, not real-time qualification."""
import unittest
from unittest.mock import patch

import common


class PacingTests(unittest.TestCase):
    def test_coarse_sleep_then_bounded_final_spin(self):
        with patch.object(common.time, "monotonic_ns", side_effect=[80_000_000, 86_000_000, 99_000_000, 100_000_000]), patch.object(common.time, "sleep") as sleep:
            common.until(100_000_000)
        sleep.assert_called_once_with(0.005)

    def test_past_deadline_never_sleeps(self):
        with patch.object(common.time, "monotonic_ns", return_value=101), patch.object(common.time, "sleep") as sleep:
            common.until(100)
        sleep.assert_not_called()


if __name__ == "__main__":
    unittest.main()
