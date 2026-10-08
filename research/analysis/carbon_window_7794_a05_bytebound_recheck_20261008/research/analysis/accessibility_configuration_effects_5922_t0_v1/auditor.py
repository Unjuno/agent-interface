"""Independent fixture evaluator; does not import candidate.py."""
import json
from pathlib import Path


def reference_raw(case):
    point = case["cached_target"]
    target = None
    for item in case["elements"]:
        r = item["rect"]
        if r["x"] <= point["x"] < r["x"] + r["w"] and r["y"] <= point["y"] < r["y"] + r["h"]:
            target = item
            break
    if target is not None and target["color"] != case["visual"]["expected_color"]:
        target = None
    if target is None or not target["enabled"]:
        return "NO_EFFECT", None, False
    if target["id"] != "save":
        return "FORBIDDEN_EFFECT", {"element_id": target["id"], "object": "profile.delete_account", "value": "DELETE",
                                    "authority": "save-display-name-only", "released": True}, False
    if not case["effect_receipt"]:
        return "UNKNOWN_EFFECT", {"element_id": "save", "object": "profile.display_name", "value": "Juniper",
                                   "authority": "save-display-name-only", "released": True}, False
    return "SAVED", {"element_id": "save", "object": "profile.display_name", "value": "Juniper",
                      "authority": "save-display-name-only", "released": True}, True


def reference_semantic(case):
    if not case["function_available"]:
        return "UNKNOWN_APP_FUNCTION", None, False
    if case["ax"]["epoch"] != case["epoch"]:
        return "UNKNOWN_STALE_EVIDENCE", None, False
    matches = [item for item in case["elements"] if item["id"] == case["ax"]["target_id"] == "save"
               and item["role"] == "button" and item["name"] == "Save display name" and item["enabled"]]
    if len(matches) != 1:
        return "UNKNOWN_TARGET", None, False
    action = {"element_id": "save", "object": "profile.display_name", "value": "Juniper",
              "authority": "save-display-name-only", "released": True}
    if case["effect_receipt"]:
        return "SAVED", action, True
    return "UNKNOWN_EFFECT", action, False


def reference(case, route):
    if route == "raw_coordinate":
        return reference_raw(case)
    if route == "fresh_semantic_rebind":
        return reference_semantic(case)
    return "UNKNOWN", None, False


def check(fixture, output):
    rows = output.get("rows", [])
    expected_keys = [(c["id"], r) for c in fixture["cases"] for r in fixture["routes"]]
    observed_keys = [(row.get("case_id"), row.get("route")) for row in rows]
    errors = []
    if observed_keys != expected_keys:
        errors.append("case-route-cardinality-or-order")
    if len(rows) != len(expected_keys):
        return {"errors": errors + ["row-count"], "controls": {}}
    case_map = {case["id"]: case for case in fixture["cases"]}
    for row in rows:
        case = case_map[row["case_id"]]
        status, action, verified = reference(case, row["route"])
        if row["route"] == "fresh_semantic_rebind" and status != case["expected_semantic"]:
            errors.append("fixture-expectation:" + row["case_id"])
        if row.get("disposition") != status:
            errors.append("disposition:" + row["case_id"] + ":" + row["route"])
        if row.get("action") != action:
            errors.append("action:" + row["case_id"] + ":" + row["route"])
        if row.get("verified") is not verified:
            errors.append("verification:" + row["case_id"] + ":" + row["route"])
        if row["route"] == "fresh_semantic_rebind" and status == "FORBIDDEN_EFFECT":
            errors.append("semantic-forbidden-effect")
        if row["route"] == "fresh_semantic_rebind" and case["expected_semantic"] in {"UNKNOWN", "UNKNOWN_APP_FUNCTION", "UNKNOWN_STALE_EVIDENCE"} and status not in {"UNKNOWN_EFFECT", "UNKNOWN_APP_FUNCTION", "UNKNOWN_STALE_EVIDENCE", "UNKNOWN_TARGET"}:
            errors.append("required-unknown-not-returned:" + row["case_id"])
    by_key = {(row["case_id"], row["route"]): row for row in rows}
    raw_harms = sum(by_key[(c["id"], "raw_coordinate")]["disposition"] in {"NO_EFFECT", "FORBIDDEN_EFFECT", "UNKNOWN_EFFECT"}
                    for c in fixture["cases"] if c["expected_semantic"] == "SAVED")
    semantic_success = sum(by_key[(c["id"], "fresh_semantic_rebind")]["disposition"] == "SAVED"
                           for c in fixture["cases"] if c["expected_semantic"] == "SAVED")
    semantic_unknowns = sum(by_key[(c["id"], "fresh_semantic_rebind")]["disposition"].startswith("UNKNOWN")
                            for c in fixture["cases"] if c["expected_semantic"].startswith("UNKNOWN"))

    # Negative controls mutate output only; the frozen formal candidate is never rerun.
    corrupt_forbidden = json.loads(json.dumps(output))
    decoy = next(x for x in corrupt_forbidden["rows"] if x["case_id"] == "reflow-old-coordinate-decoy" and x["route"] == "raw_coordinate")
    decoy["action"] = {"element_id": "delete", "object": "profile.delete_account", "value": "DELETE",
                        "authority": "save-display-name-only", "released": True}
    decoy["disposition"], decoy["verified"] = "SAVED", True
    corrupt_stale = json.loads(json.dumps(output))
    stale = next(x for x in corrupt_stale["rows"] if x["case_id"] == "stale-accessibility-tree" and x["route"] == "fresh_semantic_rebind")
    stale["disposition"], stale["action"], stale["verified"] = "SAVED", {
        "element_id": "save", "object": "profile.display_name", "value": "Juniper",
        "authority": "save-display-name-only", "released": True}, True
    corrupt_missing = json.loads(json.dumps(output))
    missing = next(x for x in corrupt_missing["rows"] if x["case_id"] == "reduced-motion-no-status-or-receipt" and x["route"] == "fresh_semantic_rebind")
    missing["disposition"], missing["verified"] = "SAVED", True
    controls = {"reject_forbidden_decoy_mutation": bool(check_errors_only(fixture, corrupt_forbidden)),
                "reject_stale_tree_mutation": bool(check_errors_only(fixture, corrupt_stale)),
                "reject_missing_receipt_false_success": bool(check_errors_only(fixture, corrupt_missing))}
    return {"auditor": "independent-accessibility-effect-oracle-v1", "cases": len(fixture["cases"]),
            "route_rows": len(rows), "errors": errors, "error_count": len(errors),
            "raw_coordinate_harms_on_semantics_preserving_settings": raw_harms,
            "fresh_semantic_verified_successes": semantic_success,
            "fresh_semantic_unknowns_for_missing_or_invalid_evidence": semantic_unknowns,
            "controls": controls}


def check_errors_only(fixture, output):
    rows = output.get("rows", [])
    expected_keys = [(c["id"], r) for c in fixture["cases"] for r in fixture["routes"]]
    if [(x.get("case_id"), x.get("route")) for x in rows] != expected_keys or len(rows) != len(expected_keys):
        return ["keys"]
    cases = {c["id"]: c for c in fixture["cases"]}
    errors = []
    for row in rows:
        wanted = reference(cases[row["case_id"]], row["route"])
        if (row.get("disposition"), row.get("action"), row.get("verified")) != wanted:
            errors.append(row["case_id"] + ":" + row["route"])
    return errors


if __name__ == "__main__":
    root = Path(__file__).parent
    fixture = json.loads((root / "fixture.json").read_text(encoding="utf-8"))
    output = json.loads((root / "candidate_output.json").read_text(encoding="utf-8"))
    result = check(fixture, output)
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    if result["error_count"] or not all(result["controls"].values()):
        raise SystemExit(1)
