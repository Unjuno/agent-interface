import json
import unittest
from pathlib import Path

import auditor
import candidate


ROOT = Path(__file__).parent


class Construction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture=json.loads((ROOT/"fixture.json").read_text())
        cls.raw=candidate.run(cls.fixture)

    def test_complete_matrix_matches_independent_oracle(self):
        result=auditor.audit(self.raw,self.fixture)
        self.assertFalse(result["errors"],result)
        self.assertEqual(result["rows"],28)

    def test_escalation_only_narrows_with_single_supported_candidate(self):
        rows={(r["case_id"],r["policy"]):r for r in self.raw["rows"]}
        self.assertEqual(rows[("single_supported_candidate","evidence_bounded")]["resolution"],"candidate")
        self.assertEqual(rows[("multiple_supported_candidates","evidence_bounded")]["resolution"],"open")
        self.assertEqual(rows[("unknown_locus_signal_loss","evidence_bounded")]["resolution"],"open")

    def test_decline_stale_and_forbidden_remain_nonacting(self):
        for r in self.raw["rows"]:
            if r["case_id"] in {"none_unsure_decline","stale_choice_version","candidate_forbidden"}:
                self.assertIsNone(r["candidate"])
                self.assertEqual(r["resolution"],"yield")

    def test_mutation_controls(self):
        controls=auditor.mutations(self.raw,self.fixture)
        self.assertTrue(all(c["rejected"] for c in controls),controls)


if __name__ == "__main__":
    unittest.main()
