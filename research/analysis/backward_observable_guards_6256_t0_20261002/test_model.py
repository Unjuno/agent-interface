import unittest

import candidate


class BackwardGuardConstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import json
        from pathlib import Path
        cls.model = json.loads((Path(__file__).resolve().parent / "MODEL.json").read_text(encoding="utf-8"))
        cls.result = candidate.build_result(cls.model)

    def test_universal_total_correctness_preimage(self):
        self.assertEqual(self.result["preimage_state_ids"], ["ready_complex", "ready_simple", "unobservable_safe_alias"])

    def test_nondeterministic_save_no_effect_is_not_in_preimage(self):
        row = next(r for r in self.result["outcome_rows"] if r["outcome"]["id"] == "intermittent_no_effect")
        self.assertFalse(row["passes_total_correctness"])
        self.assertNotIn("unreliable_effect_contract", self.result["preimage_state_ids"])

    def test_pixel_only_alias_is_unknown_but_fresh_commit_receipt_separates_pair(self):
        self.assertEqual(self.result["pixel_only_ready_vs_committed"], "UNKNOWN_NOT_OBSERVABLE")
        decisions = {tuple(row["signature"]): row["decision"] for row in self.result["fresh_typed_commit_receipt_pair"]["signatures"]}
        self.assertEqual(set(decisions.values()), {"ADMIT", "REFUSE"})

    def test_unobservable_effect_alias_remains_unknown(self):
        rows = [r for r in self.result["full_cue_decisions"] if set(r["state_ids"]) == {"unobservable_safe_alias", "unobservable_silent_alias"}]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["decision"], "UNKNOWN_NOT_OBSERVABLE")
        self.assertFalse(self.result["full_model_global_sufficient_cue_set_exists"])

    def test_authored_guard_has_missing_predicates_and_overstrong_guard_rejects_safe_layout(self):
        self.assertTrue(self.result["authored_guard_unsafe_admissions"])
        self.assertIn("ready_complex", self.result["authored_guard_safe_rejections"])
        self.assertIn("ready_complex", self.result["overstrong_guard_safe_rejections"])

    def test_verified_stratum_has_minimum_observable_cue_set(self):
        cues = self.result["verified_stratum_minimum_sufficient_cue_sets"]
        self.assertTrue(cues)
        self.assertEqual(len(cues[0]), 6)

    def test_independent_auditor_agrees_on_construction_object(self):
        import audit
        checked = audit.audit(self.model, self.result)
        self.assertEqual(checked["decision"], "PASS_METHOD_SCOPED")
        self.assertEqual(checked["errors"], [])


if __name__ == "__main__":
    unittest.main()
