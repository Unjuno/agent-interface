import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from candidate import choose
from design import build


class ConstructionTests(unittest.TestCase):
    def test_fixture_is_exhaustive_and_adds_nonisomorphic_shapes(self):
        workload, oracle = build()
        self.assertEqual(len(workload["cases"]), 132)
        self.assertEqual(set(oracle["topologies"]), {"cycle3", "branch_merge", "asymmetric4"})
        signatures = set()
        for graph in oracle["topologies"].values():
            indegree = {node: 0 for node in graph["states"]}
            outdegree = []
            for edges in graph["edges"].values():
                outdegree.append(len(edges))
                for target in edges.values():
                    indegree[target] += 1
            signatures.add((len(graph["states"]), tuple(sorted(outdegree)),
                            tuple(sorted(indegree.values()))))
        self.assertEqual(len(signatures), 3)

    def test_budget_and_model_prediction_control_selection(self):
        workload, _ = build()
        cases = workload["cases"]
        correct_affordable = next(c for c in cases if c["topology"] == "cycle3" and
                                  c["state"] == "c0" and c["preexisting_witness"] is False and
                                  c["predicted_witness_survival"]["action-b"] and
                                  c["preservation_cost"]["action-b"] == 1)
        wrong_model = next(c for c in cases if c["topology"] == "cycle3" and
                           c["state"] == "c0" and c["preexisting_witness"] is False and
                           not c["predicted_witness_survival"]["action-b"] and
                           c["preservation_cost"]["action-b"] == 1)
        over_budget = next(c for c in cases if c["topology"] == "cycle3" and
                           c["state"] == "c0" and c["preexisting_witness"] is False and
                           c["predicted_witness_survival"]["action-b"] and
                           c["preservation_cost"]["action-b"] == 2)
        self.assertEqual(choose(correct_affordable, True), "action-b")
        self.assertEqual(choose(wrong_model, True), "action-a")
        self.assertEqual(choose(over_budget, True), "action-a")

    def test_existing_witness_avoids_reranking(self):
        workload, _ = build()
        case = next(c for c in workload["cases"] if c["preexisting_witness"])
        self.assertEqual(choose(case, True), min(case["admissible_actions"]))


if __name__ == "__main__":
    unittest.main()
