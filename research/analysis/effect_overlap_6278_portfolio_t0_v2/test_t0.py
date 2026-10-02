import copy
import json
import unittest
from pathlib import Path

import audit
import candidate


ROOT = Path(__file__).parent


class PortfolioTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((ROOT / "FIXTURE.json").read_text())
        cls.raw = candidate.run(cls.fixture)
        cls.expected = audit.expected(cls.fixture)

    def test_independent_exhaustive_design_and_assignment_oracles_agree(self):
        self.assertEqual(self.raw, self.expected)

    def test_all_comparator_classes_are_fairly_feasible_or_explicit(self):
        rows = self.raw["training_optimization"]
        self.assertEqual(set(rows), {"exact_copies", "disjoint_specialists", "partial_overlap", "universal_fallback"})
        for item in rows.values():
            self.assertEqual(item["status"], "OPTIMIZED")
            for design in item["designs"]:
                ids = design["portfolio"]
                routes = [next(r for r in self.fixture["route_options"] if r["id"] == rid) for rid in ids]
                self.assertEqual(sum(r["fixed_cost"] for r in routes), self.fixture["fixed_budget"])
                self.assertEqual(sum(r["capacity"] for r in routes), self.fixture["portfolio_capacity"])

    def test_positive_contention_control_favors_partial_overlap(self):
        control = self.raw["positive_bottleneck_control"]
        scores = control["aggregate_scores"]
        self.assertEqual(scores["partial_overlap"], 9)
        self.assertEqual(scores["disjoint_specialist"], 8)
        self.assertTrue(control["same_fixed_cost"])
        self.assertTrue(control["same_total_capacity"])

    def test_positive_control_exposes_actual_predeadline_reassignment(self):
        rows = self.raw["positive_bottleneck_control"]["scenario_results"]["partial_overlap"]["left_dependency_loss"]
        moved = [r for r in rows["rows"] if r["reassigned"] and r["task"].startswith("B")]
        self.assertEqual({r["route"] for r in moved}, {"p_bc"})
        self.assertTrue(all(r["finish_ms"] <= 4 for r in moved))
        self.assertEqual(rows["score"], 2)

    def test_universal_no_advantage_control_never_loses_to_partial(self):
        self.assertTrue(self.raw["dominance_control"])
        self.assertFalse(any(x["partial_strictly_better"] for x in self.raw["dominance_control"]))

    def test_fast_and_late_reassignment_same_graph_are_distinguished(self):
        selected = self.raw["training_optimization"]["partial_overlap"]["winner"]
        rows = self.raw["training_optimization"]["partial_overlap"]["heldout"]
        self.assertGreater(rows["fast_a11y_reassign"]["score"], rows["late_a11y_reassign"]["score"])
        self.assertTrue(selected)

    def test_short_disturbance_resumes_before_reconfiguration(self):
        rows = self.raw["training_optimization"]["partial_overlap"]["heldout"]["brief_observer_recovery"]
        self.assertGreater(rows["score"], 0)
        self.assertTrue(all(r["start_ms"] >= 1 for r in rows["rows"] if r["route"] is not None))
        self.assertTrue(all(r["finish_ms"] <= 4 for r in rows["rows"] if r["route"] is not None))

    def test_authority_unknown_effect_and_committed_partial_never_replay(self):
        rows = self.raw["training_optimization"]["partial_overlap"]["heldout"]["authority_and_commit_controls"]["rows"]
        by_id = {r["task"]: r for r in rows}
        self.assertEqual(by_id["B_unauthorized"]["status"], "UNAUTHORIZED")
        self.assertEqual(by_id["C_unknown"]["status"], "EFFECT_UNKNOWN_OR_PARTIAL")
        self.assertEqual(by_id["B_partial_committed"]["status"], "ALREADY_COMMITTED_NO_REPLAY")
        self.assertIsNone(by_id["B_partial_committed"]["route"])

    def test_mandatory_empty_release_is_not_delayed(self):
        rel = self.raw["hard_release"]
        self.assertEqual(rel["state"], "empty")
        self.assertEqual(rel["issued_ms"], 0)
        self.assertLessEqual(rel["completed_ms"], rel["deadline_ms"])

    def test_heldout_scenarios_do_not_select_the_training_winners(self):
        no_heldout = copy.deepcopy(self.fixture)
        no_heldout["heldout_scenarios"] = []
        control = candidate.run(no_heldout)["training_optimization"]
        for kind, current in self.raw["training_optimization"].items():
            self.assertEqual(current["winner"], control[kind]["winner"])
            self.assertEqual(current["designs"], control[kind]["designs"])

    def test_mutations_of_denominator_edge_authority_and_release_rejected(self):
        mutants = []
        x = copy.deepcopy(self.raw)
        x["training_optimization"]["partial_overlap"]["heldout"]["authority_and_commit_controls"]["rows"].pop()
        mutants.append(x)
        x = copy.deepcopy(self.raw)
        row = next(r for r in x["training_optimization"]["partial_overlap"]["heldout"]["authority_and_commit_controls"]["rows"] if r["task"] == "B_unauthorized")
        row.update(route="ab1", start_ms=0, finish_ms=2, status="EXACT_ON_TIME", reassigned=True)
        mutants.append(x)
        x = copy.deepcopy(self.raw)
        row = next(r for r in x["training_optimization"]["partial_overlap"]["heldout"]["authority_and_commit_controls"]["rows"] if r["task"] == "B_partial_committed")
        row.update(route="ab1", start_ms=0, finish_ms=2, status="EXACT_ON_TIME", reassigned=True)
        mutants.append(x)
        x = copy.deepcopy(self.raw)
        row = next(r for r in x["training_optimization"]["partial_overlap"]["heldout"]["authority_and_commit_controls"]["rows"] if r["task"] == "A1")
        row.update(route="bc_partial1", start_ms=0, finish_ms=2, status="EXACT_ON_TIME", reassigned=True)
        mutants.append(x)
        x = copy.deepcopy(self.raw)
        x["positive_bottleneck_control"]["aggregate_scores"]["partial_overlap"] += 1
        mutants.append(x)
        x = copy.deepcopy(self.raw)
        x["hard_release"]["completed_ms"] = 2
        mutants.append(x)
        x = copy.deepcopy(self.raw)
        x["training_optimization"]["partial_overlap"]["winner"] = ["bc_partial1", "a2"]
        mutants.append(x)
        for mutant in mutants:
            errors, _ = audit.validate(mutant, self.fixture)
            self.assertTrue(errors)


if __name__ == "__main__":
    unittest.main()
