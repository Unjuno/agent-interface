from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


SCORE = 0.80
MARGIN = 0.08
AGE_NS = 250_000_000
FRAME_GAP = 2
STEP = 8
SIZE = (640, 480)
EXPECTED = {
    "valid_current_track_and_authority": (True, "TRACK_CURRENT_MATCH", True),
    "valid_track_receipt_without_authority": (True, "TRACK_CURRENT_MATCH", False),
    "stale_authority_frame": (True, "TRACK_CURRENT_MATCH", False),
    "score_just_below_gate": (False, "CURRENT_MATCH_GATE", False),
    "margin_just_below_gate": (False, "CURRENT_MATCH_GATE", False),
    "age_just_over_limit": (False, "OBSERVATION_AGE", False),
    "frame_gap_over_limit": (False, "FRAME_SEQUENCE", False),
    "geometry_changed": (False, "CURRENT_GEOMETRY", False),
    "target_missing": (False, "OBSERVATION_NOT_FOUND", False),
    "abrupt_translation_despite_strong_global_fallback": (False, "CORRIDOR_MISS", False),
    "correction_direction_disagrees_with_delta": (False, "DIRECTION_MISMATCH", False),
    "exact_inclusive_score_margin_corridor_age_boundaries": (True, "TRACK_CURRENT_MATCH", True),
    "authority_digest_does_not_bind_current_frame": (True, "TRACK_CURRENT_MATCH", False),
    "authority_expired_at_observation": (True, "TRACK_CURRENT_MATCH", False),
    "future_dated_observation": (False, "OBSERVATION_AGE", False),
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def merge(left: dict, right: dict | None) -> dict:
    copy = dict(left)
    if right:
        copy.update(right)
    return copy


def fixtures(spec: dict) -> list[dict]:
    result = []
    for item in spec["cases"]:
        current = {
            "id": item["id"], "anchor": dict(spec["anchor"]),
            "receipt": dict(spec["receipt"]), "observation": dict(spec["observation"]),
            "authority": dict(spec["authority"]) if spec["authority"] is not None else None,
            "fallback": None,
        }
        for field in ("anchor", "receipt", "observation", "authority", "fallback"):
            if field not in item:
                continue
            replacement = item[field]
            if field in ("authority", "fallback"):
                current[field] = None if replacement is None else merge(current[field] or {}, replacement)
            else:
                current[field] = merge(current[field], replacement)
        result.append(current)
    return result


def recompute(row: dict) -> tuple[bool, str, bool]:
    a, r, o = row["anchor"], row["receipt"], row["observation"]
    if r.get("schema") != "track-receipt-v1":
        return False, "INVALID_RECEIPT_SCHEMA", False
    if not isinstance(a.get("score"), (int, float)) or a["score"] < SCORE or not isinstance(a.get("margin"), (int, float)) or a["margin"] < MARGIN:
        return False, "ANCHOR_NOT_ACCEPTED", False
    if (a.get("width"), a.get("height")) != SIZE:
        return False, "ANCHOR_GEOMETRY", False
    if o.get("status") != "FOUND":
        return False, "OBSERVATION_NOT_FOUND", False
    if not isinstance(o.get("score"), (int, float)) or o["score"] < SCORE or not isinstance(o.get("margin"), (int, float)) or o["margin"] < MARGIN:
        return False, "CURRENT_MATCH_GATE", False
    h = o.get("frame_sha256")
    if not isinstance(h, str) or len(h) != 64 or set(h) - set("0123456789abcdef"):
        return False, "CURRENT_FRAME_DIGEST", False
    if (o.get("width"), o.get("height")) != SIZE:
        return False, "CURRENT_GEOMETRY", False
    if (o.get("width"), o.get("height")) != (a.get("width"), a.get("height")):
        return False, "GEOMETRY_CHANGED", False
    gap = o.get("frame_seq", -1) - a.get("frame_seq", -1)
    if not isinstance(gap, int) or isinstance(gap, bool) or gap < 1 or gap > FRAME_GAP:
        return False, "FRAME_SEQUENCE", False
    age = o.get("captured_ns", -1) - a.get("captured_ns", -1)
    if not isinstance(age, int) or isinstance(age, bool) or age < 0 or age > AGE_NS:
        return False, "OBSERVATION_AGE", False
    dx, dy, direction = r.get("predicted_dx_px"), r.get("predicted_dy_px"), r.get("correction_direction")
    if not isinstance(dx, int) or isinstance(dx, bool) or not isinstance(dy, int) or isinstance(dy, bool):
        return False, "DISPLACEMENT_TYPE", False
    if abs(dx) > STEP or abs(dy) > STEP:
        return False, "DISPLACEMENT_BOUND", False
    allowed = ((direction == "RIGHT" and dx > 0 and dy == 0)
               or (direction == "LEFT" and dx < 0 and dy == 0)
               or (direction == "DOWN" and dy > 0 and dx == 0)
               or (direction == "UP" and dy < 0 and dx == 0))
    if not allowed:
        return False, "DIRECTION_MISMATCH", False
    px, py = a["center_x_px"] + dx, a["center_y_px"] + dy
    x, y = o.get("center_x_px"), o.get("center_y_px")
    if not isinstance(x, int) or isinstance(x, bool) or not isinstance(y, int) or isinstance(y, bool):
        return False, "CURRENT_CENTER", False
    if abs(px - x) > STEP or abs(py - y) > STEP:
        return False, "CORRIDOR_MISS", False
    authority = row.get("authority")
    lease_ok = (
        isinstance(authority, dict)
        and authority.get("scope") == "corrective_input"
        and authority.get("frame_seq") == o.get("frame_seq")
        and authority.get("frame_sha256") == o.get("frame_sha256")
        and isinstance(authority.get("not_before_ns"), int)
        and isinstance(authority.get("expires_ns"), int)
        and authority["not_before_ns"] <= o["captured_ns"] <= authority["expires_ns"]
    )
    return True, "TRACK_CURRENT_MATCH", bool(lease_ok)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--source", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    args = p.parse_args()
    source, out = args.source.resolve(), args.out.resolve()
    freeze = json.loads((source / "FREEZE.json").read_text())
    errors = []
    for name, expected_hash in freeze["sha256"].items():
        if digest(source / name) != expected_hash:
            errors.append("SOURCE_HASH:" + name)
    inputs_path = source / "cases.json"
    inputs = json.loads(inputs_path.read_text())
    trace_path = out / "trace.json"
    trace = json.loads(trace_path.read_text())
    if trace.get("schema") != "track-receipt-construction-trace-v1":
        errors.append("TRACE_SCHEMA")
    if trace.get("allocation") != freeze.get("allocation"):
        errors.append("ALLOCATION_BINDING")
    if trace.get("source_sha256") != freeze.get("sha256"):
        errors.append("TRACE_SOURCE_BINDING")
    if trace.get("input_sha256") != digest(inputs_path):
        errors.append("INPUT_BINDING")
    expected_rows = fixtures(inputs)
    actual_rows = trace.get("rows", [])
    if len(actual_rows) != len(expected_rows):
        errors.append("ROW_COUNT")
    indexed = {row.get("case_id"): row for row in actual_rows}
    if len(indexed) != len(actual_rows):
        errors.append("DUPLICATE_CASE_ID")
    for fixture in expected_rows:
        cid = fixture["id"]
        got = indexed.get(cid)
        if got is None:
            errors.append("MISSING:" + cid)
            continue
        should_track, should_reason, should_action = recompute(fixture)
        stated = EXPECTED.get(cid)
        if stated != (should_track, should_reason, should_action):
            errors.append("ORACLE_DISAGREEMENT:" + cid)
        if (got.get("track_valid"), got.get("reason"), got.get("action_candidate_admitted")) != (should_track, should_reason, should_action):
            errors.append("DECISION_MISMATCH:" + cid)
        if got.get("physical_input_emitted") is not False:
            errors.append("PHYSICAL_INPUT:" + cid)
        if got.get("fallback_observed") != fixture.get("fallback"):
            errors.append("FALLBACK_BINDING:" + cid)
    if trace.get("physical_input_emissions") != 0:
        errors.append("NONZERO_PHYSICAL_INPUT_COUNT")
    expected_action_ids = {"valid_current_track_and_authority", "exact_inclusive_score_margin_corridor_age_boundaries"}
    actual_action_ids = {k for k, v in indexed.items() if v.get("action_candidate_admitted") is True}
    if actual_action_ids != expected_action_ids:
        errors.append("ACTION_CANDIDATE_SET")
    result = {
        "schema": "track-receipt-construction-audit-v1",
        "allocation": freeze["allocation"],
        "rows_audited": len(actual_rows),
        "action_candidates_admitted": len(actual_action_ids),
        "physical_input_emissions": trace.get("physical_input_emissions"),
        "decision": "PASS_TRACK_RECEIPT_BOUNDARY_CONSTRUCTION_ONLY" if not errors else "FAIL_CONSTRUCTION_GATE",
        "errors": errors,
    }
    with (out / "audit.json").open("x", encoding="utf-8") as f:
        json.dump(result, f, indent=2, sort_keys=True, allow_nan=False)
        f.write("\n")
    print(json.dumps(result, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())

