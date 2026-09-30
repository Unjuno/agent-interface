"""Independent raw-only recomputation; deliberately does not import candidate."""

import json
from pathlib import Path


def decide(ir, assignments, registry, resources):
    checks = ir["checks"]
    by_assignment = {a["check_id"]: a for a in assignments}
    by_verifier = {v["verifier_id"]: v for v in registry}
    rows = []
    for check in checks:
        a = by_assignment[check["check_id"]]
        v = by_verifier.get(a["verifier_id"])
        primitive = check["primitive"]
        input_role = check["required_evidence_role"]
        output_role = a.get("output_role", input_role)
        reasons = []
        if not isinstance(output_role, str) or not output_role.isupper() or not output_role.replace("_", "").isalnum():
            status, reasons = "REJECTED", ["invalid_output_role"]
        elif v is None:
            status, reasons = "UNAVAILABLE", ["unknown_verifier"]
        elif (primitive not in v.get("primitives", [])
              or input_role not in v.get("input_roles", [])
              or output_role not in v.get("output_roles", [])):
            status, reasons = "REJECTED", ["hard_incompatibility"]
        elif v.get("status") != "available":
            status, reasons = "REJECTED", ["verifier_not_current"]
        elif a.get("requested_version", v.get("version")) != v.get("version"):
            status, reasons = "REJECTED", ["version_mismatch"]
        elif (check.get("deadline") is not None
              and a.get("estimated_cost", 0) > resources.get("deadline_budget", 0)):
            status, reasons = "REJECTED", ["deadline_infeasible"]
        elif not resources.get("available", False):
            status, reasons = "UNAVAILABLE", ["resources_unavailable"]
        elif v.get("network_required", False) and not resources.get("network", False):
            status, reasons = "UNAVAILABLE", ["network_unavailable"]
        else:
            status = "COMPATIBLE"
        rows.append({
            "check_id": check["check_id"], "verifier_id": a.get("verifier_id"),
            "primitive": primitive, "input_role": input_role, "output_role": output_role,
            "requested_version": a.get("requested_version", (v or {}).get("version")),
            "estimated_cost": a.get("estimated_cost"), "status": status, "reasons": reasons,
        })
    states = [r["status"] for r in rows]
    total = "REJECTED" if "REJECTED" in states else "UNAVAILABLE" if "UNAVAILABLE" in states else "COMPATIBLE"
    return {"aggregate_status": total, "decisions": rows, "dispatch_count": 0, "authority": "NONE"}


def audit(raw, cases):
    if set(raw) != {"schema", "rows"} or raw["schema"] != "verifier_registry_raw.v4":
        raise ValueError("raw top-level schema mismatch")
    if len(raw["rows"]) != len(cases):
        raise ValueError("case/raw row count mismatch")
    seen = set()
    for row, case in zip(raw["rows"], cases):
        if set(row) != {"case_id", "ir", "assignments", "registry_snapshot", "resources", "observed"}:
            raise ValueError("raw row schema mismatch")
        if row["case_id"] != case["case_id"] or row["case_id"] in seen:
            raise ValueError("case identity mismatch or duplicate")
        seen.add(row["case_id"])
        ir = row["ir"]
        check_ids = [c["check_id"] for c in ir["checks"]]
        assignment_ids = [a["check_id"] for a in row["assignments"]]
        if len(check_ids) != len(set(check_ids)) or len(assignment_ids) != len(set(assignment_ids)) or set(check_ids) != set(assignment_ids):
            raise ValueError("assignment/check bijection failed")
        expected = decide(ir, row["assignments"], row["registry_snapshot"], row["resources"])
        if row["observed"] != expected:
            raise ValueError("observed output differs from independent recomputation")
        if row["ir"] != case["ir"] or row["assignments"] != case["assignments"] or row["registry_snapshot"] != case["registry_snapshot"] or row["resources"] != case["resources"]:
            raise ValueError("raw inputs differ from frozen case")
    return {"status": "PASS_HOST_CONSTRUCTION_ONLY", "rows": len(seen), "dispatch_count": 0}


def audit_file(raw_path, cases_path):
    raw = json.loads(Path(raw_path).read_text())
    cases = json.loads(Path(cases_path).read_text())
    return audit(raw, cases)
