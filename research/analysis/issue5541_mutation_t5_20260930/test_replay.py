"""Integrity tests for the retained T5 transcript; no experiment rerun."""
import copy
import json
import unittest
from replay import load_raw, replay

class RetainedT5Tests(unittest.TestCase):
    def test_raw_mutation_matrix_replays(self):
        result = replay(load_raw())
        self.assertEqual(result["raw_status"], "FAIL")
        self.assertTrue(result["all_single_mutants_killed"])
        self.assertEqual(result["combination_count"], 4)
        self.assertEqual(result["survivor_count"], 0)
        self.assertEqual(result["decision"], "FAIL_PROBE_GATE_NO_COMBINATION_SURVIVOR")

    def test_mutated_kill_set_is_rejected(self):
        raw = copy.deepcopy(load_raw())
        raw["mutants"][0]["killed"] = []
        with self.assertRaises(AssertionError):
            replay(raw)

    def test_mutated_semantic_payload_is_rejected(self):
        raw = copy.deepcopy(load_raw())
        raw["cases"][0]["authority"] = "DENIED"
        with self.assertRaises(AssertionError):
            replay(raw)

if __name__ == "__main__":
    unittest.main(verbosity=2)
