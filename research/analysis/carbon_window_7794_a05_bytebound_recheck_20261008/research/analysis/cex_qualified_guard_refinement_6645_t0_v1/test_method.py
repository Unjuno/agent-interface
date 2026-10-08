"""Construction and corruption controls; not the formal WSLc allocation."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

import auditor
import candidate


ROOT = Path(__file__).resolve().parent
FIXTURE = json.loads((ROOT / "fixture.json").read_text(encoding="utf-8"))


class GuardRefinementConstruction(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.raw = candidate.run(FIXTURE)
        cls.audit = auditor.audit(FIXTURE, cls.raw)

    def test_exact_finite_inventory_and_independent_reconstruction(self) -> None:
        self.assertEqual(len(FIXTURE["state_inventory"]), 11)
        self.assertEqual(self.audit["audit_status"], "PASS_METHOD_SCOPED", self.audit["errors"])
        self.assertEqual(self.audit["raw_counterexample_events"], len(FIXTURE["counterexamples"]))

    def test_only_replay_qualified_real_misses_refine(self) -> None:
        events = {row["counterexample_id"]: row for row in self.raw["counterexample_events"]}
        self.assertEqual(events["ce_real_dual"]["result"], "REFINEMENT_ALTERNATIVES_RETAINED")
        for name in ("ce_spurious", "ce_out_of_scope", "ce_unresolved"):
            self.assertEqual(events[name]["candidate_terms"], [])
            self.assertEqual(events[name]["result"], "NO_REFINEMENT_NONREAL")

    def test_hidden_family_alias_is_unknown_not_false_pass(self) -> None:
        decisions = self.raw["decisions"]
        self.assertEqual(decisions["safe_alias_hidden_family"], "UNKNOWN")
        self.assertEqual(decisions["harmful_alias_hidden_family"], "UNKNOWN")
        self.assertEqual(decisions["safe_rare_control"], "UNKNOWN")
        self.assertEqual(decisions["harmful_source_stale"], "UNKNOWN")

    def test_two_incomparable_minimal_refinements_are_preserved(self) -> None:
        actual = sorted(item["terms"] for item in self.raw["refinement_alternatives"])
        self.assertEqual(actual, [["context_current"], ["focus_current"]])
        self.assertEqual(self.raw["decisions"]["harmful_dual_miss"], "REFUSE_AND_DEOPT")
        self.assertEqual(self.raw["decisions"]["safe_common_a"], "ADMIT")

    def test_candidate_closes_false_admissions_left_by_unchanged_and_exact_blacklist(self) -> None:
        comparison = self.audit["arm_comparison"]
        self.assertGreater(comparison["UNCHANGED_GUARD"]["harmful_admitted"], 0)
        self.assertGreater(comparison["EXACT_STATE_BLACKLIST"]["harmful_admitted"], 0)
        self.assertEqual(comparison["CANDIDATE_REFINEMENT"]["harmful_admitted"], 0)
        self.assertEqual(comparison["ORACLE_MINIMAL_DIAGNOSTIC"]["harmful_admitted"], 0)

    def test_changed_predicates_invalidate_all_dependent_siblings_only(self) -> None:
        cache = self.raw["cache_invalidation"]
        self.assertEqual(cache["invalidated"], ["cache_skill_a_shape1", "cache_skill_b_shape2"])
        self.assertEqual(cache["retained"], ["cache_skill_c_independent"])

    def test_missing_generic_fallback_holds_without_authority_expansion(self) -> None:
        self.assertEqual(self.raw["decisions"]["safe_unresolved_class"], "HOLD_NO_SAFE_FALLBACK")
        self.assertEqual(self.raw["decisions"]["harmful_unresolved_class"], "HOLD_NO_SAFE_FALLBACK")
        self.assertEqual(self.raw["fallback"]["authority_before"], self.raw["fallback"]["authority_after"])
        self.assertEqual(self.raw["fallback"]["task_input_replays"], 0)

    def test_auditor_rejects_spurious_trace_used_as_refinement(self) -> None:
        corrupt = copy.deepcopy(self.raw)
        next(row for row in corrupt["counterexample_events"] if row["counterexample_id"] == "ce_spurious")["candidate_terms"] = ["modal_clear"]
        self.assertEqual(auditor.audit(FIXTURE, corrupt)["audit_status"], "HOLD_AUDIT_INTEGRITY")

    def test_auditor_rejects_hidden_harmful_state_admission(self) -> None:
        corrupt = copy.deepcopy(self.raw)
        corrupt["decisions"]["harmful_alias_hidden_family"] = "ADMIT"
        self.assertEqual(auditor.audit(FIXTURE, corrupt)["audit_status"], "HOLD_AUDIT_INTEGRITY")

    def test_auditor_rejects_lost_valid_rare_control(self) -> None:
        corrupt = copy.deepcopy(self.raw)
        corrupt["decisions"]["safe_rare_control"] = "REFUSE_AND_DEOPT"
        self.assertEqual(auditor.audit(FIXTURE, corrupt)["audit_status"], "HOLD_AUDIT_INTEGRITY")

    def test_auditor_rejects_missed_sibling_invalidation(self) -> None:
        corrupt = copy.deepcopy(self.raw)
        corrupt["cache_invalidation"]["invalidated"].remove("cache_skill_b_shape2")
        self.assertEqual(auditor.audit(FIXTURE, corrupt)["audit_status"], "HOLD_AUDIT_INTEGRITY")

    def test_auditor_rejects_fallback_authority_or_task_replay(self) -> None:
        for key, value in (("authority_after", 1), ("task_input_replays", 1)):
            corrupt = copy.deepcopy(self.raw)
            corrupt["fallback"][key] = value
            self.assertEqual(auditor.audit(FIXTURE, corrupt)["audit_status"], "HOLD_AUDIT_INTEGRITY")

    def test_candidate_payload_does_not_publish_truth_oracle(self) -> None:
        self.assertNotIn("oracle_diagnostic", self.raw)
        self.assertNotIn("truth_errors", self.raw)
        self.assertNotIn("oracle", self.raw)


if __name__ == "__main__":
    unittest.main()
