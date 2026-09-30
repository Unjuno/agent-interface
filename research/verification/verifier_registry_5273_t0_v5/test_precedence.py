import json
import unittest
from pathlib import Path

import candidate


class DecisionPrecedenceTests(unittest.TestCase):
    def inputs(self, *, deadline=None, estimate=12, resource_available=False, primitive="TARGET.IDENTITY_CURRENT", verifier_status="available"):
        ir = {
            "schema": "verification_ir.v0.1", "unknown_check_required": False,
            "checks": [{
                "check_id": "c1", "primitive": primitive, "subject_ref": "window:1",
                "criticality": "MANDATORY", "required_evidence_role": "CURRENT_OBSERVATION",
                "verifier_class": "deterministic", "dependencies": [], "deadline": deadline,
                "budget_class": "bounded", "fallback": "YIELD_NO_INPUT",
            }],
        }
        assignments = [{"check_id": "c1", "verifier_id": "cpu", "estimated_cost": estimate}]
        registry = [{
            "verifier_id": "cpu", "version": "1", "status": verifier_status,
            "primitives": ["TARGET.IDENTITY_CURRENT"],
            "input_roles": ["CURRENT_OBSERVATION"], "output_roles": ["CURRENT_OBSERVATION"],
        }]
        resources = {"available": resource_available, "network": False, "deadline_budget": 1}
        return ir, assignments, registry, resources

    def test_infeasible_deadline_rejects_even_when_resources_are_unavailable(self):
        self.assertTrue(callable(getattr(candidate, "preflight", None)), "preflight decision function is required")
        ir, assignments, registry, resources = self.inputs(deadline=10, resource_available=False)
        result = candidate.preflight(ir, assignments, registry, resources)

        self.assertEqual(result["decisions"][0]["status"], "REJECTED")
        self.assertEqual(result["decisions"][0]["reasons"], ["deadline_infeasible"])
        self.assertEqual(result["dispatch_count"], 0)

    def test_temporarily_unavailable_resource_does_not_become_deadline_rejection(self):
        ir, assignments, registry, resources = self.inputs(deadline=None, resource_available=False)
        result = candidate.preflight(ir, assignments, registry, resources)
        self.assertEqual(result["decisions"][0]["status"], "UNAVAILABLE")
        self.assertEqual(result["decisions"][0]["reasons"], ["resources_unavailable"])

    def test_hard_primitive_incompatibility_precedes_resource_unavailability(self):
        ir, assignments, registry, resources = self.inputs(deadline=None, resource_available=False,
                                                             primitive="EFFECT.POSTCONDITION")
        result = candidate.preflight(ir, assignments, registry, resources)
        self.assertEqual(result["decisions"][0]["status"], "REJECTED")
        self.assertEqual(result["decisions"][0]["reasons"], ["hard_incompatibility"])

    def test_stale_verifier_precedes_resource_unavailability(self):
        ir, assignments, registry, resources = self.inputs(deadline=None, resource_available=False,
                                                             verifier_status="stale")
        result = candidate.preflight(ir, assignments, registry, resources)
        self.assertEqual(result["decisions"][0]["status"], "REJECTED")
        self.assertEqual(result["decisions"][0]["reasons"], ["verifier_not_current"])

    def test_frozen_corpus_matches_literal_statuses(self):
        cases = json.loads((Path(__file__).parent / "cases.json").read_text())
        expected = {
            "warm-feasible": ("COMPATIBLE", []),
            "deadline-infeasible-and-resource-down": ("REJECTED", ["deadline_infeasible"]),
            "temporarily-resource-unavailable": ("UNAVAILABLE", ["resources_unavailable"]),
            "hard-primitive-incompatible": ("REJECTED", ["hard_incompatibility"]),
            "stale-verifier": ("REJECTED", ["verifier_not_current"]),
            "wrong-output-role": ("REJECTED", ["hard_incompatibility"]),
            "requested-version-mismatch": ("REJECTED", ["version_mismatch"]),
        }
        self.assertEqual(set(expected), {case["case_id"] for case in cases})
        for case in cases:
            output = candidate.preflight(case["ir"], case["assignments"],
                                         case["registry_snapshot"], case["resources"])
            self.assertEqual((output["decisions"][0]["status"], output["decisions"][0]["reasons"]),
                             expected[case["case_id"]], case["case_id"])

    def test_duplicate_assignment_is_rejected(self):
        ir, assignments, registry, resources = self.inputs(deadline=None, resource_available=True)
        with self.assertRaises(ValueError):
            candidate.preflight(ir, assignments + assignments, registry, resources)


if __name__ == "__main__":
    unittest.main()
