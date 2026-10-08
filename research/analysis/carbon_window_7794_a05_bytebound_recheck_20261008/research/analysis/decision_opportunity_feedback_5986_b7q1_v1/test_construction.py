import json
import unittest
from pathlib import Path

import candidate
import audit

FIXTURE=json.loads((Path(__file__).parent/"fixture.json").read_text(encoding="utf-8"))


class Construction(unittest.TestCase):
    def test_candidate_and_independent_expected_rows_agree(self):
        self.assertEqual(candidate.analyze(FIXTURE),[audit.expected_row(c,FIXTURE["oracle_action_effects"],FIXTURE["cue_content"]) for c in FIXTURE["cases"]])

    def test_optional_arms_keep_identical_source_bound_content(self):
        first=FIXTURE["cases"][:5]
        self.assertEqual({c["event_id"] for c in first},{"event-017"})
        self.assertEqual({c.get("content",FIXTURE["cue_content"]) for c in first},{FIXTURE["cue_content"]})

    def test_all_six_dispositions_are_distinct_and_frozen(self):
        labels=[x["classification"] for x in candidate.analyze(FIXTURE)]
        self.assertEqual(len(set(labels)),6)

    def test_late_delivery_not_counted_as_opportunity(self):
        row=candidate.analyze(FIXTURE)[1]
        self.assertEqual(row["classification"],"DELIVERED_BUT_NO_DECISION_WINDOW")
        self.assertEqual(row["arrival_only"],"CAPTURE_BEFORE_DEADLINE")

    def test_undelivered_and_stale_never_become_decision_candidates(self):
        rows=candidate.analyze(FIXTURE)
        self.assertEqual(rows[2]["classification"],"EARLY_BUT_NOT_DELIVERED")
        self.assertEqual(rows[4]["classification"],"STALE_OR_MISLEADING_YIELD")

    def test_synthetic_intervention_is_not_verified_value(self):
        rows=candidate.analyze(FIXTURE)
        self.assertTrue(rows[0]["decision_changed"])
        self.assertEqual(rows[0]["simulated_effect_delta"],1)
        self.assertTrue(all(not x["verified_value_claim"] for x in rows))

    def test_required_safety_cue_is_never_withheld(self):
        row=candidate.analyze(FIXTURE)[5]
        self.assertEqual(row["classification"],"MANDATORY_SAFETY_CUE_INELIGIBLE_FOR_WITHHOLDING")
        self.assertTrue(row["withholding_refused"])

    def test_five_output_corruptions_reject(self):
        rows=candidate.analyze(FIXTURE); expected=[audit.expected_row(c,FIXTURE["oracle_action_effects"],FIXTURE["cue_content"]) for c in FIXTURE["cases"]]
        self.assertTrue(all(audit.mutations_rejected(rows,expected).values()))


if __name__=="__main__": unittest.main()
