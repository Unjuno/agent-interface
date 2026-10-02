import json
import unittest

import audit_reconcile as audit


class ReconcileSetupTests(unittest.TestCase):
    def test_sources_and_actual_row_shape_before_freeze(self):
        self.assertTrue((audit.REPO / ".git").exists())
        model_path = audit.T1 / "inputs/MODEL.json"
        candidate_path = audit.T1 / "inputs/results/t0-01/candidate_raw.json"
        raw_path = audit.T2 / "results/t2-01/audit_raw.json"
        for path in (model_path, candidate_path, raw_path):
            self.assertTrue(path.is_file(), str(path))
        rows = json.loads(candidate_path.read_text())["outcome_rows"]
        self.assertIn("outcome", rows[0])
        self.assertIn("id", rows[0]["outcome"])

    def test_universal_oracle_requires_all_obligations(self):
        row = {"effect": "exact_target_saved", "forbidden_prefix": [], "release": "empty_verified", "terminated": True, "steps": 2}
        self.assertTrue(audit.exact_safe(row, 3))
        self.assertFalse(audit.exact_safe({**row, "forbidden_prefix": ["wrong_target"]}, 3))
        self.assertFalse(audit.exact_safe({**row, "release": "still_held"}, 3))


if __name__ == "__main__":
    unittest.main()
