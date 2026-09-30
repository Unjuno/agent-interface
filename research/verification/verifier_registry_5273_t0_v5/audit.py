"""Raw-only audit. Imports the independent oracle, never the candidate."""

import json
from pathlib import Path

from oracle import evaluate


def audit(raw, cases):
    if set(raw) != {"schema", "rows"} or raw["schema"] != "verifier_registry_raw.v5":
        raise ValueError("raw schema mismatch")
    if len(raw["rows"]) != len(cases):
        raise ValueError("case count mismatch")
    observed_ids = set()
    for row, case in zip(raw["rows"], cases):
        if set(row) != {"case_id", "ir", "assignments", "registry_snapshot", "resources", "observed"}:
            raise ValueError("row schema mismatch")
        if row["case_id"] != case["case_id"] or row["case_id"] in observed_ids:
            raise ValueError("case ID mismatch or duplicate")
        observed_ids.add(row["case_id"])
        check_ids = [item["check_id"] for item in row["ir"]["checks"]]
        assigned_ids = [item["check_id"] for item in row["assignments"]]
        if len(check_ids) != len(set(check_ids)) or len(assigned_ids) != len(set(assigned_ids)) or set(check_ids) != set(assigned_ids):
            raise ValueError("IR and assignment IDs are not bijective")
        if any(row[key] != case[key] for key in ("ir", "assignments", "registry_snapshot", "resources")):
            raise ValueError("raw case input differs from frozen input")
        expected = evaluate(row["ir"], row["assignments"], row["registry_snapshot"], row["resources"])
        if row["observed"] != expected:
            raise ValueError("candidate output disagrees with independent decision oracle")
    return {"status": "PASS_HOST_CONSTRUCTION_ONLY", "cases": len(observed_ids), "dispatch_count": 0}


def audit_files(raw_path, cases_path):
    return audit(json.loads(Path(raw_path).read_text()), json.loads(Path(cases_path).read_text()))
