import copy
import json
import unittest
from pathlib import Path

from run_mutation_experiment import mutate
from test_audit_formal_x11 import fixture_rows

SPEC = json.loads((Path(__file__).parent / "EXPERIMENT_SPEC.json").read_text(encoding="utf-8"))


def completion(rows):
    return [row for row in rows if row.get("event") == "runner_complete"]


class CompletionMutationTests(unittest.TestCase):
    def test_unmodified_control_is_exactly_integer_zero(self):
        rows = mutate(copy.deepcopy(fixture_rows()), "unchanged")
        records = completion(rows)
        self.assertEqual(len(records), 1)
        self.assertIs(type(records[0]["exit_code"]), int)
        self.assertEqual(records[0]["exit_code"], 0)

    def test_all_preregistered_mutations_are_implemented(self):
        for case in SPEC["mutations"]:
            with self.subTest(case=case["id"]):
                rows = mutate(copy.deepcopy(fixture_rows()), case["kind"])
                self.assertTrue(completion(rows))

    def test_boolean_zero_exploits_integer_equality(self):
        value = completion(mutate(copy.deepcopy(fixture_rows()), "exit_code_false"))[0]["exit_code"]
        self.assertIs(type(value), bool)
        self.assertEqual(value, 0)

    def test_float_zero_exploits_integer_equality(self):
        value = completion(mutate(copy.deepcopy(fixture_rows()), "exit_code_float_zero"))[0]["exit_code"]
        self.assertIs(type(value), float)
        self.assertEqual(value, 0)

    def test_success_plus_nonzero_retains_two_records(self):
        records = completion(mutate(copy.deepcopy(fixture_rows()), "append_nonzero_completion"))
        self.assertEqual([row["exit_code"] for row in records], [0, 2])

    def test_duplicate_success_adds_a_second_integer_zero(self):
        records = completion(mutate(copy.deepcopy(fixture_rows()), "append_integer_zero_completion"))
        self.assertEqual([row["exit_code"] for row in records], [0, 0])


if __name__ == "__main__":
    unittest.main()
