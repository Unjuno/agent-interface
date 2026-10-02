import importlib.util
import json
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parent
MODULE = ROOT / "candidate.py"


class ArtifactViabilityContractTests(unittest.TestCase):
    def load_candidate(self):
        if not MODULE.exists():
            self.fail("candidate scorer is missing")
        spec = importlib.util.spec_from_file_location("candidate", MODULE)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_equal_partial_score_does_not_hide_required_citation_failure(self):
        module = self.load_candidate()
        task = {
            "checks": {
                "source_fidelity": {"required": True, "weight": 2},
                "citation_binding": {"required": True, "weight": 3},
                "structure": {"required": True, "weight": 1},
                "render_readable": {"required": True, "weight": 2},
                "export_exists": {"required": True, "weight": 2},
                "cosmetic_layout": {"required": False, "weight": 3},
            },
            "must_pass": ["source_fidelity", "citation_binding", "structure", "render_readable", "export_exists"],
            "alternatives": [],
        }
        usable = {"source_fidelity": "PASS", "citation_binding": "PASS", "structure": "PASS", "render_readable": "PASS", "export_exists": "PASS", "cosmetic_layout": "FAIL"}
        unusable = {"source_fidelity": "PASS", "citation_binding": "FAIL", "structure": "PASS", "render_readable": "PASS", "export_exists": "PASS", "cosmetic_layout": "PASS"}
        left = module.score_route(task, usable)
        right = module.score_route(task, unusable)
        self.assertEqual(left["partial_score"], right["partial_score"])
        self.assertEqual(left["strict_status"], "PASS")
        self.assertEqual(right["strict_status"], "FAIL")
        self.assertEqual(left["dependency_status"], "PASS")
        self.assertEqual(right["dependency_status"], "FAIL")

    def test_unknown_required_render_evidence_is_not_promoted_to_pass(self):
        module = self.load_candidate()
        contract = {"checks": {"render": {"required": True, "weight": 2}}, "must_pass": ["render"], "alternatives": []}
        self.assertEqual(module.score_route(contract, {"render": "UNKNOWN"})["viability"], "UNKNOWN")

    def test_accessible_text_is_an_alternative_to_rendered_readability(self):
        module = self.load_candidate()
        contract = {
            "checks": {"render": {"required": True, "weight": 2}, "text": {"required": True, "weight": 1}},
            "must_pass": [],
            "alternatives": [["render", "text"]],
        }
        self.assertEqual(module.score_route(contract, {"render": "FAIL", "text": "PASS"})["viability"], "PASS")
        self.assertEqual(module.score_route(contract, {"render": "FAIL", "text": "FAIL"})["viability"], "FAIL")

    def test_observation_vector_must_match_the_frozen_contract(self):
        module = self.load_candidate()
        contract = {"checks": {"required": {"required": True, "weight": 1}}, "must_pass": ["required"], "alternatives": []}
        with self.assertRaises(ValueError):
            module.score_route(contract, {"required": "PASS", "injected": "PASS"})

    def test_minimal_cut_sets_include_a_two_condition_alternative_failure(self):
        module = self.load_candidate()
        contract = {
            "checks": {key: {"required": True, "weight": 1} for key in ("source", "citation", "appendix")},
            "must_pass": ["source"],
            "alternatives": [["citation", "appendix"]],
        }
        self.assertEqual(module.minimal_cut_sets(contract), [["source"], ["appendix", "citation"]])

    def test_run_preserves_attempt_denominator_and_route_effects(self):
        module = self.load_candidate()
        fixture = {
            "contracts": {"doc": {"checks": {"critical": {"required": True, "weight": 1}}, "must_pass": ["critical"], "alternatives": []}},
            "cases": [{"case_id": "one", "contract": "doc", "routes": {"A": {"observations": {"critical": "PASS"}}, "B": {"observations": {"critical": "FAIL"}}}}],
        }
        result = module.run(fixture)
        self.assertEqual(result["attempted_cases"], 1)
        self.assertEqual(result["results"][0]["routes"]["A"]["viability"], "PASS")
        self.assertEqual(result["results"][0]["routes"]["B"]["viability"], "FAIL")


if __name__ == "__main__":
    unittest.main()
