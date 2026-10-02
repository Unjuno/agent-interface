import json
import unittest
from pathlib import Path

import auditor

ROOT = Path(__file__).parent


class CrossHeadOwnerCounterexample(unittest.TestCase):
    def test_fixture_is_the_two_retained_distinct_head_runs(self):
        fixture = json.loads((ROOT / "fixture.json").read_text(encoding="utf-8"))
        self.assertEqual([34970434429, 34970546156], [r["id"] for r in fixture["runs"]])
        self.assertEqual(2, len({r["head_sha"] for r in fixture["runs"]}))

    def test_independent_oracle_rejects_two_formal_admissions(self):
        fixture = json.loads((ROOT / "fixture.json").read_text(encoding="utf-8"))
        candidate_rows = [
            {"current_run_id": 34970434429, "may_enter_formal_step": True},
            {"current_run_id": 34970546156, "may_enter_formal_step": True},
        ]
        result = auditor.audit(fixture, {"rows": candidate_rows})
        self.assertIn("multiple-runs-admitted-for-one-versioned-allocation", result["errors"])
        self.assertEqual("FAIL_GUARD_NOT_WORKFLOW_PATH_GLOBAL", result["disposition"])

    def test_single_canonical_admission_satisfies_invariant(self):
        fixture = json.loads((ROOT / "fixture.json").read_text(encoding="utf-8"))
        candidate_rows = [
            {"current_run_id": 34970434429, "may_enter_formal_step": True},
            {"current_run_id": 34970546156, "may_enter_formal_step": False},
        ]
        result = auditor.audit(fixture, {"rows": candidate_rows})
        self.assertEqual("PASS_INVARIANT", result["disposition"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
