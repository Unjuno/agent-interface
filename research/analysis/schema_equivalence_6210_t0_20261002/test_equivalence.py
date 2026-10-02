"""Behavioral tests for finite tool-schema equivalence certification."""
import unittest
import hashlib
from pathlib import Path

from candidate import SURFACES, boundary_profile, execute_case, expand_calls, load_fixture, certify_surfaces


class SchemaEquivalenceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = load_fixture()
        cls.context = cls.fixture["context"]

    def test_stale_evidence_is_rejected_before_any_input_or_effect(self):
        case = next(x for x in self.fixture["cases"] if x["id"] == "wrong_epoch_authorized_target_no_cancel")
        result = execute_case(case, SURFACES["canonical"], self.context)
        self.assertEqual("YIELD_STALE_EVIDENCE", result["terminal"]["decision"])
        self.assertTrue(result["terminal"]["input_empty"])
        self.assertEqual(0, result["terminal"]["effect_count"])
        self.assertNotIn("KEY_DOWN", result["events"])

    def test_wrong_target_is_denied_before_input_or_effect(self):
        case = next(x for x in self.fixture["cases"] if x["id"] == "wrong_target_current_epoch_no_cancel")
        result = execute_case(case, SURFACES["canonical"], self.context)
        self.assertEqual("YIELD_WRONG_TARGET", result["terminal"]["decision"])
        self.assertEqual(0, result["terminal"]["effect_count"])
        self.assertNotIn("KEY_DOWN", result["events"])

    def test_cancel_after_text_still_releases_and_never_submits(self):
        case = next(x for x in self.fixture["cases"] if x["id"] == "authorized_current_epoch_cancel")
        result = execute_case(case, SURFACES["canonical"], self.context)
        self.assertEqual("CANCELLED_NO_EFFECT", result["terminal"]["decision"])
        self.assertTrue(result["terminal"]["input_empty"])
        self.assertEqual(0, result["terminal"]["effect_count"])
        self.assertIn("KEY_UP_CANCEL_CLEANUP", result["events"])

    def test_only_semantically_identical_surfaces_are_certified(self):
        decisions = certify_surfaces(self.fixture)
        expected = {
            "canonical": True,
            "renamed_fields": True,
            "split_same_checkpoints": False,
            "merged_with_full_trace": False,
            "skip_freshness_guard": False,
            "alias_wrong_target": False,
            "omit_release": False,
            "hide_intermediate_release_state": False,
        }
        self.assertEqual(expected, decisions)
        self.assertEqual([1, 3, 2], boundary_profile(SURFACES["canonical"]))
        self.assertEqual([1, 3, 2], boundary_profile(SURFACES["renamed_fields"]))
        self.assertNotEqual(boundary_profile(SURFACES["canonical"]), boundary_profile(SURFACES["split_same_checkpoints"]))
        self.assertNotEqual(boundary_profile(SURFACES["canonical"]), boundary_profile(SURFACES["merged_with_full_trace"]))

    def test_independent_oracle_reconstructs_rows_and_rejects_authority_mutation(self):
        from audit import audit

        fixture_bytes = (Path(__file__).parent / "fixture.json").read_bytes()
        candidate_bytes = (Path(__file__).parent / "candidate.py").read_bytes()
        decisions = certify_surfaces(self.fixture)
        raw = {
            "schema": "schema-equivalence-raw-v1",
            "allocation": self.fixture["allocation"],
            "source_main": self.fixture["source_main"],
            "fixture_sha256": hashlib.sha256(fixture_bytes).hexdigest(),
            "candidate_sha256": hashlib.sha256(candidate_bytes).hexdigest(),
            "surface_decisions": decisions,
            "rows": [],
        }
        for surface_id, surface in SURFACES.items():
            for case in self.fixture["cases"]:
                raw["rows"].append({
                    "surface_id": surface_id,
                    "case_id": case["id"],
                    "input": {
                        surface["target_field"]: case["target_id"],
                        surface["epoch_field"]: case["evidence_epoch"],
                        "cancel_after_type": case["cancel_after_type"],
                    },
                    "tool_calls": surface["calls"],
                    "boundary_profile": boundary_profile(surface),
                    "expanded_primitives": expand_calls(surface),
                    **execute_case(case, surface, self.context),
                    "certified_equivalent": decisions[surface_id],
                    "authority_granted": False,
                })
        self.assertEqual([], audit(raw, self.fixture, fixture_bytes, candidate_bytes))
        raw["rows"][0]["authority_granted"] = True
        self.assertTrue(audit(raw, self.fixture, fixture_bytes, candidate_bytes))


if __name__ == "__main__":
    unittest.main()
