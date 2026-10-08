"""Construction tests; excluded from candidate output and scientific count."""

import unittest

from audit import EXPECTED, audit_rows
from candidate import run


class T12ConstructionTests(unittest.TestCase):
    def test_frozen_case_classifications(self):
        rows = list(run())
        self.assertEqual({r["case_id"]: (r["trace_equal"], r["bisimilar"]) for r in rows}, EXPECTED)

    def test_raw_only_auditor_accepts_frozen_candidate(self):
        result = audit_rows(list(run()))
        self.assertEqual(result["audit"], "PASS")
        self.assertEqual(result["errors"], [])

    def test_branch_split_has_same_traces_but_not_bisimilar(self):
        row = next(r for r in run() if r["case_id"] == "branch_readiness_split")
        self.assertEqual(row["left_traces"], row["right_traces"])
        self.assertFalse(row["bisimilar"])

    def test_independent_auditor_derives_branch_action_witness(self):
        result = audit_rows(list(run()))
        self.assertTrue(result["branch_witnesses"])
        labels = {
            label
            for witness in result["branch_witnesses"]
            for label in witness["left_only_actions"] + witness["right_only_actions"]
        }
        self.assertIn("COPY", labels)
        self.assertIn("DELETE", labels)


if __name__ == "__main__":
    unittest.main()
