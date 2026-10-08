#!/usr/bin/env python3
"""Independent exact-state enumerator and candidate-output auditor for #6684."""
from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path


def _values(pair: list[int]) -> range:
    if not isinstance(pair, list) or len(pair) != 2 or type(pair[0]) is not int or type(pair[1]) is not int or pair[0] > pair[1]:
        raise ValueError("invalid_interval")
    return range(pair[0], pair[1] + 1)


def _worlds(case: dict, design: dict):
    target, action, forbidden = case["target"], case["action"], case["forbidden"]
    objects = (target, action, forbidden)
    shift_names = list(dict.fromkeys(obj["shift_var"] for obj in objects))
    shift_domains = [list(itertools.product(_values(design["shift_variables"][name]["x"]),
                                           _values(design["shift_variables"][name]["y"])))
                     for name in shift_names]
    error_domains = [list(itertools.product(_values(obj["error"][0]), _values(obj["error"][1])))
                     for obj in objects]
    for scale, shifts, errors in itertools.product(case["scale_values"],
                                                   itertools.product(*shift_domains),
                                                   itertools.product(*error_domains)):
        shift_for = dict(zip(shift_names, shifts))
        bases = (target["base"],
                 [target["base"][i] + action["offset"][i] for i in range(2)],
                 [target["base"][i] + forbidden["offset_from_target"][i] for i in range(2)])
        points = []
        for obj, base, error in zip(objects, bases, errors):
            shift = shift_for[obj["shift_var"]]
            points.append(tuple(scale * base[i] + shift[i] + error[i] for i in range(2)))
        yield points[0], points[1], points[2]


def _inside(point: tuple[int, int], center: tuple[int, int], half: list[int]) -> bool:
    return all(abs(point[i] - center[i]) <= half[i] for i in range(2))


def _zone_admits(row: dict, case: dict, policy: str) -> bool:
    bounds = row[policy]
    hit, collateral = bounds["action_minus_target"], bounds["action_minus_forbidden"]
    target_half = case["target"]["half_size"]
    forbidden_half = case["forbidden"]["half_size"]
    hit_safe = all(hit[i][0] >= -target_half[i] and hit[i][1] <= target_half[i] for i in range(2))
    separated = any(collateral[i][1] < -forbidden_half[i] or collateral[i][0] > forbidden_half[i]
                    for i in range(2))
    return hit_safe and separated


def reconstruct(case: dict, design: dict) -> dict:
    target, action, forbidden = case["target"], case["action"], case["forbidden"]
    world_count = 0
    safe_count = 0
    first_unsafe = None
    hit_lo, hit_hi = [None, None], [None, None]
    collateral_lo, collateral_hi = [None, None], [None, None]
    for target_point, action_point, forbidden_point in _worlds(case, design):
        world_count += 1
        hit_delta = [action_point[i] - target_point[i] for i in range(2)]
        collateral_delta = [action_point[i] - forbidden_point[i] for i in range(2)]
        for i in range(2):
            hit_lo[i] = hit_delta[i] if hit_lo[i] is None else min(hit_lo[i], hit_delta[i])
            hit_hi[i] = hit_delta[i] if hit_hi[i] is None else max(hit_hi[i], hit_delta[i])
            collateral_lo[i] = collateral_delta[i] if collateral_lo[i] is None else min(collateral_lo[i], collateral_delta[i])
            collateral_hi[i] = collateral_delta[i] if collateral_hi[i] is None else max(collateral_hi[i], collateral_delta[i])
        hit = _inside(action_point, target_point, target["half_size"])
        clear = not _inside(action_point, forbidden_point, forbidden["half_size"])
        safe = hit and clear
        safe_count += int(safe)
        if not safe and first_unsafe is None:
            first_unsafe = {"target": target_point, "action": action_point,
                            "forbidden": forbidden_point, "hit": hit, "clear": clear}
    return {"world_count": world_count, "safe_world_count": safe_count,
            "exactly_safe": safe_count == world_count, "first_unsafe": first_unsafe,
            "exact_action_minus_target": [[hit_lo[i], hit_hi[i]] for i in range(2)],
            "exact_action_minus_forbidden": [[collateral_lo[i], collateral_hi[i]] for i in range(2)]}


def audit(design: dict, candidate: dict) -> dict:
    errors: list[str] = []
    expected = {case["case_id"]: case for case in design["cases"]}
    received = {row.get("case_id"): row for row in candidate.get("rows", [])}
    if candidate.get("schema") != "relational-coordinate-bounds-6684-candidate-v1":
        errors.append("candidate_schema_mismatch")
    if set(received) != set(expected):
        errors.append("case_set_mismatch")
    audited_rows = []
    for case_id, case in expected.items():
        row = received.get(case_id)
        if row is None:
            continue
        exact = reconstruct(case, design)
        valid = row.get("valid") is True
        if not valid:
            errors.append(f"valid_frozen_case_rejected:{case_id}")
            continue
        if row.get("family") != case["family"]:
            errors.append(f"family_mismatch:{case_id}")
        for policy in ("BOX", "RELATIONAL"):
            result = row.get(policy, {})
            decision = result.get("decision")
            if decision not in ("ADMIT", "UNKNOWN_REOBSERVE"):
                errors.append(f"invalid_decision:{case_id}:{policy}")
                continue
            for relation, exact_key in (("action_minus_target", "exact_action_minus_target"),
                                        ("action_minus_forbidden", "exact_action_minus_forbidden")):
                bounds = result.get(relation)
                if not isinstance(bounds, list) or len(bounds) != 2:
                    errors.append(f"missing_bounds:{case_id}:{policy}:{relation}")
                    continue
                exact_bounds = exact[exact_key]
                if any(bounds[i][0] > exact_bounds[i][0] or bounds[i][1] < exact_bounds[i][1]
                       for i in range(2)):
                    errors.append(f"under_approximation:{case_id}:{policy}:{relation}")
            guaranteed = _zone_admits(row, case, policy)
            if decision == "ADMIT" and (not guaranteed or not exact["exactly_safe"]):
                errors.append(f"false_admit:{case_id}:{policy}")
            if decision == "UNKNOWN_REOBSERVE" and guaranteed:
                errors.append(f"decision_disagrees_with_zone:{case_id}:{policy}")
        audited_rows.append({"case_id": case_id, "family": case["family"], **exact,
                             "BOX": row["BOX"]["decision"],
                             "RELATIONAL": row["RELATIONAL"]["decision"]})

    common_safe = [r for r in audited_rows if r["family"] == "common_mode" and r["exactly_safe"]]
    independent = [r for r in audited_rows if r["family"] == "independent_error"]
    box_false_unknown = sum(r["BOX"] != "ADMIT" for r in common_safe)
    relational_false_unknown = sum(r["RELATIONAL"] != "ADMIT" for r in common_safe)
    independent_differences = [r["case_id"] for r in independent if r["BOX"] != r["RELATIONAL"]]
    false_admissions = sum(r[policy] == "ADMIT" and not r["exactly_safe"]
                           for r in audited_rows for policy in ("BOX", "RELATIONAL"))
    disposition = "PASS_METHOD_SCOPED"
    if errors or false_admissions:
        disposition = "FAIL_UNSOUND"
    elif relational_false_unknown >= box_false_unknown or independent_differences:
        disposition = "FAIL_NO_GAIN"
    return {"schema": "relational-coordinate-bounds-6684-audit-v1",
            "disposition": disposition, "errors": errors, "rows": audited_rows,
            "summary": {"case_count": len(audited_rows),
                        "concrete_worlds": sum(r["world_count"] for r in audited_rows),
                        "false_admissions": false_admissions,
                        "common_mode_exact_safe_cases": len(common_safe),
                        "common_mode_BOX_false_unknown": box_false_unknown,
                        "common_mode_RELATIONAL_false_unknown": relational_false_unknown,
                        "independent_error_case_count": len(independent),
                        "independent_error_decision_differences": independent_differences}}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--design", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    design = json.loads(Path(args.design).read_text())
    candidate = json.loads(Path(args.candidate).read_text())
    result = audit(design, candidate)
    output = Path(args.out)
    output.mkdir(parents=True, exist_ok=True)
    (output / "audit.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"disposition": result["disposition"], "errors": len(result["errors"]),
                      "cases": result["summary"]["case_count"],
                      "worlds": result["summary"]["concrete_worlds"]}))
    return 0 if result["disposition"] == "PASS_METHOD_SCOPED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
