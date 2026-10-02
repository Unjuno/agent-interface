"""Independent raw-only semantic, structure, rendering and cost auditor."""


def _render_oracle(layers, canvas):
    pixels = [[canvas["background"]] * canvas["width"] for _ in range(canvas["height"])]
    for layer in sorted(layers, key=lambda x: x["z"]):
        for x, y in layer["cells"]:
            pixels[y][x] = layer["color"]
    return pixels


def _expected_sheet(case, route, truth):
    source = truth["spreadsheet_source"]
    a, b = source["A"], source["B"]
    expected_formula = source["followup_formula"] if route == "structured" else None
    if case["followup"]["kind"] == "install_formula":
        expected_formula = source["followup_formula"]
        for update in case["followup"]["updates"]:
            if update["cell"] == "A":
                a = update["value"]
            elif update["cell"] == "B":
                b = update["value"]
    formula_kind = "formula_cells" if expected_formula else "literal_cells"
    expected_total = a + b
    return {"A": a, "B": b, "total": expected_total, "formula": expected_formula, "kind": formula_kind}


def _expected_draw(case, route, layers, truth_canvas):
    expected_initial = _render_oracle(layers, truth_canvas)
    follow = case["followup"]["kind"]
    if follow == "none":
        return expected_initial, "COMPLETED", expected_initial
    if follow == "pixel_only":
        expected = [row[:] for row in expected_initial]
        expected[case["followup"]["y"]][case["followup"]["x"]] = case["followup"]["color"]
        return expected_initial, "COMPLETED", expected
    if route == "raster":
        return expected_initial, "UNKNOWN_UNDERLAY_NOT_RETAINED", None
    moved = [dict(x, cells=[c[:] for c in x["cells"]]) for x in layers]
    obj = next(x for x in moved if x["id"] == "blue_front")
    obj["cells"] = [[x + 1, y] for x, y in obj["cells"]]
    return expected_initial, "COMPLETED", _render_oracle(moved, truth_canvas)


def audit(public, truth, costs, raw):
    errors = []
    cases = public["cases"]
    expected_keys = {(c["id"], r) for c in cases for r in (("flat", "structured") if c["family"] == "spreadsheet" else ("raster", "native"))}
    got = {(row.get("case_id"), row.get("route")): row for row in raw if isinstance(row, dict)}
    if set(got) != expected_keys:
        errors.append("ROW_COVERAGE")
    for case in cases:
        for route in (("flat", "structured") if case["family"] == "spreadsheet" else ("raster", "native")):
            row = got.get((case["id"], route))
            if row is None:
                continue
            if case["family"] == "spreadsheet":
                source = truth["spreadsheet_source"]
                init = [source["A"], source["B"], source["initial_total"]]
                if case["initial"] != {"A": source["A"], "B": source["B"]}:
                    errors.append(case["id"] + ":PUBLIC_SOURCE_MISMATCH")
                expected = _expected_sheet(case, route, truth)
                art = row.get("artifact", {})
                initial_art = row.get("initial_artifact", {})
                if row.get("initial_visible") != init:
                    errors.append(case["id"] + ":INITIAL_PARITY:" + route)
                initial_formula = source["followup_formula"] if route == "structured" else None
                if initial_art.get("formula") != initial_formula or [initial_art.get("A"), initial_art.get("B"), initial_art.get("total")] != init:
                    errors.append(case["id"] + ":INITIAL_STRUCTURE:" + route)
                if any(art.get(k) != v for k, v in expected.items()):
                    errors.append(case["id"] + ":SHEET_SEMANTICS:" + route)
                if case["followup"]["kind"] == "install_formula" and case["followup"]["formula"] != source["followup_formula"]:
                    errors.append(case["id"] + ":REQUEST_FORMULA_MISMATCH")
                expected_styles = {case["followup"]["cell"]: case["followup"]["style"]} if case["followup"]["kind"] == "style_only" else {}
                if art.get("styles", {}) != expected_styles:
                    errors.append(case["id"] + ":STYLE_EFFECT:" + route)
                if route == "flat" and case["followup"]["kind"] != "install_formula" and art.get("formula") is not None:
                    errors.append(case["id"] + ":FLAT_HIDDEN_STRUCTURE:" + route)
                if row.get("final_visible") != [expected["A"], expected["B"], expected["total"]]:
                    errors.append(case["id"] + ":FINAL_EFFECT:" + route)
            else:
                initial, outcome, final = _expected_draw(case, route, truth["drawing_layers"], truth["canvas"])
                art = row.get("artifact", {})
                initial_art = row.get("initial_artifact", {})
                visible_initial = initial_art.get("pixels") if route == "raster" else _render_oracle(initial_art.get("objects", []), truth["canvas"])
                visible_final = art.get("pixels") if route == "raster" else _render_oracle(art.get("objects", []), truth["canvas"])
                if row.get("initial_visible") != initial or visible_initial != initial:
                    errors.append(case["id"] + ":INITIAL_RENDER_PARITY:" + route)
                if row.get("outcome") != outcome or row.get("final_visible") != final or (outcome == "COMPLETED" and visible_final != final):
                    errors.append(case["id"] + ":FOLLOWUP_EFFECT:" + route)
                if route == "raster" and any(any(k in item for k in ("objects", "underlay", "layers")) for item in (initial_art, art)):
                    errors.append(case["id"] + ":RASTER_RETAINS_HIDDEN_STRUCTURE")
                if route == "native" and not {"red_underlay", "blue_front", "green_marker"}.issubset({o.get("id") for o in art.get("objects", [])}):
                    errors.append(case["id"] + ":NATIVE_STRUCTURE_MISSING")
    # Costs are an exogenous declared scenario, not read from candidate output.
    mix_results = {}
    for mix_name, probabilities in costs["mixtures"].items():
        totals = {}
        family = "drawing" if mix_name == "drawing_pixel_only" else "spreadsheet"
        routes = ("raster", "native") if family == "drawing" else ("flat", "structured")
        if abs(sum(probabilities.values()) - 1.0) > 1e-12 or any(p < 0 for p in probabilities.values()):
            errors.append(mix_name + ":INVALID_WEIGHTS")
        for route in routes:
            initial_cost = costs[family][route]["initial"]
            total = initial_cost
            for kind, probability in probabilities.items():
                unit = costs[family][route][kind]
                if probability > 0 and unit is None:
                    total = None
                    break
                if probability > 0:
                    total += probability * unit
            totals[route] = total
        mix_results[mix_name] = totals
    if mix_results.get("spreadsheet_low_change", {}).get("flat", 0) >= mix_results.get("spreadsheet_low_change", {}).get("structured", 0):
        errors.append("LOW_MIX_RANKING")
    if mix_results.get("spreadsheet_structure_heavy", {}).get("flat", 0) <= mix_results.get("spreadsheet_structure_heavy", {}).get("structured", 0):
        errors.append("STRUCTURE_HEAVY_RANKING")
    if mix_results.get("drawing_pixel_only", {}).get("raster") is None or mix_results.get("drawing_pixel_only", {}).get("raster", 0) >= mix_results.get("drawing_pixel_only", {}).get("native", 0):
        errors.append("DRAWING_PIXEL_ONLY_RANKING")
    return {"status": "METHOD_PASS_SCOPED" if not errors else "FAIL_AUDIT", "rows": len(got), "errors": errors, "abstract_cost_sensitivity_only": mix_results}
