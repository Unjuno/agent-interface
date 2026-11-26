import unittest

from map01_cover_cycle_experiment_v1 import split_repeated_cover
from map01_overlap_controller_v39 import compile_cover


class CoverCycleExperimentTests(unittest.TestCase):
    def test_real_compiler_program_can_be_reconstructed(self):
        commands = [{"action": "strafe_left", "extent": "short"},
                    {"action": "strafe_right", "extent": "short"},
                    {"action": "fire", "extent": "short"}]
        original = compile_cover(commands)
        cycle, count = split_repeated_cover(original, hold_count=len(commands))
        self.assertEqual(cycle * count, original)
        self.assertEqual(sum(step["duration_ms"] for step in original), 10000)

    def test_preserves_exact_compiled_program_and_renewal_budget(self):
        cycle = [{"op": "hold", "keys": ["a"], "duration_ms": 350},
                 {"op": "hold", "keys": ["d"], "duration_ms": 350},
                 {"op": "hold", "keys": ["space"], "duration_ms": 100},
                 {"op": "coast", "duration_ms": 1700, "sample_ms": 250}]
        original = cycle * 4
        selected, maximum_submissions = split_repeated_cover(original, hold_count=3)
        self.assertEqual(selected * maximum_submissions, original)
        self.assertEqual(maximum_submissions, 4)
        selected[0]["keys"].append("x")
        self.assertEqual(original[0]["keys"], ["a"])

    def test_unequal_cycles_and_coast_only_do_not_grant_a_split(self):
        coast = {"op": "coast", "duration_ms": 5000, "sample_ms": 250}
        with self.assertRaises(ValueError):
            split_repeated_cover([coast, coast], hold_count=0)
        altered = [{"op": "hold", "keys": ["a"], "duration_ms": 350},
                   {"op": "coast", "duration_ms": 4650, "sample_ms": 250},
                   {"op": "hold", "keys": ["a"], "duration_ms": 350},
                   {"op": "coast", "duration_ms": 4651, "sample_ms": 250}]
        with self.assertRaises(ValueError):
            split_repeated_cover(altered, hold_count=1)

