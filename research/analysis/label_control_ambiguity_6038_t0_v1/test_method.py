import json
import unittest
from pathlib import Path

import audit
import candidate


ROOT = Path(__file__).parent


class LabelControlMethodTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((ROOT / "fixture.json").read_text())
        cls.oracle = json.loads((ROOT / "oracle.json").read_text())

    def test_fixture_has_exact_case_and_oracle_correspondence(self):
        ids = [case["id"] for case in self.fixture["cases"]]
        self.assertEqual(len(ids), 10)
        self.assertEqual(set(ids), set(self.oracle["cases"]))

    def test_candidate_exposes_expected_nearest_counterexamples(self):
        raw = candidate.run(self.fixture)
        rows = {row["case_id"]: row for row in raw["rows"]}
        self.assertEqual(rows["two_column_nearest_conflict"]["decisions"]["nearest_geometry"]["target"], "c-phone")
        self.assertEqual(rows["staggered_alignment"]["decisions"]["nearest_geometry"]["target"], "c-name")
        self.assertEqual(rows["two_plausible_controls"]["decisions"]["relation_abstention"]["action"], "ABSTAIN")

    def test_relation_policy_effect_and_fail_closed_gates(self):
        raw = candidate.run(self.fixture)
        out = audit.audit(self.fixture, self.oracle, raw)
        self.assertEqual(out["disposition"], "PASS_METHOD_SCOPED")
        self.assertEqual(out["row_count"], 10)
        self.assertEqual(out["mutations_rejected"], 4)

    def test_auditor_rejects_field_swap_and_deleted_row(self):
        raw = candidate.run(self.fixture)
        bad = json.loads(json.dumps(raw))
        bad["rows"][0]["decisions"]["relation_abstention"]["target"] = "c-name"
        with self.assertRaises(ValueError):
            audit.audit(self.fixture, self.oracle, bad)
        bad = json.loads(json.dumps(raw))
        bad["rows"].pop()
        with self.assertRaises(ValueError):
            audit.audit(self.fixture, self.oracle, bad)


if __name__ == "__main__":
    unittest.main()
