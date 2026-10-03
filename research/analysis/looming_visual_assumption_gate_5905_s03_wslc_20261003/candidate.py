"""Image-only looming-assumption gate. No fixture labels or scoring oracle."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path


def read_pgm(path):
    raw = Path(path).read_bytes()
    parts = raw.split(b"\n", 3)
    if len(parts) != 4 or parts[0] != b"P5" or parts[1] != b"96 96" or parts[2] != b"255" or len(parts[3]) != 96 * 96:
        raise ValueError("invalid frozen PGM frame")
    return raw, parts[3]


def components(mask, w=96, h=96):
    pending = set(mask)
    found = []
    while pending:
        seed = pending.pop()
        stack, group = [seed], [seed]
        while stack:
            i = stack.pop()
            x, y = i % w, i // w
            for j in (i - 1 if x else -1, i + 1 if x + 1 < w else -1,
                      i - w if y else -1, i + w if y + 1 < h else -1):
                if j in pending:
                    pending.remove(j)
                    stack.append(j)
                    group.append(j)
        found.append((sum(i % w for i in group) / len(group),
                      sum(i // w for i in group) / len(group)))
    return found


def features(pix):
    target = [i for i, v in enumerate(pix) if v >= 170]
    if not target:
        raise ValueError("target silhouette absent")
    xs, ys = [i % 96 for i in target], [i // 96 for i in target]
    cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
    radius = math.sqrt(len(target) / math.pi)
    bbox = (max(xs) - min(xs) + 1, max(ys) - min(ys) + 1)
    quadrants = [0, 0, 0, 0]
    for x, y in zip(xs, ys):
        quadrants[(2 if y >= 48 else 0) + (1 if x >= 48 else 0)] += 1
    q = [v / len(target) for v in quadrants]
    anchors = components([i for i, v in enumerate(pix) if v == 128])
    flow = [i for i, v in enumerate(pix) if v == 80]
    distances = sorted(math.hypot(i % 96 - cx, i // 96 - cy) for i in flow)
    return {"center": [cx, cy], "radius": radius,
            "aspect": max(bbox) / min(bbox), "quadrants": q,
            "appearance": sum(pix[i] for i in target) / len(target),
            "anchors": sorted(anchors, key=lambda p: (p[1] >= 48, p[0] >= 48)),
            "flow_radii": distances, "target_pixels": len(target)}


def _median(values):
    vals = sorted(values)
    n = len(vals)
    return vals[n // 2] if n % 2 else (vals[n // 2 - 1] + vals[n // 2]) / 2


def classify(f0, f1, dt):
    a0, a1 = f0["anchors"], f1["anchors"]
    if len(a0) < 4 or len(a1) < 4:
        return "UNKNOWN", "missing_anchors", None, None, None
    if len(a0) != 4 or len(a1) != 4:
        return "UNKNOWN", "unstable_anchors", None, None, None
    moves = [math.dist(x, y) for x, y in zip(a0, a1)]
    if all(v > 2.0 for v in moves):
        radial = []
        for p0, p1 in zip(a0, a1):
            d0 = math.dist(p0, (48, 48))
            d1 = math.dist(p1, (48, 48))
            radial.append(d1 / d0)
        if max(radial) - min(radial) < 0.12 and min(radial) > 1.04:
            return "REJECT", "common_mode_zoom", max(moves), None, None
    if max(moves) > 4.0:
        return "UNKNOWN", "unstable_anchors", max(moves), None, None
    q0, q1 = f0["quadrants"], f1["quadrants"]
    imbalance = max(max(q0) - min(q0), max(q1) - min(q1))
    aspect_change = max(f0["aspect"], f1["aspect"]) / min(f0["aspect"], f1["aspect"])
    if imbalance > 0.18 and aspect_change > 1.35:
        return "REJECT", "partial_occlusion", max(moves), None, None
    if math.dist(f0["center"], f1["center"]) > 3.0:
        return "REJECT", "off_axis_motion", max(moves), None, None
    if imbalance > 0.18:
        return "REJECT", "partial_occlusion", max(moves), None, None
    if aspect_change > 1.35:
        return "REJECT", "shape_deformation", max(moves), None, None
    if abs(f1["appearance"] - f0["appearance"]) > 12.0:
        return "REJECT", "appearance_discontinuity", max(moves), None, None
    if len(f0["flow_radii"]) < 20 or len(f1["flow_radii"]) < 20:
        return "UNKNOWN", "insufficient_scene_flow", max(moves), None, None
    ratios = [b / a for a, b in zip(f0["flow_radii"], f1["flow_radii"]) if a > 0]
    scene_ratio = _median(ratios)
    if scene_ratio < 1.05:
        return "UNKNOWN", "insufficient_scene_flow", max(moves), scene_ratio, None
    if scene_ratio > 1.5:
        return "UNKNOWN", "unstable_scene_flow", max(moves), scene_ratio, None
    r0, r1 = f0["radius"], f1["radius"]
    if r1 <= r0:
        return "REJECT", "no_target_expansion", max(moves), scene_ratio, None
    ttc = dt * r0 / (r1 - r0)
    if ttc <= 0 or ttc > 1000:
        return "UNKNOWN", "ttc_outside_frozen_window", max(moves), scene_ratio, ttc
    return "CUE", "coherent_centered_expansion", max(moves), scene_ratio, ttc


def run(fixture_path, output_path):
    root = Path(fixture_path).resolve().parent
    fixture = json.loads(Path(fixture_path).read_text(encoding="utf-8"))
    if fixture.get("schema") != "looming-image-only-s02-v1":
        raise ValueError("fixture schema mismatch")
    out = []
    for case in fixture["cases"]:
        b0, p0 = read_pgm(root / case["frame0"])
        b1, p1 = read_pgm(root / case["frame1"])
        f0, f1 = features(p0), features(p1)
        label, reason, anchor_motion, scene_ratio, ttc = classify(f0, f1, case["t1_ms"] - case["t0_ms"])
        lead = ttc if label == "CUE" and 200 <= ttc <= 900 else None
        out.append({"case_id": case["case_id"], "source_epoch": case["source_epoch"],
                    "frame_sha256": [hashlib.sha256(b0).hexdigest(), hashlib.sha256(b1).hexdigest()],
                    "geometry": {"center0": f0["center"], "center1": f1["center"],
                                 "radius0": f0["radius"], "radius1": f1["radius"],
                                 "aspect0": f0["aspect"], "aspect1": f1["aspect"],
                                 "anchor_motion_max": anchor_motion, "scene_flow_ratio": scene_ratio},
                    "classification": label, "reason": reason,
                    "ttc_ms": round(ttc, 6) if ttc is not None else None,
                    "release_request": lead is not None,
                    "release_lead_ms": round(lead, 6) if lead is not None else None})
    Path(output_path).write_text("".join(json.dumps(x, sort_keys=True, separators=(",", ":")) + "\n" for x in out), encoding="utf-8")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixture", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    rows = run(args.fixture, args.out)
    print(json.dumps({"rows": len(rows), "cues": sum(x["classification"] == "CUE" for x in rows),
                      "output": args.out}, sort_keys=True))
