"""Frozen T0 v6 precedence corpus. All costs are declared fixture estimates."""

import copy
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CASES = [
    ("warm_feasible", {}, {}, {}, "COMPATIBLE", "compatible"),
    ("unsupported_primitive", {"primitive": "EFFECT.POSTCONDITION"}, {}, {},
     "REJECTED", "unsupported_primitive"),
    ("wrong_input_role", {"role": "CURRENT_INTENT"}, {}, {}, "REJECTED", "wrong_input_role"),
    ("stale_version", {}, {"requested_version": "0.9"}, {}, "REJECTED", "stale_verifier_version"),
    ("resource_unavailable", {}, {}, {"available_classes": []},
     "UNAVAILABLE", "resources_unavailable"),
    ("cold_budget_exceeded", {}, {"mode": "cold"}, {"cold_cost_budget": 3},
     "REJECTED", "cold_budget_exceeded"),
    ("side_effect_prohibited", {}, {}, {}, "REJECTED", "side_effect_prohibited"),
    ("deadline_infeasible_precedes_unavailable", {"deadline": 1},
     {"mode": "warm"}, {"available_classes": []}, "REJECTED", "deadline_infeasible"),
]
CATEGORIES = ["deterministic", "local_cpu", "local_multimodal", "rich_model", "external_tool"]


def build_cases():
    cases = []
    for i, (name, ir_change, assignment_change, resource_change, status, reason) in enumerate(CASES):
        check = {"check_id": "c1", "primitive": "TARGET.IDENTITY_CURRENT",
                 "subject_ref": "window:1", "criticality": "MANDATORY",
                 "required_evidence_role": "CURRENT_OBSERVATION",
                 "verifier_class": "deterministic", "dependencies": [],
                 "deadline": 5, "budget_class": "bounded", "fallback": "YIELD_NO_INPUT"}
        ir = {"schema": "verification_ir.v0.1", "unknown_check_required": False,
              "checks": [check]}
        assignment = {"check_id": "c1", "verifier_id": "rule", "requested_version": "1.0",
                      "mode": "warm", "output_role": "CURRENT_OBSERVATION",
                      "side_effect_permitted": False}
        descriptor = {"verifier_id": "rule", "version": "1.0", "category": CATEGORIES[i % 5],
                      "supported_primitives": ["TARGET.IDENTITY_CURRENT"],
                      "accepted_evidence_roles": ["CURRENT_OBSERVATION"],
                      "output_evidence_roles": ["CURRENT_OBSERVATION"],
                      "side_effect_class": "external_write" if name == "side_effect_prohibited" else "none",
                      "authority": "none", "cold_cost": 4, "warm_cost": 1,
                      "cost_unit": "fixture_unit", "cost_provenance": "declared_fixture_estimate",
                      "latency_envelope": {"bound": 2, "unit": "fixture_tick"},
                      "concurrency": 1, "resource_class": "cpu",
                      "deadline_behavior": "reject_infeasible",
                      "failure_modes": ["input_unknown"], "fallback": "YIELD_NO_INPUT"}
        resources = {"available_classes": ["cpu"], "cold_cost_budget": 10,
                     "warm_cost_budget": 10, "forbidden_side_effect_classes": ["external_write"]}
        if name == "side_effect_prohibited":
            assignment["side_effect_permitted"] = True
        if name == "deadline_infeasible_precedes_unavailable":
            descriptor["latency_envelope"]["bound"] = 10
        if name == "unsupported_primitive":
            ir["checks"][0]["primitive"] = ir_change["primitive"]
        elif "role" in ir_change:
            ir["checks"][0]["required_evidence_role"] = ir_change["role"]
        elif "deadline" in ir_change:
            ir["checks"][0]["deadline"] = ir_change["deadline"]
        assignment.update(assignment_change)
        resources.update(resource_change)
        cases.append({"case_id": name, "ir": ir, "assignments": [assignment],
                      "registry": [descriptor], "resources": resources,
                      "expected_status": status, "expected_reason": reason})
    return cases


def write_frozen():
    path = ROOT / "cases.json"
    payload = {"schema": "verifier_registry_5273_t0_v6.corpus.v1",
               "source_issue": 5273,
               "cost_note": "Declared synthetic estimates only; not host measurements.",
               "cases": build_cases()}
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


if __name__ == "__main__":
    write_frozen()
