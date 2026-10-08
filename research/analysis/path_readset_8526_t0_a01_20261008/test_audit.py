import copy
import unittest

from audit import audit_candidate
from candidate import run_matrix


class PathConditionedReadSetAuditTests(unittest.TestCase):
    def test_independent_audit_reconstructs_the_frozen_matrix_and_controls(self):
        report = audit_candidate({"rows": run_matrix()})
        self.assertEqual(report["status"], "PASS_PATH_CONDITIONED_READSET_SCOPED")
        self.assertEqual(report["rows"], 39)
        self.assertEqual(report["safe_salvages_vs_global_union"], 2)
        self.assertEqual(report["false_accepts_by_policy"], {"EXECUTED_PATH": 1, "GLOBAL_UNION": 0, "PATH_CERTIFICATE": 0})
        self.assertEqual(report["mutation_rejections"], 3)

    def test_audit_rejects_a_deleted_branch_predicate_dependency(self):
        rows = copy.deepcopy(run_matrix())
        row = next(row for row in rows if row["case_id"] == "unexecuted_branch_changed_a" and row["policy"] == "PATH_CERTIFICATE")
        row["certificate"]["checked_fields"].remove("route")
        with self.assertRaises(ValueError):
            audit_candidate({"rows": rows})

    def test_audit_rejects_an_unexecuted_branch_mislabeled_as_executed(self):
        rows = copy.deepcopy(run_matrix())
        row = next(row for row in rows if row["case_id"] == "stable_path_a" and row["policy"] == "PATH_CERTIFICATE")
        row["certificate"]["branch"] = "B"
        with self.assertRaises(ValueError):
            audit_candidate({"rows": rows})

    def test_audit_rejects_a_certificate_without_source_generation_binding(self):
        rows = copy.deepcopy(run_matrix())
        row = next(row for row in rows if row["case_id"] == "stable_path_a" and row["policy"] == "PATH_CERTIFICATE")
        del row["certificate"]["source_epoch"]
        with self.assertRaises(ValueError):
            audit_candidate({"rows": rows})


if __name__ == "__main__":
    unittest.main()
