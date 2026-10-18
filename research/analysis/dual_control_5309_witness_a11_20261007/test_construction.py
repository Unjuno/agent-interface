import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from candidate import choose
from design import build


class ConstructionTests(unittest.TestCase):
    def test_topologies_change_the_action_to_witness_mapping(self):
        workload, oracle = build()
        signatures = set()
        for graph in oracle["topologies"].values():
            signatures.add(tuple((s, tuple(a for a, d in edges.items()
                                          if d == graph["witness_state"]))
                                 for s, edges in sorted(graph["edges"].items())))
        self.assertEqual(len(signatures), 3)
        self.assertEqual(len(workload["cases"]), 132)

    def test_cost_and_misspecification_controls(self):
        workload, _ = build()
        cases = workload["cases"]
        correct_b = next(c for c in cases if c["topology"] == "cycle3" and c["state"] == "c2"
                         and not c["preexisting_witness"] and c["preservation_cost"]["action-b"] == 1
                         and c["predicted_witness_survival"]["action-b"])
        wrong_b = next(c for c in cases if c["topology"] == "cycle3" and c["state"] == "c2"
                       and not c["preexisting_witness"] and c["preservation_cost"]["action-b"] == 1
                       and not c["predicted_witness_survival"]["action-b"])
        expensive_b = next(c for c in cases if c["topology"] == "cycle3" and c["state"] == "c2"
                           and not c["preexisting_witness"] and c["preservation_cost"]["action-b"] == 2
                           and c["predicted_witness_survival"]["action-b"])
        self.assertEqual(choose(correct_b, True), "action-b")
        self.assertEqual(choose(wrong_b, True), "action-a")
        self.assertEqual(choose(expensive_b, True), "action-a")

    def test_same_admissible_set_and_prior_witness_control(self):
        workload, _ = build()
        self.assertEqual({tuple(c["admissible_actions"]) for c in workload["cases"]},
                         {("action-a", "action-b")})
        c = next(c for c in workload["cases"] if c["preexisting_witness"])
        self.assertEqual(choose(c, True), min(c["admissible_actions"]))


if __name__ == "__main__":
    unittest.main()
