import copy
import json
import unittest
from pathlib import Path

from audit import read_jsonl, verify

HERE = Path(__file__).parent


class BundledEffectT0bContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = json.loads((HERE / "cases.json").read_text(encoding="utf-8"))
        cls.oracle = json.loads((HERE / "oracle.json").read_text(encoding="utf-8"))
        cls.decisions = read_jsonl(HERE / "results" / "decisions.jsonl")
        cls.events = read_jsonl(HERE / "results" / "effect_events.jsonl")
        cls.result = verify(cls.cases, cls.oracle, cls.decisions, cls.events)

    def test_same_target_geometry_is_bound_through_click(self):
        self.assertEqual(self.cases["target"], self.oracle["target_at_click"])
        self.assertEqual(len(self.cases["cases"]), 8)

    def test_pre_admission_flip_is_blocked_by_effect_gate_not_target_gate(self):
        lookup = {(r["case_id"], r["policy"]): r for r in self.decisions}
        self.assertEqual(lookup[("pre_admission_flip", "TARGET_ONLY")]["action"], "click")
        self.assertEqual(lookup[("pre_admission_flip", "FRESH_EFFECT_BOUNDARY")]["admission"], "BLOCK_UNAUTHORIZED_ADDON")

    def test_unknown_stale_and_integrity_invalid_effect_state_yield(self):
        lookup = {(r["case_id"], r["policy"]): r for r in self.decisions}
        for case_id in ("effect_state_unavailable", "stale_effect_generation", "effect_read_integrity_mismatch"):
            self.assertEqual(lookup[(case_id, "FRESH_EFFECT_BOUNDARY")]["admission"], "YIELD_UNKNOWN")

    def test_stable_and_explicitly_authorized_paths_are_not_suppressed(self):
        lookup = {(r["case_id"], r["policy"]): r for r in self.decisions}
        self.assertEqual(lookup[("stable_unchecked_default", "FRESH_EFFECT_BOUNDARY")]["action"], "click")
        self.assertEqual(lookup[("authorized_deceptive_optin", "FRESH_EFFECT_BOUNDARY")]["action"], "click")
        event = next(e for e in self.events if e["case_id"] == "authorized_deceptive_optin" and e["policy"] == "FRESH_EFFECT_BOUNDARY")
        self.assertTrue(event["addon_applied"] and event["addon_authorized"])

    def test_post_admission_flip_remains_an_explicit_residual_race(self):
        row = next(e for e in self.events if e["case_id"] == "post_admission_flip" and e["policy"] == "FRESH_EFFECT_BOUNDARY")
        self.assertTrue(row["residual_race"] and row["unauthorized_addon"])
        self.assertEqual(self.result["residual_post_admission_races"], 1)

    def test_candidate_decisions_do_not_expose_scorer_oracle_fields(self):
        self.assertTrue(all("selected_at_click" not in d and "unauthorized_addon" not in d for d in self.decisions))

    def test_independent_audit_passes_with_residual_boundary_labeled(self):
        self.assertEqual(self.result["disposition"], "METHOD_PASS_SCOPED_WITH_RESIDUAL_RACE")
        self.assertEqual(self.result["errors"], [])
        self.assertEqual(self.result["unauthorized_addons"], {"PLAIN": 5, "TARGET_ONLY": 5, "FRESH_EFFECT_BOUNDARY": 1})

    def test_mutated_pre_admission_decision_is_rejected(self):
        mutated = copy.deepcopy(self.decisions)
        row = next(d for d in mutated if d["case_id"] == "pre_admission_flip" and d["policy"] == "FRESH_EFFECT_BOUNDARY")
        row["action"], row["admission"], row["reason"] = "click", "ADMIT", "forged"
        checked = verify(self.cases, self.oracle, mutated, self.events)
        self.assertTrue(checked["errors"])

    def test_mutated_residual_effect_cannot_be_reclassified_as_safe(self):
        mutated = copy.deepcopy(self.events)
        row = next(e for e in mutated if e["case_id"] == "post_admission_flip" and e["policy"] == "FRESH_EFFECT_BOUNDARY")
        row["unauthorized_addon"] = False
        checked = verify(self.cases, self.oracle, self.decisions, mutated)
        self.assertTrue(checked["errors"])

    def test_mutated_effect_digest_invalidates_current_read(self):
        mutated = copy.deepcopy(self.cases)
        case = next(c for c in mutated["cases"] if c["id"] == "stable_unchecked_default")
        case["read_digest"] = "0" * 64
        checked = verify(mutated, self.oracle, self.decisions, self.events)
        self.assertTrue(checked["errors"])


if __name__ == "__main__":
    unittest.main()
