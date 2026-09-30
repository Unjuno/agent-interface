"""Authority-neutral, deterministic verifier-plan compatibility preflight."""
from __future__ import annotations


def preflight(plan: dict, registry: dict, resources: dict[str, bool]) -> dict:
    """Return compatibility metadata only; never dispatch a verifier."""
    if plan.get("schema") != "verifier_plan.v0.1" or not isinstance(plan.get("checks"), list):
        raise ValueError("invalid plan schema")
    if registry.get("schema") != "verifier_registry.v0.1":
        raise ValueError("invalid registry schema")
    if registry.get("authority") != "none":
        raise ValueError("registry authority must be none")
    descriptors = {d["verifier_id"]: d for d in registry.get("descriptors", [])}
    if len(descriptors) != len(registry.get("descriptors", [])):
        raise ValueError("duplicate verifier id")
    decisions = []
    for check in plan["checks"]:
        reasons = []
        descriptor = descriptors.get(check.get("verifier_id"))
        if descriptor is None:
            reasons.append("verifier_unavailable")
        else:
            if check.get("version") != descriptor["version"]:
                reasons.append("stale_version")
            if check.get("primitive") not in descriptor["supported_primitives"]:
                reasons.append("unsupported_primitive")
            if check.get("evidence_role") not in descriptor["accepted_evidence_roles"]:
                reasons.append("wrong_evidence_role")
            if not resources.get(descriptor["resource_class"], False):
                reasons.append("resource_unavailable")
            if descriptor["latency_provenance"] != "synthetic_estimate":
                reasons.append("latency_unqualified")
            if descriptor["side_effect_class"] != "none" and check.get("side_effects_allowed") is not True:
                reasons.append("side_effect_prohibited")
            mode = check.get("mode")
            if mode not in {"cold", "warm"}:
                reasons.append("unknown_cost_mode")
            else:
                cost = descriptor[f"{mode}_cost_ms"]
                budget = check.get("budget_ms")
                if type(budget) is not int or budget < 0 or cost > budget:
                    reasons.append("budget_exceeded")
                deadline = check.get("deadline_ms")
                if type(deadline) is not int or deadline < 0 or cost > deadline:
                    reasons.append("deadline_infeasible")
        decisions.append({
            "check_id": check.get("check_id"),
            "status": "COMPATIBLE" if not reasons else "UNAVAILABLE" if "resource_unavailable" in reasons or "latency_unqualified" in reasons else "REJECTED",
            "reasons": reasons,
            "dispatch_count": 0,
            "authority": "none",
            "cost_basis": "declared_estimate_not_measurement",
        })
    return {"schema": "verifier_preflight.v0.1", "registry_version": registry["registry_version"],
            "authority": "none", "decisions": decisions}
