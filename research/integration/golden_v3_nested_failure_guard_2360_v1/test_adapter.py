import unittest

from runtime.cli_v1.golden_v3 import adapt_dispatch_result


class NestedFailureTests(unittest.TestCase):
    def test_nested_runtime_failure_is_partial_and_preserves_effect(self):
        row = adapt_dispatch_result({
            "status": "returned",
            "result": {
                "status": "runtime_failed",
                "partial_effects": ["pressed"],
                "program_completed": False,
                "task_success": False,
                "error": "backend stopped",
            },
        })
        self.assertEqual(row["status"], "partial")
        self.assertFalse(row["program_completed"])
        self.assertFalse(row["task_success"])
        self.assertEqual(row["partial_effects"], ["pressed"])
        self.assertEqual(row["native_status"], "runtime_failed")

    def test_nested_refusal_remains_refusal(self):
        row = adapt_dispatch_result({
            "status": "returned",
            "result": {"status": "refused", "error": "stale"},
        })
        self.assertEqual(row["status"], "refused")
        self.assertFalse(row["program_completed"])
        self.assertFalse(row["task_success"])


if __name__ == "__main__":
    unittest.main()
