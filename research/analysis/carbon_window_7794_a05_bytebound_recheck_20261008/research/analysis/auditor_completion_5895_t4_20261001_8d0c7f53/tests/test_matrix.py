"""Literal contract tests for the one-shot T4 case matrix."""

import importlib
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


BASE = [
    {"event": "fixture", "allocation": "MAP01-OWNER-KEYMAP-WITNESS-5156-T3-20261001-01"},
    {"event": "runner_start", "sequence": 1},
    {"event": "runner_complete", "exit_code": 0},
]
CASE_IDS = ["control", "bool_false", "float_zero", "null", "string_zero",
            "missing_code", "duplicate_success", "success_plus_failure"]
EXITS = [0, 0, 0, 1, 1, 1, 1, 0]
COMPLETIONS = [
    [{"event": "runner_complete", "exit_code": 0}],
    [{"event": "runner_complete", "exit_code": False}],
    [{"event": "runner_complete", "exit_code": 0.0}],
    [{"event": "runner_complete", "exit_code": None}],
    [{"event": "runner_complete", "exit_code": "0"}],
    [{"event": "runner_complete"}],
    [{"event": "runner_complete", "exit_code": 0}, {"event": "runner_complete", "exit_code": 0}],
    [{"event": "runner_complete", "exit_code": 0}, {"event": "runner_complete", "exit_code": 1}],
]


class MatrixTests(unittest.TestCase):
    def test_preregistered_eight_cases_have_exact_rows_and_do_not_mutate_baseline(self):
        try:
            module = importlib.import_module("matrix")
        except ModuleNotFoundError:
            module = None
        self.assertIsNotNone(module, "T4 matrix generator must exist")
        original = [dict(row) for row in BASE]
        matrix = module.make_matrix(BASE)
        self.assertEqual([item["case_id"] for item in matrix], CASE_IDS)
        self.assertEqual([item["expected_exit"] for item in matrix], EXITS)
        for item, expected_completion in zip(matrix, COMPLETIONS):
            rows = item["rows"]
            self.assertEqual([r for r in rows if r.get("event") == "runner_complete"], expected_completion)
            self.assertEqual([r for r in rows if r.get("event") != "runner_complete"], original[:-1])
        self.assertEqual(BASE, original)

    def test_matrix_refuses_noncanonical_baseline_before_building_cases(self):
        try:
            module = importlib.import_module("matrix")
        except ModuleNotFoundError:
            module = None
        self.assertIsNotNone(module, "T4 matrix generator must exist")
        with self.assertRaises(ValueError):
            module.make_matrix([{"event": "runner_complete", "exit_code": False}])


if __name__ == "__main__":
    unittest.main(verbosity=2)
