"""Finite operational-representation assay for Issue #6624; no real app semantics."""
import json
import sys
from pathlib import Path


def start(family, route, contract):
    if family == "spreadsheet":
        if route == "structured":
            return {"cells": {"A1": 2, "A2": 3, "TOTAL": 5, "B1": "KEEP"}, "formula": "=A1+A2"}
        return {"pixels": {"A1": 2, "A2": 3, "TOTAL": 5, "B1": "KEEP"}}
    if route == "structured":
        return {"elements": {"title": "ALPHA", "body": "KEEP"}, "footer": "KEEP"}
    return {"raster": {"title": "ALPHA", "body": "KEEP", "footer": "KEEP"}}


def apply(case, route, fixture):
    family, operation = case["family"], case["operation"]
    state = start(family, route, fixture["contracts"])
    if family == "spreadsheet":
        initial_render = {"A1": 2, "A2": 3, "TOTAL": 5, "B1": "KEEP"}
    else:
        initial_render = {"title": "ALPHA", "body": "KEEP", "footer": "KEEP"}
    post = None
    if operation == "spreadsheet_increment_A2":
        op = fixture["operations"][operation]
        if route == "structured":
            state["cells"][op["cell"]] = op["to"]
            # Formula is the only source of the new total for this route.
            state["cells"]["TOTAL"] = state["cells"]["A1"] + state["cells"]["A2"]
        else:
            # Pixels preserve the initial appearance but have no cell/formula model.
            state["pixels"][op["cell"]] = op["to"]
        post = {"status": "COMPLETE" if route == "structured" else "UNKNOWN", "state": state}
    elif operation == "drawing_replace_title":
        op = fixture["operations"][operation]
        if route == "structured":
            state["elements"][op["target"]] = op["to"]
            post = {"status": "COMPLETE", "state": state}
        else:
            post = {"status": "UNKNOWN", "state": state}
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
            state["elements"]["pixel_patch"] = {"pixel": op["pixel"], "color": op["to"]}
        post = {"status": "COMPLETE", "state": state}
    initial_cost = fixture["cost_assumptions"]["initial"][route]
    follow_cost = fixture["cost_assumptions"]["followup"][operation][route]
    return {"initial": {"render": initial_render, "state": state if operation == "none" else start(family, route, fixture["contracts"])},
            "post": post, "cost": {"initial": initial_cost, "followup": follow_cost, "total": initial_cost + follow_cost}}


def run(fixture):
    cases = []
    for family, operation in [("spreadsheet", "none"), ("spreadsheet", "spreadsheet_increment_A2"),
                              ("spreadsheet", "pixel_patch"), ("drawing", "none"),
                              ("drawing", "drawing_replace_title"), ("drawing", "pixel_patch")]:
        cases.append({"id": f"{family}:{operation}", "family": family, "operation": operation,
                      "routes": {route: apply({"family": family, "operation": operation}, route, fixture)
                                 for route in ("flat", "structured")}})
    return {"schema": "representation-contrast-raw-v1", "cases": cases}


if __name__ == "__main__":
    fixture = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    raw = run(fixture)
    Path(sys.argv[2]).write_text(json.dumps(raw, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({"case_count": len(raw["cases"]), "schema": raw["schema"]}, sort_keys=True))
