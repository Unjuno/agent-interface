import unittest

from scheduler import run_case


class NestedInheritanceTests(unittest.TestCase):
    def test_deadline_only_control_misses_behind_medium_work(self):
        result = run_case("transitive", policy="no_inheritance")
        self.assertEqual(result["verifier"], {"status": "deadline_missed", "at": None})

    def test_transitive_inheritance_finishes_deadline_verifier(self):
        result = run_case("transitive", policy="inheritance_only")
        self.assertEqual(result["verifier"], {"status": "completed", "at": 6})
        self.assertEqual(result["owners"], {"A": 2, "B": 2})

    def test_cancelled_waiter_revokes_transitive_inheritance(self):
        result = run_case("cancelled", policy="inheritance_only")
        self.assertEqual(result["verifier"], {"status": "cancelled", "at": 2})
        self.assertEqual(result["owners"], {"A": 1, "B": 0})

    def test_aging_policy_bounds_background_starvation_after_inheritance(self):
        result = run_case("transitive", policy="inheritance_plus_aging")
        self.assertLessEqual(result["max_background_wait"], 6)
        self.assertEqual(result["verifier"], {"status": "completed", "at": 6})
        later = [row["job"] for row in result["schedule"] if row["tick"] > 6]
        self.assertIn("M", later)
        self.assertIn("U", later)


if __name__ == "__main__":
    unittest.main()
