import copy
import json
import unittest
from pathlib import Path

import auditor
import candidate


FIXTURE = json.loads(Path("fixture.json").read_text(encoding="utf-8"))
ORACLE = json.loads(Path("oracle.json").read_text(encoding="utf-8"))


class ProtocolTests(unittest.TestCase):
    def test_fixture_has_eight_unique_rows_and_nine_arms(self):
        self.assertEqual(len(FIXTURE["cases"]), 8)
        self.assertEqual(len({c["id"] for c in FIXTURE["cases"]}), 8)
        self.assertEqual(len(FIXTURE["arms"]), 9)
        self.assertNotIn("expected_effect", json.dumps(FIXTURE))
        self.assertNotIn("effect_oracle", json.dumps(FIXTURE))

    def test_candidate_denominator_is_72(self):
        raw = candidate.run(FIXTURE)
        self.assertEqual(len(raw["rows"]), 72)

    def test_frozen_candidate_passes_independent_audit(self):
        result = auditor.audit(FIXTURE, ORACLE, candidate.run(FIXTURE))
        self.assertEqual(result["status"], "METHOD_PASS_SCOPED")
        self.assertEqual(result["errors"], [])

    def test_stale_and_contradictory_cards_remain_unknown(self):
        raw = candidate.run(FIXTURE)
        by_key = {(r["case_id"], r["arm"]): r for r in raw["rows"]}
        for case_id in ("modal_absent_old_card", "lookalike_different_effect", "focus_moved", "generation_changed", "unsupported_mode"):
            row = by_key[(case_id, "UNCERTAINTY_CONTRADICTION")]
            self.assertTrue(row["unknown"])
            self.assertEqual(row["mode"], "UNKNOWN")
            self.assertEqual(row["operations"], [])

    def test_valid_cards_do_not_claim_goal_authority_or_completion(self):
        raw = candidate.run(FIXTURE)
        for row in raw["rows"]:
            if row["arm"] in ("MODE_LABEL", "CANDIDATE_EFFECT", "UNCERTAINTY_CONTRADICTION"):
                self.assertEqual(row["goal_appropriateness"], "UNKNOWN")
                self.assertFalse(row["authority"])
                self.assertEqual(row["completion"], "NONE")

    def test_raw_fallback_remains_in_every_baseline_case(self):
        raw = candidate.run(FIXTURE)
        self.assertTrue(all(r["raw_evidence_available"] for r in raw["rows"] if r["arm"] != "HIDE_RAW_EVIDENCE"))

    def test_auditor_detects_each_planted_mutant(self):
        result = auditor.audit(FIXTURE, ORACLE, candidate.run(FIXTURE))
        self.assertEqual(set(result["mutation_witness_counts"]), {"DROP_SOURCE_BINDING", "FLIP_EFFECT_LABEL", "SUPPRESS_UNKNOWN", "CARD_AS_AUTHORITY", "HIDE_RAW_EVIDENCE"})
        self.assertTrue(all(v > 0 for v in result["mutation_witness_counts"].values()))

    def test_delete_row_is_rejected(self):
        raw = candidate.run(FIXTURE)
        raw["rows"].pop()
        result = auditor.audit(FIXTURE, ORACLE, raw)
        self.assertTrue(any(e["kind"] == "denominator_mismatch" for e in result["errors"]))

    def test_duplicate_row_is_rejected(self):
        raw = candidate.run(FIXTURE)
        raw["rows"].append(copy.deepcopy(raw["rows"][0]))
        result = auditor.audit(FIXTURE, ORACLE, raw)
        self.assertTrue(any(e["kind"] == "duplicate_row" for e in result["errors"]))

    def test_false_completion_claim_is_rejected(self):
        raw = candidate.run(FIXTURE)
        row = next(r for r in raw["rows"] if r["case_id"] == "completion_not_observed" and r["arm"] == "CANDIDATE_EFFECT")
        row["completion"] = "COMPLETE"
        result = auditor.audit(FIXTURE, ORACLE, raw)
        self.assertTrue(any("completion_from_card" in e.get("violations", []) for e in result["errors"]))

    def test_canonical_effect_semantics_are_separate_from_oracle_effect(self):
        raw = candidate.run(FIXTURE)
        row = next(r for r in raw["rows"] if r["case_id"] == "current_genuine_modal" and r["arm"] == "CANDIDATE_EFFECT")
        self.assertEqual(row["effect_claim_status"], "UNVERIFIED")
        self.assertFalse(row["authority"])
        self.assertEqual(row["completion"], "NONE")

    def test_source_matched_wrong_effect_claim_stays_unverified(self):
        raw = candidate.run(FIXTURE)
        row = next(r for r in raw["rows"] if r["case_id"] == "completion_not_observed" and r["arm"] == "CANDIDATE_EFFECT")
        self.assertEqual(row["effect_claim"], "save_complete")
        self.assertEqual(row["effect_claim_status"], "UNVERIFIED")
        self.assertFalse(row["authority"])
        self.assertEqual(row["completion"], "NONE")
        result = auditor.audit(FIXTURE, ORACLE, raw)
        self.assertTrue(any(d["case_id"] == "completion_not_observed" and d["status"] == "UNVERIFIED" for d in result["unverified_effect_claim_disagreements"]))


if __name__ == "__main__":
    unittest.main()
