import unittest

from research.analysis.extreme_tail_eligibility_6576_construction_v1.runtime_shift import assess_shift


class RuntimeShiftConstructionTests(unittest.TestCase):
    def test_stationary_reference_has_no_false_alarm(self):
        result = assess_shift(
            [1, 2, 3, 2, 1], [2, 3, 2, 4], safety_deadline=10,
            alarm_run=2, threshold=8,
        )
        self.assertEqual(result["reference_false_alarms"], 0)
        self.assertIsNone(result["alarm_index"])
        self.assertFalse(result["protection_adequate"])

    def test_shift_alarms_but_deadline_misses_before_alarm_fail_protection(self):
        result = assess_shift(
            [1, 2, 3, 2, 1], [12, 13, 14], safety_deadline=10,
            alarm_run=2, threshold=8,
        )
        self.assertEqual(result["alarm_index"], 1)
        self.assertEqual(result["detection_delay_observations"], 2)
        self.assertEqual(result["pre_alarm_deadline_misses"], 1)
        self.assertFalse(result["protection_adequate"])
        self.assertEqual(result["post_shift_decision"], "NOT_ESTIMABLE_NEW_MODE")

    def test_delayed_alarm_within_deadline_is_scoped_adequate(self):
        result = assess_shift(
            [1, 2, 3], [7, 8, 12, 13], safety_deadline=10,
            alarm_run=2, threshold=6,
        )
        self.assertEqual(result["alarm_index"], 1)
        self.assertEqual(result["pre_alarm_deadline_misses"], 0)
        self.assertTrue(result["protection_adequate"])

    def test_invalid_values_fail_closed(self):
        for bad in (float("nan"), float("inf"), -1):
            with self.subTest(value=bad), self.assertRaises(ValueError):
                assess_shift([1], [bad], safety_deadline=10, alarm_run=1, threshold=5)


if __name__ == "__main__":
    unittest.main()
