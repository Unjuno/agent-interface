import copy
import unittest

import audit
import candidate


class OracleBoundarySwapTests(unittest.TestCase):
    def test_four_arms_identify_the_planted_boundary_classes(self):
        raw = candidate.build()
        by_case_arm = {(r["case_id"], r["arm"]): r for r in raw["outcomes"]}
        expected = {
            "semantic_limited": (False, False, False, False),
            "observation_limited": (False, True, False, True),
            "execution_limited": (False, False, True, True),
            "joint_only": (False, False, False, True),
        }
        arms = ("actual", "observation_oracle", "execution_oracle", "joint")
        for case_id, outcomes in expected.items():
            self.assertEqual(tuple(by_case_arm[case_id, arm]["effect_correct"] for arm in arms), outcomes)

    def test_execution_oracle_preserves_frozen_semantic_intent(self):
        raw = candidate.build()
        for row in raw["outcomes"]:
            if row["arm"] in ("execution_oracle", "joint"):
                self.assertEqual(row["executed_intent"], row["model_intent"])

    def test_ambiguous_oracle_and_answer_leakage_are_not_scored_as_success(self):
        raw = candidate.build()
        selected = [r for r in raw["outcomes"] if r["case_id"] in ("ambiguous", "answer_leakage")]
        self.assertTrue(all(r["disposition"] == "UNDEFINED" for r in selected if r["case_id"] == "ambiguous"))
        leaked = [r for r in selected if r["case_id"] == "answer_leakage" and r["arm"] in ("observation_oracle", "joint")]
        self.assertTrue(all(not r["oracle_admissible"] and not r["effect_correct"] for r in leaked))

    def test_reset_and_safety_gates_fail_closed_and_audit_passes(self):
        raw = candidate.build()
        self.assertEqual(audit.audit(raw)["status"], "PASS_METHOD_SCOPED")
        contaminated = copy.deepcopy(raw)
        contaminated["outcomes"][4]["initial_state_digest"] = "prior-arm-state"
        self.assertEqual(audit.audit(contaminated)["status"], "FAIL_METHOD")

    def test_oracle_cannot_bypass_safety_or_inject_plan_or_authorization(self):
        raw = candidate.build()
        for row in raw["outcomes"]:
            self.assertFalse(row["safety_bypassed"])
            if row["arm"] in ("observation_oracle", "joint") and row["case_id"] != "answer_leakage":
                self.assertFalse(row["oracle_contains_answer"])
                self.assertFalse(row["oracle_contains_plan"])
                self.assertFalse(row["oracle_contains_authorization"])

    def test_mutations_are_rejected(self):
        raw = candidate.build()
        result = audit.audit(raw)
        self.assertEqual(result["mutation_controls_passed"], 7)
        self.assertEqual(result["errors"], [])


if __name__ == "__main__":
    unittest.main()
