"""Candidate route simulator. Uses public task requests only; no oracle imports."""

from copy import deepcopy


def _draw(objects, width=4, height=1, background="white"):
    pixels = [[background] * width for _ in range(height)]
    for obj in sorted(objects, key=lambda x: x["z"]):
        for x, y in obj["cells"]:
            pixels[y][x] = obj["color"]
    return pixels


def _sheet(case, route):
    a, b = case["initial"]["A"], case["initial"]["B"]
    formula = "SUM(A,B)" if route == "structured" else None
    total = a + b
    artifact = {"kind": "formula_cells" if formula else "literal_cells", "A": a, "B": b, "total": total, "formula": formula, "styles": {}}
    initial_artifact = deepcopy(artifact)
    ops = ["create_formula_sheet"] if formula else ["write_visible_literals"]
    follow = case["followup"]
    if follow["kind"] == "style_only":
        artifact["styles"][follow["cell"]] = follow["style"]
        ops.append("style_visible_cell")
    elif follow["kind"] == "install_formula":
        # The later request explicitly supplies the formula. A flat artifact must rebuild it now.
        artifact["formula"] = follow["formula"]
        artifact["kind"] = "formula_cells"
        ops.append("install_formula_from_new_request")
        for update in follow["updates"]:
            artifact[update["cell"]] = update["value"]
            artifact["total"] = artifact["A"] + artifact["B"]
            ops.append("edit_" + update["cell"])
    visible = [artifact["A"], artifact["B"], artifact["total"]]
    return {"case_id": case["id"], "route": route, "initial_visible": [case["initial"]["A"], case["initial"]["B"], sum(case["initial"].values())], "initial_artifact": initial_artifact, "artifact": artifact, "final_visible": visible, "operations": ops}


def _drawing(case, route):
    spec = case["initial_spec"]
    objects = [{**obj, "cells": [cell[:] for cell in obj["cells"]]} for obj in spec["objects"]]
    render = lambda items: _draw(items, spec["width"], spec["height"], spec["background"])
    if route == "raster":
        artifact = {"kind": "raster", "pixels": render(objects)}
    else:
        artifact = {"kind": "native_objects", "objects": objects}
    initial_artifact = deepcopy(artifact)
    initial = render(objects)
    ops = ["render_flat_raster"] if route == "raster" else ["create_native_objects"]
    follow = case["followup"]
    outcome = "COMPLETED"
    if follow["kind"] == "pixel_only":
        x, y = follow["x"], follow["y"]
        if route == "raster":
            artifact["pixels"][y][x] = follow["color"]
            ops.append("edit_raster_pixel")
            final = artifact["pixels"]
        else:
            obj = next(o for o in artifact["objects"] if o["id"] == "green_marker")
            obj["color"] = follow["color"]
            ops.append("edit_marker_object")
            final = render(artifact["objects"])
    elif follow["kind"] == "move_front_preserve_all_underlay":
        if route == "raster":
            outcome = "UNKNOWN_UNDERLAY_NOT_RETAINED"
            final = None
            ops.append("yield_missing_underlay")
        else:
            obj = next(o for o in artifact["objects"] if o["id"] == follow["object"])
            obj["cells"] = [[x + follow["dx"], y + follow["dy"]] for x, y in obj["cells"]]
            ops.append("move_target_object_preserve_other_layers")
            final = render(artifact["objects"])
    else:
        final = initial
    return {"case_id": case["id"], "route": route, "initial_visible": initial, "initial_artifact": initial_artifact, "artifact": artifact, "outcome": outcome, "final_visible": final, "operations": ops}


def run(cases):
    rows = []
    for case in cases:
        routes = ("flat", "structured") if case["family"] == "spreadsheet" else ("raster", "native")
        for route in routes:
            rows.append(_sheet(case, route) if case["family"] == "spreadsheet" else _drawing(case, route))
    return rows
