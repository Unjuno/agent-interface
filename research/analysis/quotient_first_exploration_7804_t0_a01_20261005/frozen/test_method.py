"""Construction checks only; these do not use formal output paths."""
import copy
import importlib.util
import json
import pathlib
import sys
import unittest

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
import candidate
import auditor


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class MethodConstruction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = json.loads((HERE / "spec.json").read_text())
        cls.actual = candidate.run(cls.spec)
        cls.expected = auditor.reconstruct(cls.spec)

    def test_independent_raw_reconstruction(self):
        self.assertEqual(self.actual, self.expected)

    def test_quotient_first_reduces_both_search_counts(self):
        arms = self.actual["arms"]
        full = arms["FULL_NAMED_BFS"]
        quotient = arms["QUOTIENT_FIRST_BFS"]
        self.assertLess(quotient["expanded_nodes"], full["expanded_nodes"])
        self.assertLess(quotient["generated_transitions"], full["generated_transitions"])
        self.assertTrue(quotient["predicate_labels_preserved"])
        self.assertTrue(quotient["quotient_matches_full_partition"])

    def test_all_unsafe_quotient_classes_have_lifted_witnesses(self):
        quotient = self.actual["arms"]["QUOTIENT_FIRST_BFS"]
        self.assertEqual(quotient["unsafe_classes"], len(quotient["counterexample_witnesses"]))
        self.assertTrue(all(w["lifted_trace"] for w in quotient["counterexample_witnesses"]))

    def test_identity_breakers_fall_back(self):
        for row in self.actual["identity_breaking_controls"].values():
            self.assertTrue(row["fallback_to_named_states"])
            self.assertEqual(row["expanded_nodes"], row["reachable_states"])

    def test_naive_control_is_detected_as_unsound(self):
        self.assertTrue(self.actual["arms"]["NAIVE_ALL_ID_QUOTIENT"]["unsound"])

    def test_prior_full_graph_matches_preserved_result_counts(self):
        predecessor = load_module("old_candidate_for_construction", HERE / "predecessor_model.py")
        cfg = predecessor.world()
        named, _ = predecessor._enumerate(cfg)
        self.assertEqual(312, len(named))
        groups = {predecessor.typed_key(s, cfg) for s in named.values()}
        self.assertEqual(166, len(groups))

    def test_auditor_rejects_removed_edge_and_forged_lift(self):
        changed = copy.deepcopy(self.actual)
        changed["arms"]["QUOTIENT_FIRST_BFS"]["quotient_edges"].pop()
        self.assertTrue(auditor.compare(changed, self.expected))
        changed = copy.deepcopy(self.actual)
        changed["arms"]["QUOTIENT_FIRST_BFS"]["counterexample_witnesses"][0]["lifted_trace"][0]["action"][1] = "requester"
        self.assertTrue(auditor.compare(changed, self.expected))
        changed = copy.deepcopy(self.actual)
        changed["arms"]["QUOTIENT_FIRST_BFS"]["generated_transitions"] += 1
        self.assertTrue(auditor.compare(changed, self.expected))


if __name__ == "__main__":
    unittest.main()
