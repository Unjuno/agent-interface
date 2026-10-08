import copy
import unittest

import candidate
import audit


class PairedFrozenIntentTests(unittest.TestCase):
    def test_execution_oracle_has_same_frozen_intent_as_actual_arm(self):
        rows = {(r["case_id"], r["arm"]): r for r in candidate.build()["outcomes"]}
        for case in candidate.CASES:
            self.assertEqual(rows[case, "execution_oracle"]["model_intent"], rows[case, "actual"]["model_intent"])

    def test_execution_oracle_delivers_intent_without_repair(self):
        for row in candidate.build()["outcomes"]:
            if row["arm"] in ("execution_oracle", "joint"):
                self.assertEqual(row["executed_intent"], row["model_intent"])

    def test_planted_classes_and_nonidentifiable_controls(self):
        raw = candidate.build()
        rows = {(r["case_id"], r["arm"]): r for r in raw["outcomes"]}
        arms = candidate.ARMS
        expected = {
            "semantic_limited": (False, False, False, False),
            "observation_limited": (False, True, False, True),
            "execution_limited": (False, False, True, True),
            "joint_only": (False, False, False, True),
        }
        for case, vector in expected.items():
            self.assertEqual(tuple(rows[case, arm]["effect_correct"] for arm in arms), vector)
        self.assertTrue(all(rows["ambiguous", arm]["disposition"] == "UNDEFINED" for arm in arms))
        for arm in ("observation_oracle", "joint"):
            self.assertEqual(rows["answer_leakage", arm]["disposition"], "REJECTED_LEAKAGE")
            self.assertFalse(rows["answer_leakage", arm]["effect_correct"])

    def test_auditor_catches_paired_intent_mutation_even_when_locally_consistent(self):
        raw = candidate.build()
        altered = copy.deepcopy(raw)
        rows = {(r["case_id"], r["arm"]): r for r in altered["outcomes"]}
        exec_row = rows["semantic_limited", "execution_oracle"]
        exec_row["model_intent"] = exec_row["executed_intent"] = "requested_target"
        self.assertEqual(audit.audit(altered)["status"], "FAIL_METHOD")

    def test_clean_package_and_all_mutations(self):
        result = audit.audit(candidate.build())
        self.assertEqual(result["status"], "PASS_METHOD_SCOPED")
        self.assertEqual(result["mutation_controls_passed"], 8)
        self.assertEqual(result["errors"], [])


if __name__ == "__main__":
    unittest.main()
