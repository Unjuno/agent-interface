import copy
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
import audit_core
import candidate


class JournalStateReconciliationTests(unittest.TestCase):
    def run_case(self, case_id, external_write):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        return root, candidate.run_case(
            {"id": case_id, "external_write": external_write}, root / "db"
        )

    def test_complete_disjoint_write_allows_only_owned_field_compensation(self):
        root, row = self.run_case("disjoint_write", "disjoint_y")
        self.assertEqual(row["decision"], "COMPENSATED_DISJOINT")
        self.assertEqual(row["stale_certificate"], "UNKNOWN_STALE_CERTIFICATE")
        self.assertEqual(row["fresh_certificate_revision"], 2)
        self.assertEqual(row["final"]["state"], {"object_id": "doc", "revision": 3, "x": 0, "y": 7})
        self.assertEqual(audit_core.verify_case(row, root / "db"), [])

    def test_same_field_write_is_refused_without_changing_external_value(self):
        root, row = self.run_case("same_field_write", "same_x")
        self.assertEqual(row["decision"], "UNKNOWN_SAME_FIELD_CONFLICT")
        self.assertIsNone(row["fresh_certificate_revision"])
        self.assertEqual(row["final"]["state"], {"object_id": "doc", "revision": 2, "x": 9, "y": 0})
        self.assertEqual(audit_core.verify_case(row, root / "db"), [])

    def test_revision_advance_without_journal_row_is_unknown(self):
        root, row = self.run_case("missing_journal", "missing_row")
        self.assertEqual(row["decision"], "UNKNOWN_JOURNAL_STATE_MISMATCH")
        self.assertEqual(row["final"]["state"]["y"], 7)
        self.assertEqual(row["final"]["state"]["x"], 1)
        self.assertEqual(audit_core.verify_case(row, root / "db"), [])

    def test_sequence_gap_is_unknown(self):
        root, row = self.run_case("sequence_gap", "sequence_gap")
        self.assertEqual(row["decision"], "UNKNOWN_JOURNAL_STATE_MISMATCH")
        self.assertEqual(row["final"], row["after_external"])
        self.assertEqual(audit_core.verify_case(row, root / "db"), [])

    def test_journal_value_that_disagrees_with_committed_state_is_unknown(self):
        root, row = self.run_case("journal_state_mismatch", "tampered_value")
        self.assertEqual(row["decision"], "UNKNOWN_JOURNAL_STATE_MISMATCH")
        self.assertEqual(row["final"]["state"]["y"], 7)
        self.assertEqual(row["final"]["state"]["x"], 1)
        self.assertEqual(audit_core.verify_case(row, root / "db"), [])

    def test_independent_auditor_rejects_forged_compensation_claim(self):
        root, row = self.run_case("disjoint_write", "disjoint_y")
        forged = copy.deepcopy(row)
        forged["decision"] = "UNKNOWN_JOURNAL_STATE_MISMATCH"
        self.assertTrue(audit_core.verify_case(forged, root / "db"))

    def test_baseline_certificate_remains_current_and_recovers(self):
        root, row = self.run_case("baseline", "none")
        self.assertEqual(row["decision"], "COMPENSATED_BASELINE")
        self.assertEqual(row["stale_certificate"], "CERTIFICATE_CURRENT")
        self.assertEqual(row["final"]["state"], {"object_id": "doc", "revision": 2, "x": 0, "y": 0})
        self.assertEqual(audit_core.verify_case(row, root / "db"), [])


if __name__ == "__main__":
    unittest.main()
