import copy
import json
import unittest
from pathlib import Path

from auditor import audit
from candidate import build

ROOT = Path(__file__).parent


class T0Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((ROOT / "fixture.json").read_text())
        cls.truth = json.loads((ROOT / "truth.json").read_text())
        cls.rows = build(cls.fixture)

    def test_clean_ledger_and_denominators(self):
        result = audit(self.fixture, self.truth, self.rows)
        self.assertEqual("PASS_METHOD_SCOPED", result["status"])
        self.assertEqual(36, result["rows"])
        self.assertEqual(12, result["unique_opportunities"])

    def test_missing_opportunity_rejected(self):
        result = audit(self.fixture, self.truth, self.rows[:-1])
        self.assertIn("opportunity_denominator_or_factor_mismatch", result["errors"])

    def test_oracle_label_leak_rejected(self):
        rows = copy.deepcopy(self.rows)
        rows[0]["oracle_truth"] = "anomaly"
        result = audit(self.fixture, self.truth, rows)
        self.assertIn("forbidden_oracle_field", result["errors"])

    def test_visibility_flip_rejected(self):
        rows = copy.deepcopy(self.rows)
        rows[6]["display_visibility"] = "unavailable" if rows[6]["display_visibility"] == "visible" else "visible"
        result = audit(self.fixture, self.truth, rows)
        self.assertIn("visibility_mismatch", result["errors"])

    def test_hard_stop_suppression_rejected(self):
        rows = copy.deepcopy(self.rows)
        rows[1]["machine_hard_stop"]["suppressed"] = True
        result = audit(self.fixture, self.truth, rows)
        self.assertIn("machine_hard_stop_changed", result["errors"])

    def test_unknown_evidence_rejected(self):
        rows = copy.deepcopy(self.rows)
        rows[0]["available_evidence"] = "safe"
        result = audit(self.fixture, self.truth, rows)
        self.assertIn("evidence_not_source_bound", result["errors"])


if __name__ == "__main__":
    unittest.main()
