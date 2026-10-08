#!/usr/bin/env python3
"""Candidate BOX and shared-variable relative bounds for Issue #6684 T0."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def _ints(pair: list[int]) -> range:
    if (not isinstance(pair, list) or len(pair) != 2 or
            any(type(v) is not int for v in pair) or pair[0] > pair[1]):
        raise ValueError("invalid_integer_interval")
    return range(pair[0], pair[1] + 1)


def _point_interval(case: dict, design: dict, obj: dict, base: list[int]) -> list[list[int]]:
    shift = design["shift_variables"][obj["shift_var"]]
    result = []
    for axis in range(2):
        values = [scale * (base[axis] + error) + offset
                  for scale in case["scale_values"]
                  for error in _ints(obj["error"][axis])
                  for offset in _ints(shift["xy"[axis]])]
        result.append([min(values), max(values)])
    return result


def _difference(left: list[list[int]], right: list[list[int]]) -> list[list[int]]:
    return [[left[i][0] - right[i][1], left[i][1] - right[i][0]] for i in range(2)]


def _relational_difference(case: dict, design: dict, left: dict, left_base: list[int],
                           right: dict, right_base: list[int]) -> list[list[int]]:
    left_shift = design["shift_variables"][left["shift_var"]]
    right_shift = design["shift_variables"][right["shift_var"]]
    result = []
    for axis, name in enumerate("xy"):
        if left["shift_var"] == right["shift_var"]:
            shift_deltas = [0]
        else:
            shift_deltas = [a - b for a in _ints(left_shift[name])
                            for b in _ints(right_shift[name])]
        values = [scale * (left_base[axis] - right_base[axis]) + left_error - right_error + shift_delta
                  for scale in case["scale_values"]
                  for left_error in _ints(left["error"][axis])
                  for right_error in _ints(right["error"][axis])
                  for shift_delta in shift_deltas]
        result.append([min(values), max(values)])
    return result


def _safe(interval: list[list[int]], half_size: list[int]) -> bool:
    return all(interval[i][0] >= -half_size[i] and interval[i][1] <= half_size[i]
               for i in range(2))


def _avoids(interval: list[list[int]], half_size: list[int]) -> bool:
    return any(interval[i][1] < -half_size[i] or interval[i][0] > half_size[i]
               for i in range(2))


def evaluate(case: dict, design: dict) -> dict:
    case_id = case.get("case_id", "<missing>")
    try:
        if design.get("coordinate_unit") != "px":
            raise ValueError("unsupported_design_unit")
        if not case["scale_values"] or any(type(s) is not int or s <= 0 for s in case["scale_values"]):
            raise ValueError("invalid_scale_domain")
        target, action, forbidden = case["target"], case["action"], case["forbidden"]
        for obj in (target, action, forbidden):
            if obj["frame_id"] != design["source_frame_id"]:
                raise ValueError("frame_id_mismatch")
            if obj["epoch"] != design["current_epoch"]:
                raise ValueError("stale_or_mixed_epoch")
            if obj["shift_var"] not in design["shift_variables"]:
                raise ValueError("unknown_shift_variable")
            for pair in obj["error"]:
                _ints(pair)
        if action["target_id"] != target["id"]:
            raise ValueError("target_identity_mismatch")
        if forbidden["id"] == target["id"]:
            raise ValueError("forbidden_identity_alias")
        target_base = target["base"]
        action_base = [target_base[i] + action["offset"][i] for i in range(2)]
        forbidden_base = [target_base[i] + forbidden["offset_from_target"][i] for i in range(2)]
        target_box = _point_interval(case, design, target, target_base)
        action_box = _point_interval(case, design, action, action_base)
        forbidden_box = _point_interval(case, design, forbidden, forbidden_base)
        box_hit = _difference(action_box, target_box)
        box_forbidden = _difference(action_box, forbidden_box)
        rel_hit = _relational_difference(case, design, action, action_base, target, target_base)
        rel_forbidden = _relational_difference(case, design, action, action_base,
                                               forbidden, forbidden_base)
        box_admit = _safe(box_hit, target["half_size"]) and _avoids(box_forbidden, forbidden["half_size"])
        rel_admit = _safe(rel_hit, target["half_size"]) and _avoids(rel_forbidden, forbidden["half_size"])
        return {
            "case_id": case_id,
            "family": case["family"],
            "valid": True,
            "BOX": {"decision": "ADMIT" if box_admit else "UNKNOWN_REOBSERVE",
                    "action_minus_target": box_hit, "action_minus_forbidden": box_forbidden},
            "RELATIONAL": {"decision": "ADMIT" if rel_admit else "UNKNOWN_REOBSERVE",
                           "action_minus_target": rel_hit, "action_minus_forbidden": rel_forbidden},
        }
    except (KeyError, TypeError, ValueError, IndexError) as exc:
        reason = str(exc) or type(exc).__name__
        return {"case_id": case_id, "family": case.get("family", "invalid"), "valid": False,
                "BOX": {"decision": "UNKNOWN_REOBSERVE", "reason": reason},
                "RELATIONAL": {"decision": "UNKNOWN_REOBSERVE", "reason": reason}}


def run(design: dict) -> dict:
    return {"schema": "relational-coordinate-bounds-6684-candidate-v1",
            "rows": [evaluate(case, design) for case in design["cases"]]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--design", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    design = json.loads(Path(args.design).read_text())
    result = run(design)
    output = Path(args.out)
    output.mkdir(parents=True, exist_ok=True)
    (output / "candidate.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"schema": result["schema"], "rows": len(result["rows"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
