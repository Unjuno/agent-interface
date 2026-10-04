"""Post-freeze regression tests; formal_01 and frozen sources remain untouched."""
import copy
import json
import shutil
import pathlib
import subprocess
import sys
import tempfile
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

    def test_oversized_integer_and_non_object_inputs_fail_closed(self):
        base = copy.deepcopy(next(c for c in DATA["cases"] if c["id"] == "weights-fast"))
        base["input"]["weights"]["wait_ms"] = 10**400
        self.assertEqual(hardened_evaluate(base)["status"], "HOLD_INPUT_INVALID")
        self.assertTrue(weight_input_errors(base, DATA["criteria"]))
        for invalid_input in (None, [], "weights"):
            case = copy.deepcopy(next(c for c in DATA["cases"] if c["id"] == "weights-fast"))
            case["input"] = invalid_input
            self.assertEqual(hardened_evaluate(case)["status"], "HOLD_INPUT_INVALID")
            self.assertTrue(weight_input_errors(case, DATA["criteria"]))
        case = copy.deepcopy(next(c for c in DATA["cases"] if c["id"] == "weights-fast"))
        case["input"]["weights"] = None
        self.assertEqual(hardened_evaluate(case)["status"], "HOLD_INPUT_INVALID")
        self.assertTrue(weight_input_errors(case, DATA["criteria"]))

    def test_direct_execution_writes_only_followup_output_and_labels_command(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            shutil.copy2(ROOT / "cases.json", temp_path / "cases.json")
            shutil.copy2(ROOT / "candidate_hardened.py", temp_path / "candidate_hardened.py")
            proc = subprocess.run([sys.executable, "-B", "candidate_hardened.py"],
                                  cwd=temp_dir, capture_output=True, text=True, check=False)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertTrue((temp_path / "followup_01" / "RAW.json").is_file())
            self.assertFalse((temp_path / "formal_01").exists())
            receipt = json.loads((temp_path / "followup_01" / "CANDIDATE_RECEIPT.json").read_text())
            self.assertEqual(receipt["command"], "python3 -B candidate_hardened.py")


if __name__ == "__main__":
    unittest.main()
