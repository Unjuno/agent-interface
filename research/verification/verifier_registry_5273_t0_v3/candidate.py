"""Full-plan, no-dispatch compatibility preflight against #5268 IR v0.1."""
from __future__ import annotations

import importlib.util
from pathlib import Path

IR_PATH = Path(__file__).resolve().parents[1] / "verification_ir_5268_v1" / "candidate.py"
SPEC = importlib.util.spec_from_file_location("verification_ir_5268_v1", IR_PATH)
IR_V1 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(IR_V1)
validate_ir = IR_V1.validate_ir
KNOWN_ROLES = {"CURRENT_OBSERVATION", "CURRENT_INTENT", "CURRENT_PERMISSION", "CURRENT_CLOCK", "CURRENT_ACTION_CONTRACT", "VERIFIED_EFFECT", "UNKNOWN_REQUIREMENT", "COVERAGE_REPORT"}
DESCRIPTOR_FIELDS = {"verifier_id", "version", "supported_primitives", "accepted_evidence_roles", "output_evidence_roles", "side_effect_class", "authority", "cold_cost_ms", "warm_cost_ms", "latency_provenance", "resource_class", "deadline_behavior", "failure_modes", "fallback"}
ASSIGNMENT_FIELDS = {"check_id", "version", "mode", "budget_ms", "output_evidence_role", "side_effects_allowed"}


def validate_registry(registry: dict) -> dict:
    fields = {"schema", "registry_version", "authority", "cost_unit", "cost_provenance", "descriptors"}
    if not isinstance(registry, dict) or set(registry) != fields:
        raise ValueError("registry fields invalid")
    if (registry["schema"] != "verifier_registry.v0.1" or
        not isinstance(registry["registry_version"], str) or not registry["registry_version"] or
        registry["authority"] != "none" or registry["cost_unit"] != "milliseconds" or
        not isinstance(registry["cost_provenance"], str) or not isinstance(registry["descriptors"], list)):
        raise ValueError("registry identity, authority, or cost metadata invalid")
    seen = set()
    for row in registry["descriptors"]:
        if not isinstance(row, dict) or set(row) != DESCRIPTOR_FIELDS or row["authority"] != "none":
            raise ValueError("descriptor fields or authority invalid")
        if not isinstance(row["verifier_id"], str) or not row["verifier_id"] or row["verifier_id"] in seen:
            raise ValueError("duplicate or invalid verifier id")
        seen.add(row["verifier_id"])
        if not isinstance(row["version"], str) or not row["version"]:
            raise ValueError("descriptor version invalid")
        for name in ("supported_primitives", "accepted_evidence_roles", "output_evidence_roles", "failure_modes"):
            if not isinstance(row[name], list) or not all(isinstance(value, str) for value in row[name]):
                raise ValueError("descriptor capability lists invalid")
        for name in ("cold_cost_ms", "warm_cost_ms"):
            if type(row[name]) is not int or row[name] < 0:
                raise ValueError("descriptor costs invalid")
        for name in ("side_effect_class", "latency_provenance", "resource_class", "deadline_behavior", "fallback"):
            if not isinstance(row[name], str) or not row[name]:
                raise ValueError("descriptor contract string invalid")
    return registry


def preflight(plan_id: str, ir: dict, assignments: list[dict], registry: dict,
              resources: dict[str, bool]) -> dict:
    validate_ir(ir)
    validate_registry(registry)
    if not isinstance(plan_id, str) or not plan_id:
        raise ValueError("plan id invalid")
    if not isinstance(resources, dict) or not all(isinstance(value, bool) for value in resources.values()):
        raise ValueError("resource snapshot invalid")
    if not isinstance(assignments, list) or len(assignments) != len(ir["checks"]):
        raise ValueError("assignments must cover every IR check exactly once")
    check_ids = [row["check_id"] for row in ir["checks"]]
    assignment_ids = []
    for row in assignments:
        if not isinstance(row, dict) or set(row) != ASSIGNMENT_FIELDS:
            raise ValueError("assignment fields invalid")
        if (not isinstance(row["check_id"], str) or not isinstance(row["version"], str) or not row["version"] or
            not isinstance(row["mode"], str) or row["mode"] not in {"cold", "warm"} or
            type(row["budget_ms"]) is not int or row["budget_ms"] < 0 or
            not isinstance(row["output_evidence_role"], str) or row["output_evidence_role"] not in KNOWN_ROLES or
            type(row["side_effects_allowed"]) is not bool):
            raise ValueError("assignment types or output role invalid")
        assignment_ids.append(row["check_id"])
    if len(assignment_ids) != len(set(assignment_ids)) or set(assignment_ids) != set(check_ids):
        raise ValueError("assignment/check IDs are not a bijection")
    by_assignment = {row["check_id"]: row for row in assignments}
    by_descriptor = {row["verifier_id"]: row for row in registry["descriptors"]}
    decisions = []
    for check in ir["checks"]:
        assignment = by_assignment[check["check_id"]]
        descriptor = by_descriptor.get(check["verifier_class"])
        hard, unavailable = [], []
        if descriptor is None:
            unavailable.append("verifier_unknown")
            cost = None
        else:
            if assignment["version"] != descriptor["version"]:
                hard.append("stale_version")
            if check["primitive"] not in descriptor["supported_primitives"]:
                hard.append("unsupported_primitive")
            if check["required_evidence_role"] not in descriptor["accepted_evidence_roles"]:
                hard.append("wrong_evidence_role")
            if assignment["output_evidence_role"] not in descriptor["output_evidence_roles"]:
                hard.append("wrong_output_role")
            if descriptor["side_effect_class"] != "none" and not assignment["side_effects_allowed"]:
                hard.append("side_effect_prohibited")
            if not resources.get(descriptor["resource_class"], False):
                unavailable.append("resource_unavailable")
            if descriptor["latency_provenance"] != "synthetic_estimate":
                unavailable.append("latency_unqualified")
            cost = descriptor[f"{assignment['mode']}_cost_ms"]
            if cost > assignment["budget_ms"]:
                hard.append("budget_exceeded")
            if check["deadline"] is not None and cost > check["deadline"]:
                hard.append("deadline_infeasible")
        status = "REJECTED" if hard else "UNAVAILABLE" if unavailable else "COMPATIBLE"
        decisions.append({"check_id": check["check_id"], "status": status,
                          "reasons": hard + unavailable, "dispatch_count": 0,
                          "authority": "none", "cost_basis": "declared_estimate_not_measurement",
                          "estimated_cost_ms": cost})
    statuses = {row["status"] for row in decisions}
    overall = "REJECTED" if "REJECTED" in statuses else "UNAVAILABLE" if "UNAVAILABLE" in statuses else "COMPATIBLE"
    reasons = [{"check_id": row["check_id"], "reason": reason}
               for row in decisions for reason in row["reasons"]]
    return {"plan_id": plan_id, "schema": "verifier_plan_preflight.v0.3",
            "status": overall, "reasons": reasons, "decisions": decisions,
            "dispatch_count": 0, "authority": "none"}
