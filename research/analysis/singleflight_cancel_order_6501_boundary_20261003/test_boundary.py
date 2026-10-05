import unittest

from boundary import ordered_verdict


class CancellationOrder(unittest.TestCase):
    def test_cancel_before_return_in_same_clock_bucket(self):
        self.assertEqual(ordered_verdict([("cancel_a", 5, 0), ("return", 5, 1)], "a", "TRUE"), "CANCELLED_WAITER")

    def test_return_precedes_later_cancel(self):
        self.assertEqual(ordered_verdict([("return", 5, 0), ("cancel_a", 5, 1)], "a", "TRUE"), "ADMISSIBLE_TRUE")

    def test_other_waiter_cancel_is_local(self):
        self.assertEqual(ordered_verdict([("cancel_b", 5, 0), ("return", 5, 1)], "a", "FALSE"), "ADMISSIBLE_FALSE")

    def test_no_return_is_unknown(self):
        self.assertEqual(ordered_verdict([("cancel_a", 5, 0)], "a", "TRUE"), "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
