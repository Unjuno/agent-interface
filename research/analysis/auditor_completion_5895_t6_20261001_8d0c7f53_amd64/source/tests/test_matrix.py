import copy
import unittest

from matrix import make_matrix


class CompletionMutationMatrixTests(unittest.TestCase):
    def test_builds_frozen_case_ids_without_changing_other_rows(self):
        base = [
            {"event": "fixture", "allocation": "ALLOCATION"},
            {"event": "runner_complete", "exit_code": 0},
            {"event": "terminal_state", "neutral": True},
        ]
        original = copy.deepcopy(base)

        cases = make_matrix(base)

        self.assertEqual(
            [case["case_id"] for case in cases],
            ["control", "bool_false", "float_zero", "null", "string_zero",
             "missing_code", "duplicate_success", "success_plus_failure"],
        )
        self.assertEqual(base, original)
        self.assertEqual(len(cases), 8)
        for case in cases:
            self.assertEqual(
                [row for row in case["rows"] if row.get("event") != "runner_complete"],
                [row for row in base if row.get("event") != "runner_complete"],
            )

    def test_changes_only_the_completion_record_under_test(self):
        base = [
            {"event": "fixture", "allocation": "ALLOCATION"},
            {"event": "runner_complete", "exit_code": 0},
            {"event": "terminal_state", "neutral": True},
        ]

        cases = {case["case_id"]: case for case in make_matrix(base)}

        completion = lambda case: [r for r in case["rows"] if r.get("event") == "runner_complete"]
        self.assertEqual(completion(cases["control"]), [{"event": "runner_complete", "exit_code": 0}])
        self.assertEqual(completion(cases["bool_false"]), [{"event": "runner_complete", "exit_code": False}])
        self.assertEqual(completion(cases["float_zero"]), [{"event": "runner_complete", "exit_code": 0.0}])
        self.assertEqual(completion(cases["null"]), [{"event": "runner_complete", "exit_code": None}])
        self.assertEqual(completion(cases["string_zero"]), [{"event": "runner_complete", "exit_code": "0"}])
        self.assertEqual(completion(cases["missing_code"]), [{"event": "runner_complete"}])
        self.assertEqual(
            completion(cases["duplicate_success"]),
            [{"event": "runner_complete", "exit_code": 0}, {"event": "runner_complete", "exit_code": 0}],
        )
        self.assertEqual(
            completion(cases["success_plus_failure"]),
            [{"event": "runner_complete", "exit_code": 0}, {"event": "runner_complete", "exit_code": 1}],
        )


if __name__ == "__main__":
    unittest.main()
