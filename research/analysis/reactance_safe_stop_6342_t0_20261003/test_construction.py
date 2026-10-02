import json
import pathlib
import unittest


ROOT = pathlib.Path(__file__).parent


class FrozenT0Construction(unittest.TestCase):
    def test_fixture_declares_four_cases_and_two_framings(self):
        fixture = json.loads((ROOT / "cards.json").read_text())
        self.assertEqual(
            {case["case_id"] for case in fixture["cases"]},
            {"uncertain_save_delivery", "stale_target", "partial_edit", "verified_success_control"},
        )
        self.assertEqual(set(fixture["framing"]), {"directive", "autonomy_supportive"})

    def test_primary_pair_word_burdens_are_preregistered_equal(self):
        fixture = json.loads((ROOT / "cards.json").read_text())
        self.assertEqual(len(fixture["framing"]["directive"].split()), 8)
        self.assertEqual(len(fixture["framing"]["autonomy_supportive"].split()), 8)

    def test_unresolved_cases_have_no_success_claim_or_retry_option(self):
        fixture = json.loads((ROOT / "cards.json").read_text())
        for case in fixture["cases"]:
            if case["state"] != "verified_success":
                self.assertNotIn("retry", " ".join(case["allowed_actions"]).lower())
                self.assertNotIn("successfully", case["evidence"].lower())

    def test_accessibility_contract_has_textual_order_and_no_color_or_icon_only_cues(self):
        fixture = json.loads((ROOT / "cards.json").read_text())
        access = fixture["accessibility_contract"]
        self.assertTrue(access["text_only"])
        self.assertFalse(access["color_only_encoding"])
        self.assertFalse(access["icon_only_actions"])
        self.assertEqual(len(access["reading_order"]), 7)

    def test_negative_controls_are_distinct_and_preserve_unresolved_case(self):
        fixture = json.loads((ROOT / "cards.json").read_text())
        self.assertEqual(
            {control["control_id"] for control in fixture["negative_controls"]},
            {"mutation_permits_forbidden_retry", "mutation_claims_unverified_success"},
        )
        unresolved = next(case for case in fixture["cases"] if case["case_id"] == "uncertain_save_delivery")
        self.assertIn("has not arrived", unresolved["evidence"])

    def test_formal_programs_are_syntax_valid_without_invocation(self):
        for filename in ("render_cards.py", "audit_cards.py"):
            compile((ROOT / filename).read_text(), filename, "exec")


if __name__ == "__main__":
    unittest.main()
