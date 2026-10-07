import json
import unittest
from pathlib import Path

import auditor
import candidate


ROOT=Path(__file__).parent


class Construction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture=json.loads((ROOT/"fixture_a02.json").read_text());cls.raw=candidate.run(cls.fixture)

    def test_complete_matrix_and_expectations(self):
        result=auditor.audit(self.raw,self.fixture);self.assertFalse(result["errors"],result);self.assertEqual(result["rows"],28)

    def test_evidence_bounded_escalates_only_with_supported_single_candidate(self):
        rows={(r["case_id"],r["policy"]):r for r in self.raw["rows"]}
        self.assertEqual(rows[("known_locus_uninformative","evidence_bounded")]["resolution"],"targeted")
        self.assertEqual(rows[("single_supported_candidate","evidence_bounded")]["resolution"],"candidate")
        self.assertEqual(rows[("multiple_supported_candidates","evidence_bounded")]["resolution"],"open")
        self.assertEqual(rows[("unknown_locus_signal_loss","evidence_bounded")]["resolution"],"open")

    def test_stop_states_and_forbidden_candidates_do_not_act(self):
        for row in self.raw["rows"]:
            if row["case_id"] in {"none_unsure_decline","stale_choice_version","candidate_forbidden"}:
                self.assertEqual(row["resolution"],"yield");self.assertIsNone(row["candidate"])

    def test_mutations_rejected(self):
        controls=auditor.mutations(self.raw,self.fixture);self.assertEqual(len(controls),8);self.assertTrue(all(x["rejected"] for x in controls),controls)


if __name__=="__main__":unittest.main()
