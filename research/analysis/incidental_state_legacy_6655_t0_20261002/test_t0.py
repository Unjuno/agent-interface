"""Construction and mutation tests; formal candidate/auditor are separate later invocations."""

import copy
import unittest

import audit
import candidate


class IncidentalStateT0Tests(unittest.TestCase):
    def setUp(self):
        self.raw = candidate.build_records()

    def row(self, case_id, seed=1):
        return next(row for row in self.raw["rows"] if row["case_id"] == case_id and row["seed"] == seed)

    def test_control_reconstructs_all_seeded_cases(self):
        result = audit.audit(self.raw)
        self.assertEqual("PASS_METHOD_SCOPED", result["status"])
        self.assertEqual([], result["errors"])
        self.assertEqual(224, result["rows"])
        self.assertTrue(all(count == 32 for count in result["seeds_per_case"].values()))

    def test_helpful_and_harmful_incidental_state_are_both_detected(self):
        summary = audit.audit(self.raw)["descriptive_summary"]
        self.assertLess(summary["helpful_incidental_view"]["inherit_mean_observations"],
                        summary["helpful_incidental_view"]["reset_mean_observations"])
        self.assertLess(summary["harmful_stale_filter"]["inherit_correct_rate"],
                        summary["harmful_stale_filter"]["reset_correct_rate"])

    def test_required_effect_is_preserved_in_both_arms(self):
        row = self.row("required_saved_effect")
        self.assertTrue(all(arm["state_after_treatment"]["saved_record"] for arm in row["arms"]))

    def test_required_effect_relabel_mutation_is_rejected(self):
        raw = copy.deepcopy(self.raw)
        row = next(x for x in raw["rows"] if x["case_id"] == "required_saved_effect")
        row["state_diff"][0]["classification"] = "incidental"
        self.assertIn("state_diff", audit.audit(raw)["errors"])

    def test_omitted_changed_field_is_rejected(self):
        raw = copy.deepcopy(self.raw)
        self.row_from(raw, "harmful_stale_filter")["state_diff"] = []
        self.assertIn("state_diff", audit.audit(raw)["errors"])

    def test_cross_paired_task_seed_is_rejected(self):
        raw = copy.deepcopy(self.raw)
        row = next(x for x in raw["rows"] if x["case_id"] == "helpful_incidental_view")
        reset = next(a for a in row["arms"] if a["arm"] == "reset")
        reset["later_task_seed"] += 1
        self.assertIn("later_task_seed", audit.audit(raw)["errors"])

    def test_incomplete_restore_cannot_be_promoted(self):
        raw = copy.deepcopy(self.raw)
        row = self.row_from(raw, "incomplete_restoration")
        reset = next(a for a in row["arms"] if a["arm"] == "reset")
        reset["restoration"]["complete"] = True
        self.assertIn("ineligible_restore_record", audit.audit(raw)["errors"])

    def test_shared_external_state_is_ineligible(self):
        raw = copy.deepcopy(self.raw)
        row = self.row_from(raw, "shared_external_state")
        row["eligible"] = True
        self.assertIn("eligibility", audit.audit(raw)["errors"])

    def test_assignment_order_mutation_is_rejected(self):
        raw = copy.deepcopy(self.raw)
        row = self.row_from(raw, "irrelevant_theme")
        row["assignment_order"].reverse()
        self.assertIn("randomization", audit.audit(raw)["errors"])

    @staticmethod
    def row_from(raw, case_id, seed=1):
        return next(row for row in raw["rows"] if row["case_id"] == case_id and row["seed"] == seed)


if __name__ == "__main__":
    unittest.main()
