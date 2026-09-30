"""Preflight a #5268 IR against versioned verifier descriptors; never dispatch."""
from __future__ import annotations

import importlib.util
from pathlib import Path

IR_DIR = Path(__file__).resolve().parents[1] / "verification_ir_5268_v1"
IR_SPEC = importlib.util.spec_from_file_location("verification_ir_5268_candidate", IR_DIR / "candidate.py")
IR_MODULE = importlib.util.module_from_spec(IR_SPEC)
IR_SPEC.loader.exec_module(IR_MODULE)
validate_ir = IR_MODULE.validate_ir

DESCRIPTOR_FIELDS = {"verifier_id", "version", "supported_primitives", "accepted_evidence_roles", "output_evidence_roles", "side_effect_class", "authority", "cold_cost_ms", "warm_cost_ms", "latency_provenance", "resource_class", "deadline_behavior", "failure_modes", "fallback"}
ASSIGNMENT_FIELDS = {"check_id", "version", "mode", "budget_ms", "output_evidence_role", "side_effects_allowed"}


def validate_registry(registry: dict) -> dict:
    if not isinstance(registry, dict) or set(registry) != {"schema", "registry_version", "authority", "cost_unit", "cost_provenance", "descriptors"}:
        raise ValueError("registry fields invalid")
    if (registry["schema"] != "verifier_registry.v0.1" or
        not isinstance(registry["registry_version"], str) or not registry["registry_version"] or
        registry["authority"] != "none" or not isinstance(registry["cost_provenance"], str)):
        raise ValueError("registry identity or authority invalid")
    if registry["cost_unit"] != "milliseconds" or not isinstance(registry["descriptors"], list):
        raise ValueError("registry cost unit or descriptors invalid")
    seen = set()
    for row in registry["descriptors"]:
        if not isinstance(row, dict) or set(row) != DESCRIPTOR_FIELDS or row["authority"] != "none":
            raise ValueError("descriptor fields or authority invalid")
        if not isinstance(row["verifier_id"], str) or not row["verifier_id"] or row["verifier_id"] in seen:
            raise ValueError("duplicate or invalid verifier id")
        if not isinstance(row["version"], str) or not row["version"]:
            raise ValueError("descriptor version invalid")
        seen.add(row["verifier_id"])
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


def preflight(ir: dict, assignment: dict, registry: dict, resources: dict[str, bool]) -> dict:
    validate_ir(ir)
    validate_registry(registry)
    if (not isinstance(resources, dict) or not all(isinstance(v, bool) for v in resources.values()) or
        not isinstance(assignment, dict) or set(assignment) != ASSIGNMENT_FIELDS):
        raise ValueError("assignment or resource snapshot invalid")
    if (not isinstance(assignment["version"], str) or not assignment["version"] or
        not isinstance(assignment["mode"], str) or assignment["mode"] not in {"cold", "warm"} or
        type(assignment["budget_ms"]) is not int or assignment["budget_ms"] < 0 or
        not isinstance(assignment["output_evidence_role"], str) or
        type(assignment["side_effects_allowed"]) is not bool):
        raise ValueError("assignment field types invalid")
    check = next((row for row in ir["checks"] if row["check_id"] == assignment["check_id"]), None)
    if check is None:
        raise ValueError("assignment check_id missing from IR")
    descriptor = next((row for row in registry["descriptors"] if row["verifier_id"] == check["verifier_class"]), None)
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
        if descriptor["side_effect_class"] != "none" and assignment["side_effects_allowed"] is not True:
            hard.append("side_effect_prohibited")
        if not resources.get(descriptor["resource_class"], False):
            unavailable.append("resource_unavailable")
        if descriptor["latency_provenance"] != "synthetic_estimate":
            unavailable.append("latency_unqualified")
        cost = descriptor[f"{assignment['mode']}_cost_ms"]
        if cost > assignment["budget_ms"]:
            hard.append("budget_exceeded")
        deadline = check["deadline"]
        if deadline is not None and cost > deadline:
            hard.append("deadline_infeasible")
    status = "REJECTED" if hard else "UNAVAILABLE" if unavailable else "COMPATIBLE"
    return {"check_id": check["check_id"], "status": status, "reasons": hard + unavailable,
            "dispatch_count": 0, "authority": "none", "cost_basis": "declared_estimate_not_measurement",
            "estimated_cost_ms": cost}
