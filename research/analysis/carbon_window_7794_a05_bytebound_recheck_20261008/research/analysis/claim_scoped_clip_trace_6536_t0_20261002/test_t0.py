from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import audit
import candidate


class ClipTraceT0Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((ROOT / "fixtures.json").read_text())
        cls.oracle = json.loads((ROOT / "oracle.json").read_text())
        cls.raw = candidate.run(cls.fixture)

    def test_case_schedule_and_oracle_are_complete(self):
        ids = [case["id"] for case in self.fixture["cases"]]
        self.assertEqual(ids, [f"C{i:02d}" for i in range(1, 10)])
        self.assertEqual(set(ids), set(self.oracle["supported"]))
        self.assertEqual(sum(self.oracle["supported"].values()), 2)

    def test_candidate_claim_scopes_match_frozen_oracle(self):
        result = {row["case_id"]: row["arms"]["D_claim_scoped_map_candidate"] for row in self.raw["rows"]}
        self.assertEqual(result, self.oracle["supported"])

    def test_independent_audit_reconstructs_all_cases(self):
        result = audit.audit(self.raw, self.fixture, self.oracle)
        self.assertEqual(result["status"], "PASS_METHOD_SCOPED")
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["scoped_positive_accepts"], 2)

    def test_comparison_arms_expose_false_acceptance(self):
        result = audit.audit(self.raw, self.fixture, self.oracle)
        for arm in ("A_clip_caption", "B_clip_master_link", "C_hashed_edl_only"):
            self.assertGreater(result["false_accepts_by_arm"][arm], 0)
        self.assertNotIn("D_claim_scoped_map_candidate", result["false_accepts_by_arm"])

    def test_all_five_corruption_controls_are_rejected(self):
        for name in self.oracle["required_mutations"]:
            with self.subTest(name=name):
                self.assertTrue(audit.mutation_rejected(name, self.raw, self.fixture, self.oracle))


if __name__ == "__main__":
    unittest.main()
