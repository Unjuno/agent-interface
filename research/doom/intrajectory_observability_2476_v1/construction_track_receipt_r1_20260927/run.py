from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
import time
from pathlib import Path


MIN_SCORE = 0.80
MIN_MARGIN = 0.08
MAX_AGE_NS = 250_000_000
MAX_FRAME_GAP = 2
MAX_STEP_PX = 8
GEOMETRY = (640, 480)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def merged(base: dict, override: dict | None) -> dict:
    result = dict(base)
    if override:
        result.update(override)
    return result


def score_gate(score: object, margin: object) -> bool:
    return (
        isinstance(score, (int, float)) and not isinstance(score, bool)
        and isinstance(margin, (int, float)) and not isinstance(margin, bool)
        and score >= MIN_SCORE and margin >= MIN_MARGIN
    )


def assess(anchor: dict, receipt: dict, observation: dict) -> tuple[bool, str, list[int] | None]:
    if receipt.get("schema") != "track-receipt-v1":
        return False, "INVALID_RECEIPT_SCHEMA", None
    if not score_gate(anchor.get("score"), anchor.get("margin")):
        return False, "ANCHOR_NOT_ACCEPTED", None
    if (anchor.get("width"), anchor.get("height")) != GEOMETRY:
        return False, "ANCHOR_GEOMETRY", None
    if observation.get("status") != "FOUND":
        return False, "OBSERVATION_NOT_FOUND", None
    if not score_gate(observation.get("score"), observation.get("margin")):
        return False, "CURRENT_MATCH_GATE", None
    digest = observation.get("frame_sha256")
    if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        return False, "CURRENT_FRAME_DIGEST", None
    if (observation.get("width"), observation.get("height")) != GEOMETRY:
        return False, "CURRENT_GEOMETRY", None
    if (observation.get("width"), observation.get("height")) != (anchor.get("width"), anchor.get("height")):
        return False, "GEOMETRY_CHANGED", None
    seq_delta = observation.get("frame_seq", -1) - anchor.get("frame_seq", -1)
    if not isinstance(seq_delta, int) or isinstance(seq_delta, bool) or not 1 <= seq_delta <= MAX_FRAME_GAP:
        return False, "FRAME_SEQUENCE", None
    age = observation.get("captured_ns", -1) - anchor.get("captured_ns", -1)
    if not isinstance(age, int) or isinstance(age, bool) or not 0 <= age <= MAX_AGE_NS:
        return False, "OBSERVATION_AGE", None

    dx, dy = receipt.get("predicted_dx_px"), receipt.get("predicted_dy_px")
    direction = receipt.get("correction_direction")
    if not all(isinstance(v, int) and not isinstance(v, bool) for v in (dx, dy)):
        return False, "DISPLACEMENT_TYPE", None
    if abs(dx) > MAX_STEP_PX or abs(dy) > MAX_STEP_PX:
        return False, "DISPLACEMENT_BOUND", None
    direction_ok = {
        "RIGHT": dx > 0 and dy == 0,
        "LEFT": dx < 0 and dy == 0,
        "DOWN": dy > 0 and dx == 0,
        "UP": dy < 0 and dx == 0,
    }.get(direction, False)
    if not direction_ok:
        return False, "DIRECTION_MISMATCH", None
    predicted = [anchor["center_x_px"] + dx, anchor["center_y_px"] + dy]
    observed = [observation.get("center_x_px"), observation.get("center_y_px")]
    if not all(isinstance(v, int) and not isinstance(v, bool) for v in observed):
        return False, "CURRENT_CENTER", predicted
    if any(abs(a - b) > MAX_STEP_PX for a, b in zip(predicted, observed)):
        return False, "CORRIDOR_MISS", predicted
    return True, "TRACK_CURRENT_MATCH", predicted


def authority_matches(authority: dict | None, observation: dict) -> bool:
    if not isinstance(authority, dict) or authority.get("scope") != "corrective_input":
        return False
    captured = observation.get("captured_ns")
    return (
        authority.get("frame_seq") == observation.get("frame_seq")
        and authority.get("frame_sha256") == observation.get("frame_sha256")
        and isinstance(captured, int) and not isinstance(captured, bool)
        and isinstance(authority.get("not_before_ns"), int)
        and isinstance(authority.get("expires_ns"), int)
        and authority["not_before_ns"] <= captured <= authority["expires_ns"]
    )


def build_cases(data: dict) -> list[dict]:
    rows = []
    for spec in data["cases"]:
        row = {
            "id": spec["id"],
            "anchor": dict(data["anchor"]),
            "receipt": dict(data["receipt"]),
            "observation": dict(data["observation"]),
            "authority": dict(data["authority"]) if data["authority"] is not None else None,
            "fallback": None,
        }
        for key in ("anchor", "receipt", "observation", "authority", "fallback"):
            if key not in spec:
                continue
            patch = spec[key]
            if key in ("authority", "fallback"):
                row[key] = None if patch is None else merged(row[key] or {}, patch)
            else:
                row[key] = merged(row[key], patch)
        rows.append(row)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    source, out = args.source.resolve(), args.out.resolve()
    freeze = json.loads((source / "FREEZE.json").read_text())
    for name, expected in freeze["sha256"].items():
        actual = sha256(source / name)
        if actual != expected:
            raise SystemExit(f"FREEZE_MISMATCH:{name}:{actual}")
    input_path = source / "cases.json"
    inputs = json.loads(input_path.read_text())
    rows = []
    started = time.monotonic_ns()
    for case in build_cases(inputs):
        valid, reason, predicted = assess(case["anchor"], case["receipt"], case["observation"])
        authority = authority_matches(case["authority"], case["observation"])
        rows.append({
            "case_id": case["id"],
            "track_valid": valid,
            "reason": reason,
            "predicted_center_px": predicted,
            "authority_matches_current_frame": authority,
            "action_candidate_admitted": valid and authority,
            "fallback_observed": case["fallback"],
            "physical_input_emitted": False,
        })
    result = {
        "schema": "track-receipt-construction-trace-v1",
        "allocation": freeze["allocation"],
        "source_sha256": freeze["sha256"],
        "input_sha256": sha256(input_path),
        "python": sys.version,
        "platform": platform.platform(),
        "started_monotonic_ns": started,
        "finished_monotonic_ns": time.monotonic_ns(),
        "rows": rows,
        "physical_input_emissions": 0,
    }
    out.mkdir(parents=True, exist_ok=True)
    with (out / "trace.json").open("x", encoding="utf-8") as f:
        json.dump(result, f, indent=2, sort_keys=True, allow_nan=False)
        f.write("\n")
    print(json.dumps({"allocation": freeze["allocation"], "rows": len(rows), "trace_sha256": sha256(out / "trace.json")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

