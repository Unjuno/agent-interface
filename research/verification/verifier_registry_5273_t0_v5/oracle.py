"""Literal independent decision oracle for frozen v5 construction cases."""


def evaluate(plan, assigned, descriptors, snapshot):
    lookup = {item["check_id"]: item for item in assigned}
    catalog = {item["verifier_id"]: item for item in descriptors}
    output = []
    for check in plan["checks"]:
        row = lookup[check["check_id"]]
        desc = catalog.get(row.get("verifier_id"))
        incoming = check["required_evidence_role"]
        outgoing = row.get("output_role", incoming)
        why = []
        if desc is None:
            state, why = "UNAVAILABLE", ["unknown_verifier"]
        elif (check["primitive"] not in desc["primitives"]
              or incoming not in desc["input_roles"]
              or outgoing not in desc["output_roles"]):
            state, why = "REJECTED", ["hard_incompatibility"]
        elif desc["status"] != "available":
            state, why = "REJECTED", ["verifier_not_current"]
        elif row.get("requested_version", desc["version"]) != desc["version"]:
            state, why = "REJECTED", ["version_mismatch"]
        elif check.get("deadline") is not None and row.get("estimated_cost", 0) > snapshot.get("deadline_budget", 0):
            state, why = "REJECTED", ["deadline_infeasible"]
        elif not snapshot.get("available", False):
            state, why = "UNAVAILABLE", ["resources_unavailable"]
        elif desc.get("network_required", False) and not snapshot.get("network", False):
            state, why = "UNAVAILABLE", ["network_unavailable"]
        else:
            state = "COMPATIBLE"
        output.append({
            "check_id": check["check_id"], "verifier_id": row.get("verifier_id"),
            "primitive": check["primitive"], "input_role": incoming, "output_role": outgoing,
            "requested_version": row.get("requested_version", desc.get("version") if desc else None),
            "estimated_cost": row.get("estimated_cost"), "status": state, "reasons": why,
        })
    states = [item["status"] for item in output]
    total = "REJECTED" if "REJECTED" in states else "UNAVAILABLE" if "UNAVAILABLE" in states else "COMPATIBLE"
    return {"aggregate_status": total, "decisions": output, "dispatch_count": 0, "authority": "NONE"}
