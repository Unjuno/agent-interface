"""Independent raw-only reconstruction for the Issue #6610 T0 assay."""
import copy
import json
import sys
from pathlib import Path


def expected_case(case, fixture):
    family, follow = case["family"], fixture["followups"][case["followup"]]
    exp = fixture["initial_contract"][family]
    out = {}
    for route in ("flat", "structured"):
        if family == "spreadsheet":
            state = {"cells": {"A1": 2, "A2": 3, "TOTAL": 5}, "untouched": {"B1": "KEEP"},
                     "formula": "=SUM(A1:A2)" if route == "structured" else None,
                     "formula_value": 5 if route == "structured" else None}
            initial_render = {"A1": 2, "A2": 3, "TOTAL": 5}
            visible_ok = initial_render == exp["visible_cells"] and state["untouched"] == exp["untouched"]
        else:
            state = {"elements": [{"id": "title", "text": "ALPHA"}, {"id": "body", "text": "KEEP"}],
                     "untouched": {"footer": "KEEP"},
                     "native_element_ids": ["title", "body"] if route == "structured" else []}
            initial_render = ["ALPHA", "KEEP"]
            visible_ok = initial_render == [x["text"] for x in exp["visible_elements"]] and state["untouched"] == exp["untouched"]
        requirement = exp.get("required_structure")
        structure_ok = requirement is None or (route == "structured" and requirement in ("formula", "native_elements"))
        initial_ok = visible_ok and structure_ok
        if follow["kind"] == "spreadsheet_source_increment":
            state["cells"][follow["cell"]] = follow["to"]
            total = state["cells"]["A1"] + state["cells"]["A2"]
            if route == "structured":
                if state["formula"] != "=SUM(A1:A2)":
                    raise AssertionError("structured formula witness missing")
                state["formula_value"] = total
                state["cells"]["TOTAL"] = total
            else:
                state["formula_value"] = None
                state["cells"]["TOTAL"] = total
            post_render = dict(state["cells"])
            post_ok = (state["cells"]["TOTAL"] == follow["expected_total"] and
                       state["untouched"] == exp["untouched"] and
                       (route != "structured" or state["formula_value"] == total))
        elif follow["kind"] == "drawing_title_replace":
            found = [x for x in state["elements"] if x["id"] == follow["element_id"]]
            if len(found) != 1:
                raise AssertionError("target identity is not unique")
            found[0]["text"] = follow["to"]
            post_render = [x["text"] for x in state["elements"]]
            post_ok = (found[0]["text"] == follow["to"] and state["untouched"] == exp["untouched"] and
                       post_render[1] == "KEEP")
        elif follow["kind"] == "raster_pixel_patch":
            post_render = {"pixel": list(follow["pixel"]), "color": follow["to"], "base": initial_render}
            post_ok = post_render["pixel"] == list(follow["pixel"]) and post_render["color"] == follow["to"]
        else:
            post_render, post_ok = None, None
        initial_cost = fixture["routes"][route]["initial_cost"]
        followup_cost = follow["followup_cost"][route]
        out[route] = {"initial": {"pass": initial_ok, "render": initial_render, "state":
                       {k: v for k, v in state.items()} if follow["kind"] == "none" else initial_state_for(family, route)},
                      "post": None if post_render is None else {"pass": post_ok, "render": post_render, "state": state},
                      "initial_cost": initial_cost, "followup_cost": followup_cost,
                      "total_cost": initial_cost + followup_cost}
        if follow["kind"] == "none":
            out[route]["initial"]["state"] = initial_state_for(family, route)
    return {"case_id": case["case_id"], "family": family, "followup": case["followup"], "routes": out}


def initial_state_for(family, route):
    if family == "spreadsheet":
        return {"cells": {"A1": 2, "A2": 3, "TOTAL": 5}, "untouched": {"B1": "KEEP"},
                "formula": "=SUM(A1:A2)" if route == "structured" else None,
                "formula_value": 5 if route == "structured" else None}
    return {"elements": [{"id": "title", "text": "ALPHA"}, {"id": "body", "text": "KEEP"}],
            "untouched": {"footer": "KEEP"}, "native_element_ids": ["title", "body"] if route == "structured" else []}


def verify(raw, fixture):
    errors = []
    if raw.get("schema") != "post-success-changeability-raw-v1" or raw.get("fixture_schema") != fixture.get("schema"):
        errors.append("schema")
    expected = [expected_case(case, fixture) for case in fixture["cases"]]
    if raw.get("cases") != expected:
        errors.append("case-reconstruction")
    if len(raw.get("cases", [])) != 6 or [x.get("case_id") for x in raw.get("cases", [])] != [x["case_id"] for x in fixture["cases"]]:
        errors.append("case-denominator-order")
    for row in raw.get("cases", []):
        for route in ("flat", "structured"):
            r = row.get("routes", {}).get(route, {})
            if r.get("initial", {}).get("pass") is not True or (r.get("post") is not None and r["post"].get("pass") is not True):
                errors.append(f"effect-gate:{row.get('case_id')}:{route}")
        if row.get("routes", {}).get("flat", {}).get("initial", {}).get("render") != row.get("routes", {}).get("structured", {}).get("initial", {}).get("render"):
            errors.append(f"initial-equivalence:{row.get('case_id')}")
    comparisons = []
    for family in ("spreadsheet", "drawing"):
        structural = next(x for x in raw["cases"] if x["family"] == family and "structural" in x["followup"])
        nofollow = next(x for x in raw["cases"] if x["family"] == family and x["followup"] == "none")
        raster = next(x for x in raw["cases"] if x["family"] == family and "raster_patch" in x["followup"])
        initial_flat = nofollow["routes"]["flat"]["total_cost"]
        initial_structured = nofollow["routes"]["structured"]["total_cost"]
        mix = fixture["followup_distribution"]
        expected_flat = sum(mix[name] * next(x for x in raw["cases"] if x["family"] == family and x["followup"] == ("none" if name == "none" else family+"_"+name))["routes"]["flat"]["total_cost"] for name in mix)
        expected_structured = sum(mix[name] * next(x for x in raw["cases"] if x["family"] == family and x["followup"] == ("none" if name == "none" else family+"_"+name))["routes"]["structured"]["total_cost"] for name in mix)
        if not initial_flat < initial_structured:
            errors.append(f"initial-ranking:{family}")
        if not expected_structured < expected_flat:
            errors.append(f"mixture-inversion:{family}")
        if not raster["routes"]["flat"]["total_cost"] < raster["routes"]["structured"]["total_cost"]:
            errors.append(f"raster-flat-preferred:{family}")
        if not nofollow["routes"]["flat"]["total_cost"] < nofollow["routes"]["structured"]["total_cost"]:
            errors.append(f"no-followup-flat-preferred:{family}")
        comparisons.append({
            "family": family,
            "initial_flat": initial_flat,
            "initial_structured": initial_structured,
            "mixture_expected_flat": expected_flat,
            "mixture_expected_structured": expected_structured,
            "no_followup_flat": nofollow["routes"]["flat"]["total_cost"],
            "no_followup_structured": nofollow["routes"]["structured"]["total_cost"],
            "raster_patch_flat": raster["routes"]["flat"]["total_cost"],
            "raster_patch_structured": raster["routes"]["structured"]["total_cost"],
        })
    # Effective corruption controls: each mutation must create a verification error.
    controls = []
    mutants = []
    m = copy.deepcopy(raw); m["cases"][0]["routes"]["flat"]["initial"]["pass"] = False; mutants.append(m)
    m = copy.deepcopy(raw); m["cases"][1]["routes"]["flat"]["post"]["state"].setdefault("untouched", {})["B1"] = "CHANGED"; mutants.append(m)
    m = copy.deepcopy(raw); m["cases"][1]["routes"]["structured"]["post"]["state"]["formula"] = "=SUM(A1:B1)"; mutants.append(m)
    m = copy.deepcopy(raw); m["cases"][1]["routes"]["flat"]["initial"]["state"]["native_element_ids"] = ["title"]; mutants.append(m)
    controls = [bool(verify_core(m, fixture)) for m in mutants]
    stricter = copy.deepcopy(fixture)
    stricter["initial_contract"]["spreadsheet"]["required_structure"] = "formula"
    controls.append(bool(verify_core(raw, stricter)))
    if controls != [True, True, True, True, True]:
        errors.append("corruption-controls")
    return errors, {"controls_rejected": sum(controls), "controls_total": 5, "cost_comparison": comparisons}


def verify_core(raw, fixture):
    # Core deliberately excludes recursive corruption-control evaluation.
    expected = [expected_case(case, fixture) for case in fixture["cases"]]
    errors = []
    if raw.get("schema") != "post-success-changeability-raw-v1" or raw.get("fixture_schema") != fixture.get("schema"):
        errors.append("schema")
    if raw.get("cases") != expected:
        errors.append("case-reconstruction")
    return errors


def main(fixture_path, raw_path, audit_path):
    fixture = json.loads(Path(fixture_path).read_text(encoding="utf-8"))
    raw = json.loads(Path(raw_path).read_text(encoding="utf-8"))
    errors, controls = verify(raw, fixture)
    result = {"schema": "post-success-changeability-audit-v1", "disposition": "METHOD_PASS_SCOPED" if not errors else "FAIL_AUDIT",
              "case_count": len(raw.get("cases", [])), "checks": 35, "errors": errors, **controls,
              "initial_ranking": "flat<structured" if not errors else "unverified",
              "followup_mixture_ranking": "structured<flat" if not errors else "unverified",
              "scope": "finite synthetic assay sensitivity; no real editability or user benefit claim"}
    Path(audit_path).write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: audit.py FIXTURE.json RAW.json AUDIT.json")
    main(*sys.argv[1:])
