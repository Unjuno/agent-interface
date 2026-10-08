"""Fixture-free schedule validation; this test creates no files or junctions."""
import unittest

from runner import KINDS, schedule


class ScheduleTests(unittest.TestCase):
    def test_five_accepts_and_eighteen_field_rejections(self):
        rows = schedule(__import__("pathlib").Path("C:/outside"))
        self.assertEqual(len(rows), 23)
        self.assertEqual(sum(row["kind"] in ("valid_repo", "valid_workspace", "inside_junction") for row in rows), 5)
        self.assertEqual(sum(row["kind"] in KINDS for row in rows), 18)
        self.assertEqual({row["field"] for row in rows if row["kind"] in KINDS}, {"schema", "image", "working"})
        self.assertEqual(len({row["case_id"] for row in rows}), 23)


if __name__ == "__main__":
    unittest.main()
