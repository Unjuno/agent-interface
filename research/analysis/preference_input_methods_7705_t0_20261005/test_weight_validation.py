"""Post-freeze regression tests; formal_01 and frozen sources remain untouched."""
import copy
import json
import math
import pathlib
import unittest

import auditor
from auditor_hardened import weight_input_errors
from candidate import DATA, evaluate as frozen_evaluate
from candidate_hardened import evaluate as hardened_evaluate

ROOT = pathlib.Path(__file__).parent


class WeightValidationFollowup(unittest.TestCase):
    def test_nan_reproduces_original_false_feasible_classification(self):
        case = copy.deepcopy(next(c for c in DATA["cases"] if c["id"] == "weights-fast"))
        case["input"]["weights"]["wait_ms"] = float("nan")
        legacy = frozen_evaluate(case)
        self.assertEqual(legacy["status"], "NO_FEASIBLE_ROUTE")
        menu = json.loads((ROOT / "cases.json").read_text())
        result = auditor.audit(menu, [case], [{"case_id": case["id"], "result": legacy}])
        self.assertEqual(result["status"], "PASS_METHOD_SCOPED")
        self.assertEqual(weight_input_errors(case, menu["criteria"]),
                         ["WEIGHT_VALUE_NOT_FINITE_NONNEGATIVE"])

    def test_hardened_candidate_fails_closed_for_nonfinite_and_invalid_weights(self):
        base = copy.deepcopy(next(c for c in DATA["cases"] if c["id"] == "weights-fast"))
        for bad in (float("nan"), float("inf"), -float("inf"), -0.1, True):
            case = copy.deepcopy(base)
            case["input"]["weights"]["wait_ms"] = bad
            self.assertEqual(hardened_evaluate(case)["status"], "HOLD_INPUT_INVALID")
            self.assertTrue(weight_input_errors(case, DATA["criteria"]))

    def test_overflowing_total_and_score_fail_closed(self):
        base = copy.deepcopy(next(c for c in DATA["cases"] if c["id"] == "weights-fast"))
        base["input"]["weights"] = {key: 1e308 for key in DATA["criteria"]}
        self.assertEqual(hardened_evaluate(base)["status"], "HOLD_INPUT_INVALID")
        self.assertTrue(weight_input_errors(base, DATA["criteria"]))


if __name__ == "__main__":
    unittest.main()
