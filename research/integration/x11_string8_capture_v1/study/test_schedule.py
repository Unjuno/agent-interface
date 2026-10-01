import unittest

from runner import formal_cases


class ScheduleTests(unittest.TestCase):
    def test_formal_schedule_is_30_unique_cases_in_fixed_order(self):
        cases = formal_cases()
        self.assertEqual(len(cases), 30)
        self.assertEqual(len({case["case_id"] for case in cases}), 30)
        self.assertEqual(cases[0]["case_id"], "00-all_zero-root")
        self.assertEqual(cases[-1]["case_id"], "02-ordinary_color-child")


if __name__ == "__main__":
    unittest.main()
