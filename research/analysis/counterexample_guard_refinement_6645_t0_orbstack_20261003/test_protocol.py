import copy
import json
import unittest
from pathlib import Path

from auditor import audit
from candidate import run


FIXTURE = json.loads((Path(__file__).parent / "fixture.json").read_text())


class ProtocolTests(unittest.TestCase):
    def setUp(self):
        self.raw = run(FIXTURE)

    def test_independent_audit_accepts_candidate(self):
        result = audit(FIXTURE, self.raw)
        self.assertEqual(result["status"], "PASS", result["errors"])
        self.assertEqual(result["metrics"]["false_admissions"]["candidate"], 0)

    def test_incomparable_minima_are_preserved(self):
        self.assertEqual(self.raw["refinement_alternatives"],
                         [["effect_allowed"], ["epoch_current"], ["target_fresh"]])

    def test_heldout_families_refuse_and_common_control_admits(self):
        decisions = {r["id"]: r["decision"] for r in self.raw["rows"]}
        self.assertEqual(decisions["valid_common"], "ADMIT")
        for case_id in ("heldout_permission_denied", "heldout_target_stale", "heldout_epoch_stale"):
            self.assertNotEqual(decisions[case_id], "ADMIT")

    def test_out_of_envelope_and_no_fallback_fail_closed(self):
        decisions = {r["id"]: r["decision"] for r in self.raw["rows"]}
        self.assertEqual(decisions["out_of_scope"], "UNKNOWN_FALLBACK")
        self.assertEqual(decisions["unmodeled_family_no_fallback"], "STOP_NO_FALLBACK")

    def test_observationally_equivalent_safe_and_harmful_states_get_same_decision(self):
        decisions = {r["id"]: r["decision"] for r in self.raw["rows"]}
        self.assertEqual(decisions["valid_rare_alias"], decisions["heldout_target_stale"])
        self.assertEqual(decisions["valid_rare_alias"], "UNKNOWN_FALLBACK")

    def test_shared_dependency_invalidates_all_and_only_its_siblings(self):
        self.assertEqual(self.raw["cache_invalidation"],
                         {"shared": True, "sibling_a": True, "sibling_b": True, "sibling_c": False})

    def test_corrupt_counterexample_is_not_used_as_refinement_source(self):
        self.assertFalse(next(c for c in FIXTURE["cases"] if c["id"] == "spurious_oracle_corrupt")["replay_authenticated"])
        self.assertEqual(len(self.raw["refinement_alternatives"]), 3)

    def test_corrupt_training_lineage_stops_before_refinement(self):
        changed = copy.deepcopy(FIXTURE)
        ce = next(c for c in changed["cases"] if c.get("training"))
        ce["replay_authenticated"] = False
        with self.assertRaises(ValueError):
            run(changed)

    def test_mutated_false_admission_is_rejected(self):
        bad = copy.deepcopy(self.raw)
        next(r for r in bad["rows"] if r["id"] == "heldout_epoch_stale")["decision"] = "ADMIT"
        self.assertEqual(audit(FIXTURE, bad)["status"], "FAIL")

    def test_mutated_sibling_invalidation_is_rejected(self):
        bad = copy.deepcopy(self.raw)
        bad["cache_invalidation"]["sibling_b"] = False
        self.assertEqual(audit(FIXTURE, bad)["status"], "FAIL")

    def test_mutated_incomparable_option_tie_break_is_rejected(self):
        bad = copy.deepcopy(self.raw)
        bad["refinement_alternatives"] = [["effect_allowed"]]
        self.assertEqual(audit(FIXTURE, bad)["status"], "FAIL")

    def test_authority_or_replay_mutation_is_rejected(self):
        bad = copy.deepcopy(self.raw)
        bad["rows"][0]["task_input_replayed"] = True
        self.assertEqual(audit(FIXTURE, bad)["status"], "FAIL")

    def test_fixture_case_mutation_breaks_raw_audit(self):
        changed = copy.deepcopy(FIXTURE)
        changed["cases"][0]["features"]["effect_allowed"] = False
        self.assertEqual(audit(changed, self.raw)["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
