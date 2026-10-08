"""Independent, deliberately small acceptance oracle; does not import candidate."""


def decide(case):
    ir, assignment, registry, resources = (
        case["ir"], case["assignments"], case["registry"], case["resources"])
    if len(assignment) != len(ir["checks"]):
        return {"aggregate_status": "REJECTED",
                "decisions": [{"check_id": c["check_id"], "status": "REJECTED",
                               "reason": "assignment_coverage_mismatch", "authority": "NONE",
                               "dispatch_count": 0} for c in ir["checks"]],
                "dispatch_count": 0, "authority": "NONE"}
    decisions = []
    for check in ir["checks"]:
        matches = [a for a in assignment if a["check_id"] == check["check_id"]]
        if len(matches) != 1:
            decisions.append({"check_id": check["check_id"], "status": "REJECTED",
                              "reason": "assignment_coverage_mismatch", "authority": "NONE",
                              "dispatch_count": 0})
            continue
        a = matches[0]
        ds = [d for d in registry if d["verifier_id"] == a["verifier_id"]]
        if len(ds) != 1:
            decisions.append({"check_id": check["check_id"], "status": "REJECTED",
                              "reason": "unknown_verifier", "authority": "NONE",
                              "dispatch_count": 0})
            continue
        d = ds[0]
        mode = a["mode"]
        cost = d[mode + "_cost"]
        status, reason = "COMPATIBLE", "compatible"
        if check["primitive"] not in d["supported_primitives"]:
            status, reason = "REJECTED", "unsupported_primitive"
        elif check["required_evidence_role"] not in d["accepted_evidence_roles"]:
            status, reason = "REJECTED", "wrong_input_role"
        elif a["output_role"] not in d["output_evidence_roles"]:
            status, reason = "REJECTED", "wrong_output_role"
        elif a["requested_version"] != d["version"]:
            status, reason = "REJECTED", "stale_verifier_version"
        elif d["authority"] != "none":
            status, reason = "REJECTED", "authority_not_permitted"
        elif d["side_effect_class"] in resources["forbidden_side_effect_classes"]:
            status, reason = "REJECTED", "side_effect_prohibited"
        elif check["deadline"] is not None and d["latency_envelope"]["bound"] > check["deadline"]:
            status, reason = "REJECTED", "deadline_infeasible"
        elif d["resource_class"] not in resources["available_classes"]:
            status, reason = "UNAVAILABLE", "resources_unavailable"
        elif cost > resources[mode + "_cost_budget"]:
            status, reason = "REJECTED", mode + "_budget_exceeded"
        decisions.append({"check_id": check["check_id"], "status": status, "reason": reason})
    statuses = {d["status"] for d in decisions}
    aggregate = ("REJECTED" if "REJECTED" in statuses else
                 "UNAVAILABLE" if "UNAVAILABLE" in statuses else "COMPATIBLE")
    return {"aggregate_status": aggregate, "decisions": decisions,
            "dispatch_count": 0, "authority": "NONE"}
