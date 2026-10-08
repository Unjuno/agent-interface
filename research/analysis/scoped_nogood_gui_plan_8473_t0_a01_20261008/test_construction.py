import copy
import json
import unittest
from pathlib import Path

import auditor
import candidate


class ScopedNoGoodConstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = json.loads(Path("candidate_inputs.json").read_text(encoding="utf-8"))
        cls.oracle = json.loads(Path("oracle.json").read_text(encoding="utf-8"))
        cls.raw = candidate.run(cls.source)

    def test_independent_oracle_gate(self):
        result = auditor.audit(self.source, self.oracle, self.raw)
        self.assertEqual(result["status"], "PASS_METHOD_SCOPED", result["errors"])
        self.assertEqual(result["runs"], 21)

    def test_scoped_feedback_saves_duplicate_queries_and_keeps_alternatives(self):
        rows = {(x["scenario"], x["policy"]): x for x in self.raw["runs"]}
        for scenario in ("occlusion_rearrangement", "focus_recovery"):
            baseline = rows[(scenario, "NO_FEEDBACK")]
            scoped = rows[(scenario, "SCOPED_NOGOOD")]
            self.assertEqual(baseline["duplicate_infeasible_queries"], 1)
            self.assertEqual(scoped["duplicate_infeasible_queries"], 0)
            self.assertEqual(scoped["terminal"], "EFFECT")

    def test_generation_change_invalidates_scoped_reason(self):
        row = next(x for x in self.raw["runs"]
                   if x["scenario"] == "transient_blocker_clears" and x["policy"] == "SCOPED_NOGOOD")
        self.assertEqual(row["terminal"], "EFFECT")
        self.assertFalse(any(a.get("status") == "PRUNED" for a in row["attempts"]))

    def test_timeout_is_rechecked_not_learned_as_infeasible(self):
        row = next(x for x in self.raw["runs"]
                   if x["scenario"] == "timeout_then_recheck" and x["policy"] == "SCOPED_NOGOOD")
        self.assertEqual([x["status"] for x in row["attempts"]], ["TIMEOUT", "FEASIBLE"])
        self.assertEqual(row["terminal"], "EFFECT")

    def test_expired_nogood_is_rechecked_even_without_generation_change(self):
        row = next(x for x in self.raw["runs"]
                   if x["scenario"] == "constraint_expires" and x["policy"] == "SCOPED_NOGOOD")
        self.assertEqual([x["status"] for x in row["attempts"]], ["INFEASIBLE", "FEASIBLE"])
        self.assertEqual(row["terminal"], "EFFECT")

    def test_unmodeled_failure_yields_recheck_without_learning(self):
        row = next(x for x in self.raw["runs"]
                   if x["scenario"] == "unknown_then_recheck" and x["policy"] == "SCOPED_NOGOOD")
        self.assertEqual([x["status"] for x in row["attempts"]], ["UNKNOWN", "FEASIBLE"])
        self.assertEqual(row["pruned_plans"], 0)

    def test_global_blacklist_is_a_diagnostic_overpruning_control(self):
        rows = {(x["scenario"], x["policy"]): x for x in self.raw["runs"]}
        self.assertEqual(rows[("occlusion_rearrangement", "GLOBAL_BLACKLIST")]["terminal"], "NO_PLAN")
        self.assertEqual(rows[("occlusion_rearrangement", "SCOPED_NOGOOD")]["terminal"], "EFFECT")

    def test_raw_mutation_is_rejected(self):
        changed = copy.deepcopy(self.raw)
        row = next(x for x in changed["runs"]
                   if x["scenario"] == "transient_blocker_clears" and x["policy"] == "SCOPED_NOGOOD")
        row["terminal"] = "NO_PLAN"
        self.assertTrue(auditor.audit(self.source, self.oracle, changed)["errors"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
