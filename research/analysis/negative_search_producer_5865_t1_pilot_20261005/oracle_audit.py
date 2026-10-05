def audit_rows(rows):
    errors = []
    certified = 0
    eligible = 0
    for row in rows:
        candidate = row["candidate"]
        oracle = row["oracle"]
        status = candidate.get("status")
        matches = oracle.get("matching_ids", [])
        complete = oracle.get("complete") is True
        if complete and not matches:
            eligible += 1

        if status == "NO_MATCH_WITHIN_CERTIFIED_SCOPE":
            scope = candidate.get("scope", {})
            if not complete:
                kind = "unsupported_negative"
            elif matches:
                kind = "false_negative"
            elif (scope.get("surface_id") != oracle.get("surface_id")
                  or scope.get("epoch") != oracle.get("epoch")):
                kind = "scope_mismatch"
            else:
                certified += 1
                continue
            errors.append({"case_id": row.get("case_id"), "kind": kind})
        elif status == "MATCH_FOUND" and complete and not matches:
            errors.append({"case_id": row.get("case_id"), "kind": "false_positive"})

    coverage = certified / eligible if eligible else None
    return {
        "status": "PASS_AUDIT" if not errors else "FAIL_AUDIT",
        "errors": errors,
        "certified_negative_count": certified,
        "eligible_negative_count": eligible,
        "useful_coverage": coverage,
    }
