"""Construction candidate for verifier assignment preflight (T0 v4)."""

import re

from verification_ir_5268_v1.candidate import validate_ir


def _valid_role(role):
    return isinstance(role, str) and bool(re.fullmatch(r"[A-Z][A-Z0-9_]*", role))


def preflight(ir, assignments, registry, resources):
    """Compute non-dispatching decisions from the complete frozen inputs."""
    validate_ir(ir)
    if not isinstance(assignments, list) or not isinstance(registry, list):
        raise ValueError("assignments and registry must be lists")
    if not isinstance(resources, dict):
        raise ValueError("resources must be an object")
    checks = ir["checks"]
    check_ids = [c["check_id"] for c in checks]
    assignment_ids = [a.get("check_id") for a in assignments if isinstance(a, dict)]
    if len(assignments) != len(checks) or len(set(assignment_ids)) != len(assignment_ids) or set(assignment_ids) != set(check_ids):
        raise ValueError("assignments must bijectively cover IR checks")
    by_id = {a["check_id"]: a for a in assignments}
    registry_ids = [v.get("verifier_id") for v in registry if isinstance(v, dict)]
    if len(registry_ids) != len(registry) or len(set(registry_ids)) != len(registry_ids):
        raise ValueError("registry verifier IDs must be unique")
    registry_by_id = {v["verifier_id"]: v for v in registry}
    decisions = []
    for check in checks:
        assignment = by_id[check["check_id"]]
        verifier_id = assignment.get("verifier_id")
        verifier = registry_by_id.get(verifier_id)
        primitive = check["primitive"]
        input_role = check["required_evidence_role"]
        output_role = assignment.get("output_role", input_role)
        requested_version = assignment.get("requested_version")
        status = "COMPATIBLE"
        reasons = []
        if not _valid_role(output_role):
            status, reasons = "REJECTED", ["invalid_output_role"]
        elif verifier is None:
            status, reasons = "UNAVAILABLE", ["unknown_verifier"]
        else:
            required = (primitive in verifier.get("primitives", [])
                        and input_role in verifier.get("input_roles", [])
                        and output_role in verifier.get("output_roles", []))
            if not required or verifier.get("status") not in ("available", "stale"):
                status, reasons = "REJECTED", ["hard_incompatibility"]
            elif requested_version is not None and requested_version != verifier.get("version"):
                status, reasons = "REJECTED", ["version_mismatch"]
            elif verifier.get("status") != "available":
                status, reasons = "REJECTED", ["verifier_not_current"]
            elif not resources.get("available", False):
                status, reasons = "UNAVAILABLE", ["resources_unavailable"]
            elif verifier.get("network_required", False) and not resources.get("network", False):
                status, reasons = "UNAVAILABLE", ["network_unavailable"]
            elif (check.get("deadline") is not None
                  and assignment.get("estimated_cost", 0) > resources.get("deadline_budget", 0)):
                status, reasons = "REJECTED", ["deadline_infeasible"]
        decisions.append({
            "check_id": check["check_id"], "verifier_id": verifier_id,
            "primitive": primitive, "input_role": input_role, "output_role": output_role,
            "requested_version": requested_version if requested_version is not None else (verifier or {}).get("version"),
            "estimated_cost": assignment.get("estimated_cost"), "status": status,
            "reasons": reasons,
        })
    statuses = [d["status"] for d in decisions]
    aggregate = "REJECTED" if "REJECTED" in statuses else "UNAVAILABLE" if "UNAVAILABLE" in statuses else "COMPATIBLE"
    return {"aggregate_status": aggregate, "decisions": decisions,
            "dispatch_count": 0, "authority": "NONE"}
