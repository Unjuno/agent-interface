#!/usr/bin/env python3
"""Independent raw-event auditor for the Issue #6581 T0b fixture."""
import argparse
import hashlib
import json
import math
from pathlib import Path


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _cross(a, b, p):
    return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])


def _line_polygon_interval(start, finish, polygon):
    """Clip a segment against all half-planes of one convex polygon."""
    signed_area = sum(
        polygon[i][0] * polygon[(i + 1) % len(polygon)][1]
        - polygon[(i + 1) % len(polygon)][0] * polygon[i][1]
        for i in range(len(polygon))
    )
    orientation = 1.0 if signed_area >= 0 else -1.0
    lower, upper = 0.0, 1.0
    for index, vertex in enumerate(polygon):
        following = polygon[(index + 1) % len(polygon)]
        at_start = orientation * _cross(vertex, following, start)
        at_finish = orientation * _cross(vertex, following, finish)
        slope = at_finish - at_start
        if abs(slope) <= 1e-13:
            if at_start < -1e-8:
                return None
            continue
        crossing = (-1e-8 - at_start) / slope
        if slope > 0:
            lower = max(lower, crossing)
        else:
            upper = min(upper, crossing)
        if lower > upper + 1e-8:
            return None
    lower, upper = max(0.0, lower), min(1.0, upper)
    return (lower, upper) if lower <= upper + 1e-8 else None


def _first_gap(start, finish, polygons):
    """Return first parameter outside a polygon-union corridor, or None."""
    if polygons is None:
        return None
    intervals = sorted(
        interval
        for polygon in polygons
        if (interval := _line_polygon_interval(start, finish, polygon)) is not None
    )
    covered_until = 0.0
    for lower, upper in intervals:
        if lower > covered_until + 1e-7:
            return covered_until
        covered_until = max(covered_until, upper)
        if covered_until >= 1.0 - 1e-7:
            return None
    return covered_until if covered_until < 1.0 - 1e-7 else None


def _distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def audit_payload(raw, spec, spec_bytes, expected_spec_sha256, expected_freeze_sha256=None,
                  expected_html_sha256=None, expected_image_ref=None):
    errors = []
    if raw.get("schema") != "path-width-gui-raw-v1":
        errors.append("wrong raw schema")
    if raw.get("allocation_id") != "PATH-WIDTH-CONTINUOUS-GUI-6581-T0B-20261002-01":
        errors.append("wrong allocation identity")
    if raw.get("run_role") != "formal":
        errors.append("raw run is not marked as the one formal allocation")
    if expected_freeze_sha256 is not None and raw.get("freeze_sha256") != expected_freeze_sha256:
        errors.append("freeze digest mismatch")
    if expected_html_sha256 is not None and raw.get("fixture_html_sha256") != expected_html_sha256:
        errors.append("fixture HTML digest mismatch")
    if expected_image_ref is not None and raw.get("runtime_image_ref") != expected_image_ref:
        errors.append("runtime image identity mismatch")
    actual_spec_hash = _sha(spec_bytes)
    if actual_spec_hash != expected_spec_sha256 or raw.get("fixture_spec_sha256") != expected_spec_sha256:
        errors.append("frozen fixture spec digest mismatch")

    declared = {row["id"]: row for row in spec.get("scenarios", [])}
    observed_rows = raw.get("scenarios")
    if not isinstance(observed_rows, list) or [x.get("scenario_id") for x in observed_rows] != list(declared):
        errors.append("scenario roster/order differs from frozen spec")
        observed_rows = observed_rows if isinstance(observed_rows, list) else []

    reconstructed = {}
    tolerance = float(spec["endpoint_tolerance"])
    for result in observed_rows:
        sid = result.get("scenario_id")
        scenario = declared.get(sid)
        if scenario is None:
            errors.append(f"unexpected scenario {sid!r}")
            continue
        events = result.get("raw_events")
        if not isinstance(events, list) or len(events) != len(scenario["trace"]) + 1:
            errors.append(f"{sid}: event count does not match frozen gesture")
            continue
        expected_types = ["down"] + ["move"] * (len(scenario["trace"]) - 1) + ["up"]
        if [event.get("type") for event in events] != expected_types:
            errors.append(f"{sid}: pointer event order/type changed")
        if [event.get("seq") for event in events] != list(range(len(events))):
            errors.append(f"{sid}: pointer sequence numbers are not contiguous")
        if any(event.get("trusted") is not True for event in events):
            errors.append(f"{sid}: non-browser-trusted pointer event")
        expected_points = scenario["trace"] + [scenario["trace"][-1]]
        for index, (event, expected) in enumerate(zip(events, expected_points)):
            try:
                actual = (float(event["x"]), float(event["y"]))
            except (KeyError, TypeError, ValueError):
                errors.append(f"{sid}: invalid coordinates at event {index}")
                continue
            if not all(math.isfinite(v) for v in actual) or _distance(actual, expected) > 1e-6:
                errors.append(f"{sid}: raw event {index} differs from frozen coordinate")

        first_exit = None
        if scenario["mode"] == "constrained":
            points = [(float(e["x"]), float(e["y"])) for e in events[:-1]]
            first = _first_gap(points[0], points[0], scenario["corridor_polygons"])
            if first is not None:
                first_exit = {"seq": 0, "t": 0.0}
            for index, (start, finish) in enumerate(zip(points, points[1:]), start=1):
                if first_exit is not None:
                    break
                gap = _first_gap(start, finish, scenario["corridor_polygons"])
                if gap is not None:
                    first_exit = {"seq": index, "t": gap}
            validity = "VALID" if first_exit is None else "INVALID"
        elif scenario["mode"] == "unconstrained" and scenario["corridor_polygons"] is None:
            validity = "NOT_APPLICABLE"
        else:
            errors.append(f"{sid}: invalid constraint mode/spec combination")
            validity = "UNKNOWN"

        last = events[-1]
        endpoint = scenario["trace"][-1]
        endpoint_hit = _distance((float(last["x"]), float(last["y"])), endpoint) <= tolerance
        saved = endpoint_hit and (validity in ("VALID", "NOT_APPLICABLE"))
        expected_receipt = {
            "endpoint_hit": endpoint_hit,
            "saved_effect": saved,
            "path_validity": validity,
            "first_exit": first_exit,
        }
        actual_receipt = result.get("app_receipt")
        if not isinstance(actual_receipt, dict):
            errors.append(f"{sid}: missing app receipt")
        else:
            for key in ("endpoint_hit", "saved_effect", "path_validity"):
                if actual_receipt.get(key) != expected_receipt[key]:
                    errors.append(f"{sid}: app receipt {key} disagrees with raw-event reconstruction")
            actual_exit = actual_receipt.get("first_exit")
            if actual_exit is None or first_exit is None:
                if actual_exit != first_exit:
                    errors.append(f"{sid}: app first-exit receipt disagrees")
            elif actual_exit.get("seq") != first_exit["seq"] or abs(float(actual_exit.get("t", -9)) - first_exit["t"]) > 1e-6:
                errors.append(f"{sid}: app first-exit receipt disagrees")
        reconstructed[sid] = expected_receipt

    by_id = {x.get("scenario_id"): x for x in observed_rows}
    wide = by_id.get("primary_wide", {}).get("raw_events")
    narrow = by_id.get("primary_narrow", {}).get("raw_events")
    primary_inputs_match = bool(wide and narrow and wide == narrow)
    primary_effects = (
        reconstructed.get("primary_wide", {}).get("saved_effect") is True
        and reconstructed.get("primary_narrow", {}).get("saved_effect") is False
        and reconstructed.get("primary_wide", {}).get("endpoint_hit") is True
        and reconstructed.get("primary_narrow", {}).get("endpoint_hit") is True
    )
    variable_control = reconstructed.get("variable_width", {}).get("path_validity") == "INVALID"
    corner_control = reconstructed.get("corner_control", {}).get("path_validity") == "VALID"
    endpoint_adversary = (
        reconstructed.get("endpoint_after_exit", {}).get("endpoint_hit") is True
        and reconstructed.get("endpoint_after_exit", {}).get("path_validity") == "INVALID"
        and reconstructed.get("endpoint_after_exit", {}).get("saved_effect") is False
    )
    no_corridor_control = (
        reconstructed.get("ordinary_drag_no_corridor", {}).get("path_validity") == "NOT_APPLICABLE"
        and reconstructed.get("ordinary_drag_no_corridor", {}).get("saved_effect") is True
    )
    if not primary_inputs_match:
        errors.append("primary wide/narrow event inputs are not byte-identical")
    if not primary_effects:
        errors.append("primary width contrast did not change constrained saved effect as frozen")
    if not variable_control:
        errors.append("variable-width control did not expose its narrowed segment")
    if not corner_control:
        errors.append("corner-following control was not accepted")
    if not endpoint_adversary:
        errors.append("endpoint-after-exit adversary was not rejected while endpoint was reached")
    if not no_corridor_control:
        errors.append("ordinary no-corridor control inferred path validity or lost endpoint effect")
    return {
        "schema": "path-width-independent-audit-v1",
        "allocation_id": raw.get("allocation_id"),
        "expected_spec_sha256": expected_spec_sha256,
        "rows_reconstructed": len(reconstructed),
        "scenario_receipts": reconstructed,
        "controls": {
            "primary_event_inputs_byte_identical": primary_inputs_match,
            "primary_width_effect_divergence": primary_effects,
            "variable_width": variable_control,
            "corner": corner_control,
            "endpoint_after_exit": endpoint_adversary,
            "no_corridor_not_applicable": no_corridor_control,
        },
        "errors": errors,
        "disposition": "PASS_METHOD_SCOPED" if not errors else "FAIL_AUDIT",
        "scope": "synthetic browser fixture and authored pointer events only; no human, agent, live application, timing, or safety claim",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--freeze", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raw_bytes = args.raw.read_bytes()
    spec_bytes = args.spec.read_bytes()
    freeze_bytes = args.freeze.read_bytes()
    freeze = json.loads(freeze_bytes)
    freeze_sha = _sha(freeze_bytes)
    declared_sources = freeze.get("source_sha256", {})
    for relative in ("spec.json", "fixture.html", "run.mjs", "package.json", "package-lock.json", "audit.py", "test_contract.py"):
        source_path = args.freeze.parent / relative
        if declared_sources.get(relative) != _sha(source_path.read_bytes()):
            raise SystemExit(f"frozen source hash mismatch: {relative}")
    audit = audit_payload(
        json.loads(raw_bytes), json.loads(spec_bytes), spec_bytes,
        freeze["source_sha256"]["spec.json"], freeze_sha,
        freeze["source_sha256"]["fixture.html"], freeze["container"]["playwright_image"],
    )
    args.output.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"disposition": audit["disposition"], "rows": audit["rows_reconstructed"], "errors": audit["errors"]}))
    return 0 if audit["disposition"] == "PASS_METHOD_SCOPED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
