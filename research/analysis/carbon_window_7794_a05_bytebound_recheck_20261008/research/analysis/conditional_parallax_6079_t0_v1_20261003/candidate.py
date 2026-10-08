"""Truth-blind pairwise observer for the #6079 synthetic raster fixture."""
from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path

TARGET = 240
LANDMARKS = frozenset((100, 101, 102))
MIN_SEPARATION_PX = 2.0


def parse_pgm(encoded: str) -> tuple[int, int, bytes]:
    data = base64.b64decode(encoded, validate=True)
    parts = data.split(b"\n", 3)
    if len(parts) != 4 or parts[0] != b"P5" or parts[3] == b"":
        raise ValueError("invalid frozen PGM")
    width, height = (int(v) for v in parts[1].split())
    if parts[2] != b"255" or len(parts[3]) != width * height:
        raise ValueError("invalid PGM dimensions/range")
    return width, height, parts[3]


def centroid_relative(encoded: str) -> tuple[float, float]:
    width, height, pixels = parse_pgm(encoded)
    target_points = []
    bg_points = []
    for index, value in enumerate(pixels):
        if value == TARGET:
            target_points.append((index % width, index // width))
        elif value in LANDMARKS:
            bg_points.append((index % width, index // width))
    if not target_points or not bg_points:
        raise ValueError("missing target or landmark pixels")
    tx = sum(p[0] for p in target_points) / len(target_points)
    ty = sum(p[1] for p in target_points) / len(target_points)
    bx = sum(p[0] for p in bg_points) / len(bg_points)
    by = sum(p[1] for p in bg_points) / len(bg_points)
    return tx - bx, ty - by


def classify(pair: dict) -> dict:
    members = pair["members"]
    if len(members) != 2:
        raise ValueError("expected exactly two paired members")
    left, right = members
    lf, rf = left["frames"], right["frames"]
    if len(lf) != len(rf) or [f["t_ms"] for f in lf] != [f["t_ms"] for f in rf]:
        raise ValueError("paired frame clocks differ")
    receipt = pair["probe_receipt"]
    if receipt.get("authority") != "none" or receipt.get("coordinate_frame") != "synthetic-world-x":
        raise ValueError("probe receipt outside frozen advisory contract")
    if receipt.get("event_t_ms") != 500:
        raise ValueError("unexpected probe event time")
    passive_equal = all(a["pgm_b64"] == b["pgm_b64"] for a, b in zip(lf[:5], rf[:5], strict=True))
    if not passive_equal:
        return {"pair_id": pair["pair_id"], "classification": "UNKNOWN", "reason": "passive_pair_mismatch", "max_relative_separation_px": None, "authority": False, "contact_claim": False}
    actual_dx = float(receipt.get("actual_dx", 0.0))
    if actual_dx == 0.0:
        return {"pair_id": pair["pair_id"], "classification": "UNKNOWN", "reason": "no_actual_probe_translation", "max_relative_separation_px": 0.0, "authority": False, "contact_claim": False}
    separation = 0.0
    for a, b in zip(lf[5:], rf[5:], strict=True):
        ax, ay = centroid_relative(a["pgm_b64"])
        bx, by = centroid_relative(b["pgm_b64"])
        separation = max(separation, ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5)
    result = "DISTINGUISHED_UNDER_RIGID_OVERLAY_ASSUMPTIONS" if separation >= MIN_SEPARATION_PX else "UNKNOWN"
    return {"pair_id": pair["pair_id"], "classification": result, "reason": "relative_motion_test", "max_relative_separation_px": round(separation, 6), "authority": False, "contact_claim": False}


def run(source: dict) -> dict:
    return {"schema": "conditional-parallax-candidate-v1", "results": [classify(p) for p in source["pairs"]]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    source = json.loads(args.input.read_text(encoding="utf-8"))
    result = run(source)
    args.output.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"pairs={len(result['results'])} distinguished={sum(r['classification'].startswith('DISTINGUISHED') for r in result['results'])} unknown={sum(r['classification']=='UNKNOWN' for r in result['results'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
