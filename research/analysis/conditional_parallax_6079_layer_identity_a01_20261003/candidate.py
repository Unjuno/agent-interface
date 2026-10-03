"""Candidate estimator for the #6838 finite layer-identity fixture."""
from __future__ import annotations

import argparse
import hashlib
import json
from fractions import Fraction
from pathlib import Path

ALLOCATION = "CONDITIONAL-PARALLAX-6079-LAYER-IDENTITY-A01-20261003-01"
MIN_SUPPORT = 2
THRESHOLD_SQ = 25


def mean_delta(tracks: list[dict], layer: str | None = None) -> tuple[Fraction, Fraction]:
    selected = [t for t in tracks if layer is None or t.get("layer") == layer]
    if not selected:
        raise ValueError("empty track selection")
    dx = [Fraction(t["xy"][1][0] - t["xy"][0][0]) for t in selected]
    dy = [Fraction(t["xy"][1][1] - t["xy"][0][1]) for t in selected]
    return sum(dx, Fraction()) / len(dx), sum(dy, Fraction()) / len(dy)


def valid_contract(case: dict) -> bool:
    probe = case.get("probe", {})
    if (probe.get("status") != "verified" or probe.get("source_id") != case.get("source_id")
            or probe.get("frame_ids") != case.get("frame_ids") or probe.get("intent_epoch") != "e1"):
        return False
    scenes = case.get("scenes", [])
    if len(scenes) != 2 or [s.get("scene_id") for s in scenes] != ["left", "right"]:
        return False
    maps = []
    for scene in scenes:
        tracks = scene.get("tracks", [])
        ids = [t.get("track_id") for t in tracks]
        if len(ids) != len(set(ids)):
            return False
        if any(t.get("membership") != "verified" or t.get("source_id") != case.get("source_id")
               or t.get("frame_ids") != case.get("frame_ids") for t in tracks):
            return False
        layer_map = {layer: {t["track_id"] for t in tracks if t.get("layer") == layer}
                     for layer in ("target", "background")}
        if any(len(layer_map[layer]) < MIN_SUPPORT for layer in layer_map):
            return False
        maps.append(layer_map)
    return all(maps[0][layer] == maps[1][layer] for layer in ("target", "background"))


def sq(dx: Fraction, dy: Fraction) -> Fraction:
    return dx * dx + dy * dy


def rational(v: Fraction) -> dict:
    return {"n": v.numerator, "d": v.denominator}


def estimate(case: dict) -> dict:
    left, right = (s["tracks"] for s in case["scenes"])
    try:
        all_l, all_r = mean_delta(left), mean_delta(right)
        diagnostic_sq = sq(all_l[0] - all_r[0], all_l[1] - all_r[1])
    except (ValueError, KeyError, IndexError, TypeError):
        diagnostic_sq = None
    if not valid_contract(case):
        return {"case_id": case.get("case_id"), "diagnostic_all_features_sq": rational(diagnostic_sq) if diagnostic_sq is not None else None,
                "layer_relative_sq": None, "status": "UNKNOWN"}
    target_l, target_r = mean_delta(left, "target"), mean_delta(right, "target")
    back_l, back_r = mean_delta(left, "background"), mean_delta(right, "background")
    dx = (target_l[0] - back_l[0]) - (target_r[0] - back_r[0])
    dy = (target_l[1] - back_l[1]) - (target_r[1] - back_r[1])
    relative_sq = sq(dx, dy)
    status = "DISTINGUISHED" if relative_sq > THRESHOLD_SQ else "UNKNOWN"
    return {"case_id": case["case_id"],
            "diagnostic_all_features_sq": rational(diagnostic_sq) if diagnostic_sq is not None else None,
            "layer_relative_sq": rational(relative_sq), "status": status}


def run(public: dict, public_sha256: str) -> list[dict]:
    if public.get("schema") != "conditional-parallax-layer-public-v1":
        raise ValueError("unknown public fixture schema")
    rows = [estimate(case) for case in public.get("cases", [])]
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    raw = args.input.read_bytes()
    public = json.loads(raw)
    rows = run(public, hashlib.sha256(raw).hexdigest())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8", newline="\n") as stream:
        for row in rows:
            stream.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    print(f"candidate_rows={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
