"""Raw-only oracle for Issue #6624; independently derives expected state/effects."""
import copy
import json
import sys
from pathlib import Path


def initial(family, route):
    if family == "spreadsheet":
        if route == "structured":
            return {"cells": {"A1": 2, "A2": 3, "TOTAL": 5, "B1": "KEEP"}, "formula": "=A1+A2"}
        return {"pixels": {"A1": 2, "A2": 3, "TOTAL": 5, "B1": "KEEP"}}
    if route == "structured":
        return {"elements": {"title": "ALPHA", "body": "KEEP"}, "footer": "KEEP"}
    return {"raster": {"title": "ALPHA", "body": "KEEP", "footer": "KEEP"}}


def expected(case, fixture):
    family, operation = case["family"], case["operation"]
    result = {}
    for route in ("flat", "structured"):
        state0 = initial(family, route)
        state = copy.deepcopy(state0)
        if family == "spreadsheet":
            render = {"A1": 2, "A2": 3, "TOTAL": 5, "B1": "KEEP"}
        else:
            render = {"title": "ALPHA", "body": "KEEP", "footer": "KEEP"}
        post = None
        if operation == "spreadsheet_increment_A2":
            if route == "structured":
                a1, a2 = 2, fixture["operations"][operation]["to"]
                state["cells"]["A2"] = a2
                state["cells"]["TOTAL"] = a1 + a2
                status = "COMPLETE" if state["formula"] == "=A1+A2" else "FAIL"
            else:
                # Raster-only evidence cannot establish the changed semantic total.
                state["pixels"]["A2"] = fixture["operations"][operation]["to"]
                status = "UNKNOWN"
            post = {"status": status, "state": state}
        elif operation == "drawing_replace_title":
            if route == "structured":
                state["elements"]["title"] = fixture["operations"][operation]["to"]
                status = "COMPLETE" if state["elements"].get("body") == "KEEP" else "FAIL"
            else:
                status = "UNKNOWN"
            post = {"status": status, "state": state}
        elif operation == "pixel_patch":
            op = fixture["operations"][operation]
            if family == "spreadsheet":
                if route == "structured":
                    state["cells"]["pixel_patch"] = {"pixel": op["pixel"], "color": op["to"]}
                else:
                    state["pixels"]["patch"] = {"pixel": op["pixel"], "color": op["to"]}
            elif route == "flat":
                state["raster"]["patch"] = {"pixel": op["pixel"], "color": op["to"]}
            else:
                # This operation asks only for a pixel change, not for structural editability.
                state["elements"]["pixel_patch"] = {"pixel": op["pixel"], "color": op["to"]}
            post = {"status": "COMPLETE", "state": state}
        cost = fixture["cost_assumptions"]
        result[route] = {"initial": {"render": render, "state": state0}, "post": post,
                         "cost": {"initial": cost["initial"][route],
                                  "followup": cost["followup"][operation][route],
                                  "total": cost["initial"][route] + cost["followup"][operation][route]}}
    return {"id": f"{family}:{operation}", "family": family, "operation": operation, "routes": result}


def core_errors(raw, fixture):
    errors = []
    if fixture.get("contracts", {}).get("drawing_visible", {}).get("required_structure") is not None:
        errors.append("initial-contract-strengthened")
    declared = [("spreadsheet", "none"), ("spreadsheet", "spreadsheet_increment_A2"),
                ("spreadsheet", "pixel_patch"), ("drawing", "none"),
                ("drawing", "drawing_replace_title"), ("drawing", "pixel_patch")]
    cases = [{"id": f"{f}:{o}", "family": f, "operation": o} for f, o in declared]
    expected_rows = [expected(c, fixture) for c in cases]
    if raw.get("schema") != "representation-contrast-raw-v1" or raw.get("cases") != expected_rows:
        errors.append("independent-row-reconstruction")
    for row in raw.get("cases", []):
        routes = row.get("routes", {})
        if routes.get("flat", {}).get("initial", {}).get("render") != routes.get("structured", {}).get("initial", {}).get("render"):
            errors.append(f"initial-parity:{row.get('id')}")
    # Operational distinction is structural, not a descriptive route label.
    for row_id in ("spreadsheet:none", "spreadsheet:spreadsheet_increment_A2"):
        row = next((x for x in raw.get("cases", []) if x.get("id") == row_id), {})
        flat = row.get("routes", {}).get("flat", {}).get("initial", {}).get("state", {})
        if "cells" in flat or "formula" in flat:
            errors.append("flat-spreadsheet-retained-hidden-structure")
    for row_id in ("drawing:none", "drawing:drawing_replace_title"):
        row = next((x for x in raw.get("cases", []) if x.get("id") == row_id), {})
        flat = row.get("routes", {}).get("flat", {}).get("initial", {}).get("state", {})
        if "elements" in flat or "native_element_ids" in flat:
            errors.append("flat-drawing-retained-hidden-structure")
    return errors


def verify(raw, fixture):
    errors = core_errors(raw, fixture)
    rows = raw.get("cases", [])
    for family in ("spreadsheet", "drawing"):
        prefix = "spreadsheet_increment_A2" if family == "spreadsheet" else "drawing_replace_title"
        structural = next((r for r in rows if r.get("id") == f"{family}:{prefix}"), {})
        nofollow = next((r for r in rows if r.get("id") == f"{family}:none"), {})
        pixel = next((r for r in rows if r.get("id") == f"{family}:pixel_patch"), {})
        if structural.get("routes", {}).get("flat", {}).get("post", {}).get("status") != "UNKNOWN":
            errors.append(f"flat-structural-unknown:{family}")
        if structural.get("routes", {}).get("structured", {}).get("post", {}).get("status") != "COMPLETE":
            errors.append(f"structured-effect:{family}")
        if not nofollow.get("routes", {}).get("flat", {}).get("cost", {}).get("total", 999) < nofollow.get("routes", {}).get("structured", {}).get("cost", {}).get("total", -1):
            errors.append(f"flat-nofollowup-preferred:{family}")
        if not pixel.get("routes", {}).get("flat", {}).get("cost", {}).get("total", 999) < pixel.get("routes", {}).get("structured", {}).get("cost", {}).get("total", -1):
            errors.append(f"flat-pixel-preferred:{family}")
    # Independent cost-mixture arithmetic; compare expected abstract costs, not candidate labels.
    mix, costs = fixture["cost_assumptions"]["mixture"], fixture["cost_assumptions"]
    inversions = {}
    for family in ("spreadsheet", "drawing"):
        structural_op = "spreadsheet_increment_A2" if family == "spreadsheet" else "drawing_replace_title"
        weighted = {}
        for route in ("flat", "structured"):
            weighted[route] = (costs["initial"][route] + mix["structural"] * costs["followup"][structural_op][route]
                               + mix["pixel_patch"] * costs["followup"]["pixel_patch"][route])
        inversions[family] = weighted
        if not weighted["structured"] < weighted["flat"]:
            errors.append(f"mixture-ranking:{family}")
    # Mutation set: answer injection, hidden structure, wrong target, collateral mutation,
    # false formula, pixel-only editability assertion, and initial-contract strengthening.
    mutations = []
    m = copy.deepcopy(raw); m["cases"][1]["routes"]["flat"]["post"]["state"]["pixels"]["TOTAL"] = 6; mutations.append((m, fixture))
    m = copy.deepcopy(raw); m["cases"][0]["routes"]["flat"]["initial"]["state"]["cells"] = {"A1": 2}; mutations.append((m, fixture))
    m = copy.deepcopy(raw); m["cases"][4]["routes"]["structured"]["post"]["state"]["elements"]["body"] = "BETA"; mutations.append((m, fixture))
    m = copy.deepcopy(raw); m["cases"][4]["routes"]["structured"]["post"]["state"]["footer"] = "CHANGED"; mutations.append((m, fixture))
    m = copy.deepcopy(raw); m["cases"][1]["routes"]["structured"]["post"]["state"]["formula"] = "=A1-A2"; mutations.append((m, fixture))
    m = copy.deepcopy(raw); m["cases"][4]["routes"]["flat"]["post"] = {"status": "COMPLETE", "state": {"raster": {"patch": "editable"}}}; mutations.append((m, fixture))
    strengthened = copy.deepcopy(fixture); strengthened["contracts"]["drawing_visible"]["required_structure"] = "native_elements"
    mutations.append((raw, strengthened))
    rejected = [bool(core_errors(m, f)) for m, f in mutations]
    if rejected != [True] * len(mutations):
        errors.append("mutation-controls")
    return {"schema": "representation-contrast-audit-v1", "disposition": "METHOD_PASS_SCOPED" if not errors else "FAIL_AUDIT",
            "case_count": len(rows), "errors": errors, "mutation_controls_rejected": sum(rejected),
            "mutation_controls_total": len(rejected), "weighted_cost_units": inversions,
            "scope": "synthetic finite assay sensitivity; abstract costs; no real app, model, user artifact, or product claim"}


if __name__ == "__main__":
    fixture = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    raw = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    result = verify(raw, fixture)
    Path(sys.argv[3]).write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if not result["errors"] else 1)
