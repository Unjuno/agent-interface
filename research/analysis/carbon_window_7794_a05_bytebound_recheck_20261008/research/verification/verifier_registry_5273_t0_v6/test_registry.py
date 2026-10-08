import unittest

import candidate


class CompleteRegistryContractTests(unittest.TestCase):
    def run_one(self, *, primitive="TARGET.IDENTITY_CURRENT", role="CURRENT_OBSERVATION",
                deadline=5, descriptor_changes=None, assignment_changes=None, resource_changes=None):
        ir = {"schema": "verification_ir.v0.1", "unknown_check_required": False,
              "checks": [{"check_id": "c1", "primitive": primitive,
                          "subject_ref": "window:1", "criticality": "MANDATORY",
                          "required_evidence_role": role, "verifier_class": "deterministic",
                          "dependencies": [], "deadline": deadline, "budget_class": "bounded",
                          "fallback": "YIELD_NO_INPUT"}]}
        descriptor = {"verifier_id": "rule", "version": "1.0",
                      "supported_primitives": ["TARGET.IDENTITY_CURRENT"],
                      "accepted_evidence_roles": ["CURRENT_OBSERVATION"],
                      "output_evidence_roles": ["CURRENT_OBSERVATION"],
                      "side_effect_class": "none", "authority": "none",
                      "cold_cost": 4, "warm_cost": 1, "cost_unit": "fixture_unit",
                      "latency_envelope": {"bound": 2, "unit": "fixture_tick"},
                      "resource_class": "cpu", "deadline_behavior": "reject_infeasible",
                      "failure_modes": ["input_unknown"], "fallback": "YIELD_NO_INPUT"}
        descriptor.update(descriptor_changes or {})
        assignment = {"check_id": "c1", "verifier_id": "rule", "requested_version": "1.0",
                      "mode": "warm", "output_role": "CURRENT_OBSERVATION",
                      "side_effect_permitted": False}
        assignment.update(assignment_changes or {})
        resources = {"available_classes": ["cpu"], "cold_cost_budget": 10,
                     "warm_cost_budget": 10, "forbidden_side_effect_classes": ["external_write"]}
        resources.update(resource_changes or {})
        return candidate.preflight(ir, [assignment], [descriptor], resources)

    def test_warm_feasible_route_retains_cost_authority_and_dispatch_boundary(self):
        ir = {"schema": "verification_ir.v0.1", "unknown_check_required": False,
              "checks": [{"check_id": "c1", "primitive": "TARGET.IDENTITY_CURRENT",
                          "subject_ref": "window:1", "criticality": "MANDATORY",
                          "required_evidence_role": "CURRENT_OBSERVATION", "verifier_class": "deterministic",
                          "dependencies": [], "deadline": 5, "budget_class": "bounded",
                          "fallback": "YIELD_NO_INPUT"}]}
        assignment = [{"check_id": "c1", "verifier_id": "rule", "requested_version": "1.0",
                       "mode": "warm", "output_role": "CURRENT_OBSERVATION",
                       "side_effect_permitted": False}]
        descriptor = [{"verifier_id": "rule", "version": "1.0",
                       "supported_primitives": ["TARGET.IDENTITY_CURRENT"],
                       "accepted_evidence_roles": ["CURRENT_OBSERVATION"],
                       "output_evidence_roles": ["CURRENT_OBSERVATION"],
                       "side_effect_class": "none", "authority": "none",
                       "cold_cost": 4, "warm_cost": 1, "cost_unit": "fixture_unit",
                       "latency_envelope": {"bound": 2, "unit": "fixture_tick"},
                       "resource_class": "cpu", "deadline_behavior": "reject_infeasible",
                       "failure_modes": ["input_unknown"], "fallback": "YIELD_NO_INPUT"}]
        resources = {"available_classes": ["cpu"], "cold_cost_budget": 10,
                     "warm_cost_budget": 10, "forbidden_side_effect_classes": ["external_write"]}

        self.assertTrue(callable(getattr(candidate, "preflight", None)), "complete preflight is required")
        result = candidate.preflight(ir, assignment, descriptor, resources)
        row = result["decisions"][0]
        self.assertEqual((result["aggregate_status"], row["status"], row["reason"]),
                         ("COMPATIBLE", "COMPATIBLE", "compatible"))
        self.assertEqual((row["cold_cost_estimate"], row["warm_cost_estimate"], row["selected_cost_estimate"]),
                         (4, 1, 1))
        self.assertEqual(row["cost_provenance"], "DECLARED_ESTIMATE_NOT_MEASUREMENT")
        self.assertEqual((row["authority"], result["authority"], result["dispatch_count"]),
                         ("NONE", "NONE", 0))

    def test_unsupported_primitive_is_rejected_before_any_dispatch(self):
        result = self.run_one(primitive="EFFECT.POSTCONDITION")
        self.assertEqual((result["decisions"][0]["status"], result["decisions"][0]["reason"]),
                         ("REJECTED", "unsupported_primitive"))
        self.assertEqual(result["dispatch_count"], 0)

    def test_wrong_evidence_role_is_rejected(self):
        result = self.run_one(role="CURRENT_INTENT")
        self.assertEqual((result["decisions"][0]["status"], result["decisions"][0]["reason"]),
                         ("REJECTED", "wrong_input_role"))

    def test_wrong_output_role_is_rejected(self):
        result = self.run_one(assignment_changes={"output_role": "VERIFIED_EFFECT"})
        self.assertEqual((result["decisions"][0]["status"], result["decisions"][0]["reason"]),
                         ("REJECTED", "wrong_output_role"))

    def test_stale_requested_verifier_version_is_rejected(self):
        result = self.run_one(assignment_changes={"requested_version": "0.9"})
        self.assertEqual((result["decisions"][0]["status"], result["decisions"][0]["reason"]),
                         ("REJECTED", "stale_verifier_version"))

    def test_deadline_infeasibility_precedes_resource_unavailability(self):
        result = self.run_one(deadline=1, descriptor_changes={"warm_cost": 12,
                            "latency_envelope": {"bound": 10, "unit": "fixture_tick"}},
                              resource_changes={"available_classes": []})
        self.assertEqual((result["decisions"][0]["status"], result["decisions"][0]["reason"]),
                         ("REJECTED", "deadline_infeasible"))

    def test_unqualified_null_deadline_remains_compatible(self):
        ir = self.base_ir()
        ir["checks"][0]["deadline"] = None
        result = candidate.preflight(ir, [self.assignment("c1")], [self.descriptor()],
                                     self.resources())
        self.assertEqual(result["decisions"][0]["status"], "COMPATIBLE")
        self.assertIsNone(result["decisions"][0]["deadline"])

    def test_unavailable_resource_is_explicit_and_never_dispatched(self):
        result = self.run_one(resource_changes={"available_classes": []})
        self.assertEqual((result["decisions"][0]["status"], result["decisions"][0]["reason"]),
                         ("UNAVAILABLE", "resources_unavailable"))
        self.assertEqual(result["dispatch_count"], 0)

    def test_cold_only_budget_violation_is_rejected(self):
        result = self.run_one(assignment_changes={"mode": "cold"},
                              resource_changes={"cold_cost_budget": 3})
        self.assertEqual((result["decisions"][0]["status"], result["decisions"][0]["reason"]),
                         ("REJECTED", "cold_budget_exceeded"))

    def test_prohibited_side_effect_is_rejected(self):
        result = self.run_one(descriptor_changes={"side_effect_class": "external_write"})
        self.assertEqual((result["decisions"][0]["status"], result["decisions"][0]["reason"]),
                         ("REJECTED", "side_effect_prohibited"))

    def test_unknown_verifier_is_explicit_not_a_crash(self):
        result = candidate.preflight(self.base_ir(), [self.assignment("c1")],
                                     [], self.resources())
        self.assertEqual((result["aggregate_status"], result["decisions"][0]["reason"]),
                         ("REJECTED", "unknown_verifier"))

    def test_ambiguous_duplicate_verifier_identity_is_not_first_match_wins(self):
        result = candidate.preflight(self.base_ir(), [self.assignment("c1")],
                                     [self.descriptor(), self.descriptor()], self.resources())
        self.assertEqual((result["aggregate_status"], result["decisions"][0]["reason"]),
                         ("REJECTED", "unknown_verifier"))

    def test_duplicate_assignments_are_rejected_without_choosing_one(self):
        result = candidate.preflight(self.base_ir(),
                                     [self.assignment("c1"), self.assignment("c1")],
                                     [self.descriptor()], self.resources())
        self.assertEqual((result["aggregate_status"], result["decisions"][0]["reason"]),
                         ("REJECTED", "assignment_coverage_mismatch"))

    def test_descriptor_categories_and_declared_metadata_survive_preflight(self):
        categories = ["deterministic", "local_cpu", "local_multimodal",
                      "rich_model", "external_tool"]
        for category in categories:
            descriptor = self.descriptor()
            descriptor["category"] = category
            result = candidate.preflight(self.base_ir(), [self.assignment("c1")],
                                         [descriptor], self.resources())
            row = result["decisions"][0]
            self.assertEqual(row["category"], category)
            self.assertEqual(row["failure_modes"], ["input_unknown"])
            self.assertEqual(row["fallback"], "YIELD_NO_INPUT")
            self.assertEqual((row["authority"], result["dispatch_count"]), ("NONE", 0))

    def test_extra_unbound_assignment_is_rejected(self):
        extra = {**self.assignment("orphan"), "verifier_id": "other"}
        result = candidate.preflight(self.base_ir(), [self.assignment("c1"), extra],
                                     [self.descriptor()], self.resources())
        self.assertEqual((result["aggregate_status"], result["decisions"][0]["reason"]),
                         ("REJECTED", "assignment_coverage_mismatch"))

    def test_assignments_are_a_bijection_over_all_ir_checks(self):
        ir = self.base_ir()
        ir["checks"].append({**ir["checks"][0], "check_id": "c2",
                             "primitive": "TARGET.IDENTITY_CURRENT"})
        result = candidate.preflight(ir, [self.assignment("c1")], [self.descriptor()],
                                     self.resources())
        self.assertEqual((result["aggregate_status"], len(result["decisions"])),
                         ("REJECTED", 2))
        self.assertEqual({row["reason"] for row in result["decisions"]},
                         {"assignment_coverage_mismatch"})

    def base_ir(self):
        return {"schema": "verification_ir.v0.1", "unknown_check_required": False,
                "checks": [{"check_id": "c1", "primitive": "TARGET.IDENTITY_CURRENT",
                            "subject_ref": "window:1", "criticality": "MANDATORY",
                            "required_evidence_role": "CURRENT_OBSERVATION", "verifier_class": "deterministic",
                            "dependencies": [], "deadline": 5, "budget_class": "bounded",
                            "fallback": "YIELD_NO_INPUT"}]}

    def descriptor(self):
        return {"verifier_id": "rule", "version": "1.0",
                "category": "deterministic",
                "supported_primitives": ["TARGET.IDENTITY_CURRENT"],
                "accepted_evidence_roles": ["CURRENT_OBSERVATION"],
                "output_evidence_roles": ["CURRENT_OBSERVATION"],
                "side_effect_class": "none", "authority": "none",
                "cold_cost": 4, "warm_cost": 1, "cost_unit": "fixture_unit",
                "latency_envelope": {"bound": 2, "unit": "fixture_tick"},
                "resource_class": "cpu", "deadline_behavior": "reject_infeasible",
                "failure_modes": ["input_unknown"], "fallback": "YIELD_NO_INPUT"}

    def assignment(self, check_id):
        return {"check_id": check_id, "verifier_id": "rule", "requested_version": "1.0",
                "mode": "warm", "output_role": "CURRENT_OBSERVATION",
                "side_effect_permitted": False}

    def resources(self):
        return {"available_classes": ["cpu"], "cold_cost_budget": 10,
                "warm_cost_budget": 10, "forbidden_side_effect_classes": ["external_write"]}


if __name__ == "__main__":
    unittest.main()
