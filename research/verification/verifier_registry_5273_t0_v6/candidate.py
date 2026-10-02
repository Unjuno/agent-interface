"""Construction candidate for the complete verifier descriptor contract (T0 v6)."""

from verification_ir_5268_v1.candidate import validate_ir


def preflight(ir, assignments, registry, resources):
    """Produce a zero-dispatch compatibility report for every IR check."""
    validate_ir(ir)
    checks = ir["checks"]
    by_check = {}
    for assignment in assignments:
        by_check.setdefault(assignment.get("check_id"), []).append(assignment)
    decisions = []
    for check in checks:
        check_id = check["check_id"]
        rows = by_check.get(check_id, [])
        if len(rows) != 1 or len(assignments) != len(checks):
            decisions.append(_rejected(check_id, "assignment_coverage_mismatch"))
            continue
        assignment = rows[0]
        matches = [row for row in registry
                   if row.get("verifier_id") == assignment.get("verifier_id")]
        if len(matches) != 1:
            decisions.append(_rejected(check_id, "unknown_verifier"))
            continue
        descriptor = matches[0]
        mode = assignment.get("mode")
        cost_key = mode + "_cost" if mode in ("cold", "warm") else None
        if cost_key is None:
            decisions.append(_rejected(check_id, "unknown_mode"))
            continue
        selected = descriptor[cost_key]
        status, reason = "COMPATIBLE", "compatible"
        # Hard semantic incompatibilities are checked before resource availability.
        if check["primitive"] not in descriptor["supported_primitives"]:
            status, reason = "REJECTED", "unsupported_primitive"
        elif check["required_evidence_role"] not in descriptor["accepted_evidence_roles"]:
            status, reason = "REJECTED", "wrong_input_role"
        elif assignment.get("output_role") not in descriptor["output_evidence_roles"]:
            status, reason = "REJECTED", "wrong_output_role"
        elif assignment.get("requested_version") != descriptor["version"]:
            status, reason = "REJECTED", "stale_verifier_version"
        elif descriptor.get("authority", "none").lower() != "none":
            status, reason = "REJECTED", "authority_not_permitted"
        elif (descriptor["side_effect_class"] in resources["forbidden_side_effect_classes"]
              or (descriptor["side_effect_class"] != "none"
                  and not assignment.get("side_effect_permitted", False))):
            status, reason = "REJECTED", "side_effect_prohibited"
        elif (check["deadline"] is not None
              and descriptor["latency_envelope"]["bound"] > check["deadline"]):
            status, reason = "REJECTED", "deadline_infeasible"
        elif descriptor["resource_class"] not in resources["available_classes"]:
            status, reason = "UNAVAILABLE", "resources_unavailable"
        elif selected > resources[mode + "_cost_budget"]:
            status, reason = "REJECTED", mode + "_budget_exceeded"
        decisions.append({
            "check_id": check_id, "verifier_id": descriptor["verifier_id"],
            "requested_version": assignment.get("requested_version"),
            "primitive": check["primitive"], "input_role": check["required_evidence_role"],
            "subject_ref": check["subject_ref"], "criticality": check["criticality"],
            "deadline": check["deadline"], "budget_class": check["budget_class"],
            "check_fallback": check["fallback"],
            "output_role": assignment.get("output_role"),
            "side_effect_class": descriptor["side_effect_class"], "authority": "NONE",
            "mode": mode, "cold_cost_estimate": descriptor["cold_cost"],
            "warm_cost_estimate": descriptor["warm_cost"], "selected_cost_estimate": selected,
            "cost_unit": descriptor["cost_unit"],
            "cost_provenance": "DECLARED_ESTIMATE_NOT_MEASUREMENT",
            "declared_cost_provenance": descriptor.get("cost_provenance", "unspecified"),
            "latency_bound": descriptor["latency_envelope"]["bound"],
            "latency_unit": descriptor["latency_envelope"]["unit"],
            "resource_class": descriptor["resource_class"],
            "category": descriptor.get("category", "unspecified"),
            "failure_modes": list(descriptor["failure_modes"]),
            "fallback": descriptor["fallback"],
            "descriptor_snapshot": dict(descriptor),
            "status": status, "reason": reason,
        })
    statuses = {row["status"] for row in decisions}
    aggregate = ("REJECTED" if "REJECTED" in statuses else
                 "UNAVAILABLE" if "UNAVAILABLE" in statuses else "COMPATIBLE")
    return {"aggregate_status": aggregate, "decisions": decisions,
            "dispatch_count": 0, "authority": "NONE"}


def _rejected(check_id, reason):
    return {"check_id": check_id, "status": "REJECTED", "reason": reason,
            "authority": "NONE", "dispatch_count": 0}
