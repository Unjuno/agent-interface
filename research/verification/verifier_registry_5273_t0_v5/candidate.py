"""Frozen decision-precedence candidate for verifier registry T0 v5."""

from verification_ir_5268_v1.candidate import validate_ir


def preflight(ir, assignments, registry, resources):
    validate_ir(ir)
    if not isinstance(assignments, list) or not isinstance(registry, list) or not isinstance(resources, dict):
        raise ValueError("invalid preflight input types")
    checks = ir["checks"]
    check_ids = [check["check_id"] for check in checks]
    assignment_ids = [row.get("check_id") for row in assignments if isinstance(row, dict)]
    if (len(assignments) != len(checks) or len(set(check_ids)) != len(check_ids)
            or len(set(assignment_ids)) != len(assignment_ids) or set(check_ids) != set(assignment_ids)):
        raise ValueError("assignment/check bijection required")
    verifiers = {row.get("verifier_id"): row for row in registry if isinstance(row, dict)}
    if len(verifiers) != len(registry):
        raise ValueError("duplicate or malformed verifier descriptor")
    assigned = {row["check_id"]: row for row in assignments}
    decisions = []
    for check in checks:
        assignment = assigned[check["check_id"]]
        verifier = verifiers.get(assignment.get("verifier_id"))
        input_role = check["required_evidence_role"]
        output_role = assignment.get("output_role", input_role)
        status, reasons = "COMPATIBLE", []
        if verifier is None:
            status, reasons = "UNAVAILABLE", ["unknown_verifier"]
        elif (check["primitive"] not in verifier.get("primitives", [])
              or input_role not in verifier.get("input_roles", [])
              or output_role not in verifier.get("output_roles", [])):
            status, reasons = "REJECTED", ["hard_incompatibility"]
        elif verifier.get("status") != "available":
            status, reasons = "REJECTED", ["verifier_not_current"]
        elif assignment.get("requested_version", verifier.get("version")) != verifier.get("version"):
            status, reasons = "REJECTED", ["version_mismatch"]
        elif (check.get("deadline") is not None
              and assignment.get("estimated_cost", 0) > resources.get("deadline_budget", 0)):
            status, reasons = "REJECTED", ["deadline_infeasible"]
        elif not resources.get("available", False):
            status, reasons = "UNAVAILABLE", ["resources_unavailable"]
        elif verifier.get("network_required", False) and not resources.get("network", False):
            status, reasons = "UNAVAILABLE", ["network_unavailable"]
        decisions.append({
            "check_id": check["check_id"], "verifier_id": assignment.get("verifier_id"),
            "primitive": check["primitive"], "input_role": input_role, "output_role": output_role,
            "requested_version": assignment.get("requested_version", verifier.get("version") if verifier else None),
            "estimated_cost": assignment.get("estimated_cost"), "status": status, "reasons": reasons,
        })
    statuses = [row["status"] for row in decisions]
    aggregate = "REJECTED" if "REJECTED" in statuses else "UNAVAILABLE" if "UNAVAILABLE" in statuses else "COMPATIBLE"
    return {"aggregate_status": aggregate, "decisions": decisions, "dispatch_count": 0, "authority": "NONE"}
