import copy
import unittest

from audit import EXPECTED, MODES, check
from candidate import evaluate_trace
from fixtures import TRACES


def raw_rows():
    return [row for trace in TRACES.values() for row in evaluate_trace(trace, MODES)]


class IndependentAuditTests(unittest.TestCase):
    def test_independent_expected_table_accepts_candidate_rows(self):
        self.assertEqual([], check(raw_rows()))

    def test_auditor_rejects_unsafe_joint_admission(self):
        rows = copy.deepcopy(raw_rows())
        row = next(r for r in rows if r["trace_id"] == "shared_revoked" and r["mode"] == "all_owner_conjunction")
        row["admitted"] = True
        self.assertTrue(check(rows))

    def test_auditor_rejects_permission_as_effect_receipt(self):
        rows = copy.deepcopy(raw_rows())
        row = next(r for r in rows if r["trace_id"] == "shared_both_grant" and r["mode"] == "scoped_delegation")
        row["effect_verified"] = True
        self.assertTrue(check(rows))

    def test_auditor_rejects_row_loss_and_order_mutation(self):
        rows = raw_rows()
        self.assertIn("row count mismatch", check(rows[:-1]))
        reordered = copy.deepcopy(rows)
        reordered[0], reordered[1] = reordered[1], reordered[0]
        self.assertTrue(check(reordered))

    def test_expected_table_is_literal_and_has_every_fixture_trace(self):
        self.assertEqual(set(TRACES), set(EXPECTED))
        self.assertEqual(17, len(EXPECTED))


if __name__ == "__main__":
    unittest.main()
