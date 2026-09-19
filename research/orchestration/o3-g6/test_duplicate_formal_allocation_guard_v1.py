import unittest

from duplicate_formal_allocation_guard_v1 import inspect_runs

PATH = ".github/workflows/formal.yml"
SHA = "a" * 40
ALLOC = "formal-01"


def run(run_id, status, *, sha=SHA, path=PATH, run_number=None):
    return {
        "id": run_id,
        "path": path,
        "head_sha": sha,
        "status": status,
        "run_number": run_number or run_id,
        "run_attempt": 1,
        "event": "push",
        "conclusion": None,
    }


class GuardTest(unittest.TestCase):
    def inspect(self, rows):
        return inspect_runs(
            {"workflow_runs": rows},
            workflow_path=PATH,
            head_sha=SHA,
            allocation_id=ALLOC,
        )

    def test_zero_active_is_safe_to_launch(self):
        out = self.inspect([run(1, "completed")])
        self.assertEqual(out["result_class"], "PASS_SINGLE_ACTIVE")
        self.assertTrue(out["safe_to_launch_another"])

    def test_one_active_blocks_another_launch_without_calling_it_duplicate(self):
        out = self.inspect([run(1, "in_progress")])
        self.assertEqual(out["result_class"], "PASS_SINGLE_ACTIVE")
        self.assertFalse(out["safe_to_launch_another"])
        self.assertEqual(out["active_count"], 1)

    def test_two_active_same_sha_and_workflow_fail(self):
        out = self.inspect([run(1, "in_progress"), run(2, "queued")])
        self.assertEqual(out["result_class"], "FAIL_DUPLICATE_ACTIVE")
        self.assertEqual(out["active_count"], 2)

    def test_different_sha_is_not_same_frozen_allocation_launch(self):
        out = self.inspect([run(1, "in_progress"), run(2, "in_progress", sha="b" * 40)])
        self.assertEqual(out["active_count"], 1)

    def test_different_workflow_is_not_same_launch(self):
        out = self.inspect([run(1, "in_progress"), run(2, "in_progress", path="other.yml")])
        self.assertEqual(out["active_count"], 1)

    def test_duplicate_api_row_same_run_id_is_deduplicated(self):
        out = self.inspect([run(1, "in_progress"), run(1, "in_progress")])
        self.assertEqual(out["active_count"], 1)

    def test_completed_plus_active_is_not_duplicate_active(self):
        out = self.inspect([run(1, "completed"), run(2, "in_progress")])
        self.assertEqual(out["active_count"], 1)

    def test_malformed_rows_are_counted_not_promoted_to_conflict(self):
        out = self.inspect([{"id": 1}, run(2, "in_progress")])
        self.assertEqual(out["malformed_count"], 1)
        self.assertEqual(out["active_count"], 1)


if __name__ == "__main__":
    unittest.main()
