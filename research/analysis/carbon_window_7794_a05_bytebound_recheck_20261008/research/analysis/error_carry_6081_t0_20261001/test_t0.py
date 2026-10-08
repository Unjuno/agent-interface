import importlib.util
import sys
import unittest
from fractions import Fraction
from pathlib import Path


HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location("candidate", HERE / "candidate.py")
candidate = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = candidate
spec.loader.exec_module(candidate)


class CandidateConstructionTests(unittest.TestCase):
    def test_exact_cardinal_is_exact(self):
        self.assertEqual(candidate.compile_case([1, 0, 1], 5, [[1, 0], [0, 1], [-1, 0], [0, -1]], "error_carry"), [[1, 0]] * 5)

    def test_zero_refuses_to_continue(self):
        self.assertEqual(candidate.compile_case([0, 0, 1], 7, [[1, 0], [0, 1], [-1, 0], [0, -1]], "error_carry"), [])

    def test_schedule_is_horizon_bounded(self):
        for n in range(1, 12):
            schedule = candidate.compile_case([7, 2, 10], n, [[1, 0], [0, 1], [-1, 0], [0, -1]], "error_carry")
            self.assertLessEqual(len(schedule), n)

    def test_commands_are_legal(self):
        alphabet = [[1, 0], [0, 1], [-1, 0], [0, -1]]
        self.assertTrue(all(c in alphabet for c in candidate.compile_case([7, 2, 10], 8, alphabet, "error_carry")))


if __name__ == "__main__":
    unittest.main()
