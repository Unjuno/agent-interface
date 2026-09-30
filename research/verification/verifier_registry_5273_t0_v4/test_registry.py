import unittest

import candidate


class RegistryTests(unittest.TestCase):
    def preflight(self, ir, assignments, registry, resources):
        fn = getattr(candidate, "preflight", None)
        self.assertTrue(callable(fn), "candidate.preflight missing")
        return fn(ir, assignments, registry, resources)

    def setUp(self):
        self.ir = {
            "schema": "verification_ir.v0.1",
            "unknown_check_required": False,
            "checks": [{
                "check_id": "c1", "primitive": "TARGET.IDENTITY_CURRENT",
                "subject_ref": "window:1", "criticality": "MANDATORY",
                "required_evidence_role": "CURRENT_OBSERVATION",
                "verifier_class": "deterministic", "dependencies": [],
                "deadline": None, "budget_class": "bounded", "fallback": "YIELD_NO_INPUT",
            }],
        }
        self.assignments = [{"check_id": "c1", "verifier_id": "cpu", "estimated_cost": 12}]
        self.registry = [{
            "verifier_id": "cpu", "version": "1", "status": "available",
            "primitives": ["TARGET.IDENTITY_CURRENT"],
            "input_roles": ["CURRENT_OBSERVATION"],
            "output_roles": ["CURRENT_OBSERVATION"], "cost": 12,
        }]
        self.resources = {"available": True, "network": False, "deadline_budget": 100}

    def test_compatible_output_is_bound_to_full_assignment_inputs(self):
        result = self.preflight(self.ir, self.assignments, self.registry, self.resources)
        self.assertEqual(result["aggregate_status"], "COMPATIBLE")
        self.assertEqual(result["decisions"][0]["status"], "COMPATIBLE")
        for key, expected in (("check_id", "c1"), ("verifier_id", "cpu"),
                              ("primitive", "TARGET.IDENTITY_CURRENT"),
                              ("input_role", "CURRENT_OBSERVATION"),
                              ("output_role", "CURRENT_OBSERVATION"),
                              ("requested_version", "1")):
            self.assertEqual(result["decisions"][0][key], expected)
        self.assertEqual(result["decisions"][0]["estimated_cost"], 12)
        self.assertEqual(result["dispatch_count"], 0)
        self.assertEqual(result["authority"], "NONE")

    def test_hard_incompatibility_precedes_unavailable_network(self):
        registry = [{**self.registry[0], "status": "stale"}]
        resources = {**self.resources, "network": False}
        result = self.preflight(self.ir, self.assignments, registry, resources)
        self.assertEqual(result["decisions"][0]["status"], "REJECTED")

    def test_assignment_must_bijectively_cover_every_ir_check(self):
        with self.assertRaises(ValueError):
            self.preflight(self.ir, [], self.registry, self.resources)

    def test_unsupported_primitive_is_rejected_even_when_resources_unavailable(self):
        ir = {**self.ir, "checks": [{**self.ir["checks"][0], "primitive": "EFFECT.POSTCONDITION",
                                     "required_evidence_role": "VERIFIED_EFFECT"}]}
        result = self.preflight(ir, self.assignments, self.registry,
                                {**self.resources, "available": False})
        self.assertEqual(result["decisions"][0]["status"], "REJECTED")


if __name__ == "__main__":
    unittest.main()
