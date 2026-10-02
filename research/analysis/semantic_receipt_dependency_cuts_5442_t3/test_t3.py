"""Construction tests excluded from candidate output and scientific counts."""

import unittest

from audit import EXPECTED, audit
from candidate import run


class T3Tests(unittest.TestCase):
    def test_expected_policy_dispositions(self):
        rows = list(run())
        got = {
            row["case_id"]: (row["ab_agreement_commit"], row["provenance_pair_commit"], row["trusted_c_status"], row["trusted_c_commit"])
            for row in rows
        }
        self.assertEqual(got, EXPECTED)

    def test_common_cache_counterexample_and_abstention_tradeoff(self):
        rows = {row["case_id"]: row for row in run()}
        common = rows["shared_cache_common_lie"]
        self.assertTrue(common["ab_agreement_commit"])
        self.assertFalse(common["provenance_pair_commit"])
        self.assertEqual(common["trusted_c_status"], "SEMANTICALLY_CONTRADICTED")
        correlated = rows["actuator_readback_fault"]
        self.assertTrue(correlated["ab_agreement_commit"])
        self.assertFalse(correlated["provenance_pair_commit"])
        self.assertEqual(correlated["trusted_c_status"], "UNKNOWN")

    def test_independent_raw_only_audit(self):
        result = audit(list(run()))
        self.assertEqual(result, {"rows": 5, "errors": [], "audit": "PASS"})

    def test_dependency_closure_is_derived_through_intermediates(self):
        rows = {row["case_id"]: row for row in run()}
        self.assertEqual(rows["no_fault"]["dependency_closures"]["observer_a"], ["parser_a", "shared_cache"])
        self.assertEqual(rows["no_fault"]["dependency_closures"]["observer_c"], ["actuator_readback"])


if __name__ == "__main__":
    unittest.main()
