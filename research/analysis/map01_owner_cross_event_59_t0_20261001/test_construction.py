import json
import unittest
from pathlib import Path

import auditor

ROOT = Path(__file__).parent


class CrossEventOwnerOracleTests(unittest.TestCase):
    def setUp(self):
        self.fixture = json.loads((ROOT / "fixture.json").read_text(encoding="utf-8"))

    def test_fixture_holds_path_and_allocation_constant_across_events(self):
        runs = self.fixture["runs"]
        self.assertEqual(1, len({row["path"] for row in runs}))
        self.assertEqual(2, len({row["event"] for row in runs}))
        self.assertTrue(all(row["head_branch"] == "main" for row in runs))

    def test_two_admissions_fail_independent_invariant(self):
        candidate = {
            "workflow_path": self.fixture["workflow_path"],
            "allocation_id": self.fixture["allocation_id"],
            "rows": [
                {"current_run_id": row["id"], "may_enter_formal_step": True}
                for row in self.fixture["runs"]
            ],
        }
        result = auditor.audit(self.fixture, candidate)
        self.assertIn("multiple-events-admitted-for-one-versioned-allocation", result["errors"])
        self.assertEqual("FAIL_EVENT_FILTER_ESCAPES_PATH_GLOBAL_OWNER", result["disposition"])

    def test_single_admission_passes_invariant(self):
        first, second = self.fixture["runs"]
        candidate = {
            "workflow_path": self.fixture["workflow_path"],
            "allocation_id": self.fixture["allocation_id"],
            "rows": [
                {"current_run_id": first["id"], "may_enter_formal_step": True},
                {"current_run_id": second["id"], "may_enter_formal_step": False},
            ],
        }
        self.assertEqual("PASS_ALLOCATION_GLOBAL", auditor.audit(self.fixture, candidate)["disposition"])

    def test_missing_or_reordered_rows_fail_closed(self):
        candidate = {
            "workflow_path": self.fixture["workflow_path"],
            "allocation_id": self.fixture["allocation_id"],
            "rows": [{"current_run_id": self.fixture["runs"][1]["id"], "may_enter_formal_step": True}],
        }
        result = auditor.audit(self.fixture, candidate)
        self.assertIn("candidate-row-identity-or-order-mismatch", result["errors"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
