import unittest

from candidate import POLICIES, run_matrix


EXPECTED = {
    "stable_path_a": (True, True, True),
    "stable_path_b": (True, True, True),
    "unexecuted_branch_changed_a": (False, True, True),
    "unexecuted_branch_unknown_b": (False, True, True),
    "executed_leaf_changed": (False, False, False),
    "predicate_changed": (False, False, False),
    "unknown_predicate": (False, False, False),
    "unknown_active_input": (False, False, False),
    "hidden_read_incomplete": (False, True, False),
    "predicate_provenance_unknown": (False, False, False),
    "aba_source_epoch": (False, False, False),
    "producer_generation_changed": (False, False, False),
    "deadline_expired": (False, False, False),
}


class PathConditionedReadSetModelTests(unittest.TestCase):
    def test_each_policy_records_the_exact_fields_its_validator_consults(self):
        rows = run_matrix()
        keyed = {(row["case_id"], row["policy"]): row for row in rows}
        self.assertEqual(
            keyed[("stable_path_a", "GLOBAL_UNION")]["certificate"]["checked_fields"],
            ["route", "alpha", "beta", "source_epoch", "producer_generation", "deadline_ms", "complete", "predicate_provenance"],
        )
        self.assertEqual(
            keyed[("stable_path_a", "EXECUTED_PATH")]["certificate"]["checked_fields"],
            ["route", "alpha", "source_epoch", "producer_generation", "deadline_ms", "predicate_provenance"],
        )
        self.assertEqual(
            keyed[("stable_path_a", "PATH_CERTIFICATE")]["certificate"]["checked_fields"],
            ["route", "alpha", "source_epoch", "producer_generation", "deadline_ms", "complete", "predicate_provenance", "result_binding"],
        )

    def test_only_unexecuted_branch_change_is_safely_salvaged_by_path_policies(self):
        rows = run_matrix()
        keyed = {(row["case_id"], row["policy"]): row for row in rows}
        global_row = keyed[("unexecuted_branch_changed_a", "GLOBAL_UNION")]
        path_row = keyed[("unexecuted_branch_changed_a", "EXECUTED_PATH")]
        certificate_row = keyed[("unexecuted_branch_changed_a", "PATH_CERTIFICATE")]
        self.assertFalse(global_row["accepted"])
        self.assertTrue(path_row["accepted"])
        self.assertTrue(certificate_row["accepted"])

    def test_path_certificate_fails_closed_on_each_frozen_adversarial_control(self):
        rows = run_matrix()
        keyed = {(row["case_id"], row["policy"]): row for row in rows}
        for case_id in (
            "executed_leaf_changed",
            "predicate_changed",
            "unknown_predicate",
            "unknown_active_input",
            "hidden_read_incomplete",
            "predicate_provenance_unknown",
            "aba_source_epoch",
            "producer_generation_changed",
            "deadline_expired",
        ):
            with self.subTest(case_id=case_id):
                self.assertFalse(keyed[(case_id, "PATH_CERTIFICATE")]["accepted"])

    def test_matrix_has_exact_frozen_case_and_policy_coverage(self):
        rows = run_matrix()
        self.assertEqual(set(POLICIES), {"GLOBAL_UNION", "EXECUTED_PATH", "PATH_CERTIFICATE"})
        self.assertEqual(
            {(row["case_id"], row["policy"]) for row in rows},
            {(case_id, policy) for case_id in EXPECTED for policy in POLICIES},
        )
        for case_id, expected in EXPECTED.items():
            observed = tuple(
                next(row["accepted"] for row in rows if row["case_id"] == case_id and row["policy"] == policy)
                for policy in POLICIES
            )
            self.assertEqual(observed, expected, case_id)

    def test_naive_executed_path_exposes_the_incomplete_hidden_read_counterexample(self):
        rows = run_matrix()
        row = next(
            row for row in rows
            if row["case_id"] == "hidden_read_incomplete" and row["policy"] == "EXECUTED_PATH"
        )
        self.assertTrue(row["accepted"])
        self.assertFalse(row["certificate"]["complete"])


if __name__ == "__main__":
    unittest.main()
