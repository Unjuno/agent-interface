"""Finite synthetic assay for post-success artifact changeability (Issue #6610)."""
import json
import copy
import sys
from pathlib import Path


def initial_state(family, route, contract):
    if family == "spreadsheet":
        state = {"cells": {"A1": 2, "A2": 3, "TOTAL": 5}, "untouched": {"B1": "KEEP"},
                 "formula": "=SUM(A1:A2)" if route == "structured" else None,
                 "formula_value": 5 if route == "structured" else None}
        rendered = {"A1": 2, "A2": 3, "TOTAL": 5}
    else:
        state = {"elements": [{"id": "title", "text": "ALPHA"}, {"id": "body", "text": "KEEP"}],
                 "untouched": {"footer": "KEEP"},
                 "native_element_ids": ["title", "body"] if route == "structured" else []}
        rendered = ["ALPHA", "KEEP"]
    expected = contract[family]
    return state, rendered, expected


def run_case(case, fixture):
    family, followup_id = case["family"], case["followup"]
    follow = fixture["followups"][followup_id]
    rows = {}
    for route in ("flat", "structured"):
        state, rendered, expected = initial_state(family, route, fixture["initial_contract"])
        visible_ok = rendered == (expected["visible_cells"] if family == "spreadsheet" else [x["text"] for x in expected["visible_elements"]]) and state["untouched"] == expected["untouched"]
        requirement = expected.get("required_structure")
        structure_ok = requirement is None or (route == "structured" and requirement in ("formula", "native_elements"))
        initial_pass = visible_ok and structure_ok
        initial = {"pass": initial_pass, "render": rendered, "state": copy.deepcopy(state)}
        post = None
        if follow["kind"] == "spreadsheet_source_increment":
            state["cells"][follow["cell"]] = follow["to"]
            if route == "structured":
                state["formula_value"] = state["cells"]["A1"] + state["cells"]["A2"]
                state["cells"]["TOTAL"] = state["formula_value"]
            else:
                state["formula_value"] = None
                state["cells"]["TOTAL"] = follow["expected_total"]
            post = {"pass": state["cells"]["TOTAL"] == follow["expected_total"] and state["untouched"] == expected["untouched"],
                    "render": dict(state["cells"]), "state": state}
        elif follow["kind"] == "drawing_title_replace":
            target = next(x for x in state["elements"] if x["id"] == follow["element_id"])
            target["text"] = follow["to"]
            post = {"pass": target["text"] == follow["to"] and state["untouched"] == expected["untouched"],
                    "render": [x["text"] for x in state["elements"]], "state": state}
        elif follow["kind"] == "raster_pixel_patch":
            post = {"pass": True, "render": {"pixel": list(follow["pixel"]), "color": follow["to"], "base": rendered},
                    "state": state}
        total_cost = fixture["routes"][route]["initial_cost"] + follow["followup_cost"][route]
        rows[route] = {"initial": initial, "post": post, "initial_cost": fixture["routes"][route]["initial_cost"],
                       "followup_cost": follow["followup_cost"][route], "total_cost": total_cost}
    return {"case_id": case["case_id"], "family": family, "followup": followup_id, "routes": rows}


def main(fixture_path, raw_path):
    fixture = json.loads(Path(fixture_path).read_text(encoding="utf-8"))
    raw = {"schema": "post-success-changeability-raw-v1",
           "fixture_schema": fixture["schema"],
           "cases": [run_case(case, fixture) for case in fixture["cases"]]}
    Path(raw_path).write_text(json.dumps(raw, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({"schema": raw["schema"], "case_count": len(raw["cases"]), "raw_path": str(raw_path)}, sort_keys=True))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: candidate.py FIXTURE.json RAW.json")
    main(sys.argv[1], sys.argv[2])
