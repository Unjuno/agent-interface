import copy
import unittest

from audit import audit, decide


def sample_case():
    ir = {"schema": "verification_ir.v0.1", "unknown_check_required": False,
          "checks": [{"check_id": "c1", "primitive": "TARGET.IDENTITY_CURRENT",
                      "subject_ref": "window:1", "criticality": "MANDATORY",
                      "required_evidence_role": "CURRENT_OBSERVATION", "verifier_class": "deterministic",
                      "dependencies": [], "deadline": None, "budget_class": "bounded",
                      "fallback": "YIELD_NO_INPUT"}]}
    assignments = [{"check_id": "c1", "verifier_id": "cpu", "estimated_cost": 12}]
    registry = [{"verifier_id": "cpu", "version": "1", "status": "available",
                 "primitives": ["TARGET.IDENTITY_CURRENT"], "input_roles": ["CURRENT_OBSERVATION"],
                 "output_roles": ["CURRENT_OBSERVATION"], "cost": 12}]
    resources = {"available": True, "network": False, "deadline_budget": 100}
    return {"case_id": "warm", "ir": ir, "assignments": assignments,
            "registry_snapshot": registry, "resources": resources}


class AuditTests(unittest.TestCase):
    def test_recomputes_from_raw_inputs_and_binds_case(self):
        case = sample_case()
        row = {**case, "observed": decide(case["ir"], case["assignments"], case["registry_snapshot"], case["resources"])}
        result = audit({"schema": "verifier_registry_raw.v4", "rows": [row]}, [case])
        self.assertEqual(result["rows"], 1)

    def test_rejects_assignment_mutation_even_if_old_decision_is_retained(self):
        case = sample_case()
        row = {**case, "observed": decide(case["ir"], case["assignments"], case["registry_snapshot"], case["resources"])}
        changed = copy.deepcopy(row)
        changed["assignments"][0]["verifier_id"] = "different"
        with self.assertRaises(ValueError):
            audit({"schema": "verifier_registry_raw.v4", "rows": [changed]}, [case])

    def test_rejects_extra_observed_fields(self):
        case = sample_case()
        row = {**case, "observed": {**decide(case["ir"], case["assignments"], case["registry_snapshot"], case["resources"]), "extra": 1}}
        with self.assertRaises(ValueError):
            audit({"schema": "verifier_registry_raw.v4", "rows": [row]}, [case])


if __name__ == "__main__":
    unittest.main()
