#!/usr/bin/env python3
"""Image-only conservative geometry candidate; no fixture truth is imported."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path


def read_pgm(path: Path):
    data = path.read_bytes()
    if not data.startswith(b"P5\n"):
        raise ValueError("PGM_MAGIC")
    head, pixels = data.split(b"255\n", 1)
    dims = head.splitlines()[1].split()
    w, h = map(int, dims)
    if len(pixels) != w * h:
        raise ValueError("PGM_SIZE")
    return w, h, pixels


def components(w, h, p):
    seen = bytearray(w * h)
    out = []
    for i, value in enumerate(p):
        if value < 128 or seen[i]:
            continue
        stack, pts = [i], []
        seen[i] = 1
        while stack:
            n = stack.pop()
            y, x = divmod(n, w)
            pts.append((x, y))
            for yy in range(max(0, y - 1), min(h, y + 2)):
                for xx in range(max(0, x - 1), min(w, x + 2)):
                    q = yy * w + xx
                    if not seen[q] and p[q] >= 128:
                        seen[q] = 1
                        stack.append(q)
        if len(pts) >= 9:
            out.append((sum(x for x, _ in pts) / len(pts),
                        sum(y for _, y in pts) / len(pts), len(pts)))
    return out


def symmetric(points):
    # A deliberately conservative warning for a radial pattern that has a
    # plausible target-only-growth explanation at this observation boundary.
    if len(points) < 6:
        return False
    unmatched = list(points)
    for x, y, _ in points:
        j = min(range(len(unmatched)), key=lambda k: (unmatched[k][0] + x - 128) ** 2
                + (unmatched[k][1] + y - 128) ** 2)
        ox, oy, _ = unmatched[j]
        if math.hypot(ox + x - 128, oy + y - 128) > 2.0:
            return False
        unmatched.pop(j)
    return True


def emit(decision, reason, **extra):
    return {"decision": decision, "reason": reason,
            "simulated_release": False, "safe": False, **extra}


def decide(row, base: Path):
    w0, h0, p0 = read_pgm(base / row["frame0"])
    w1, h1, p1 = read_pgm(base / row["frame1"])
    if (w0, h0) != (w1, h1) or (w0, h0) != (128, 128):
        return emit("UNKNOWN", "IMAGE_DIMENSIONS")
    a, b = components(w0, h0, p0), components(w1, h1, p1)
    targets0 = [c for c in a if math.hypot(c[0] - 64, c[1] - 64) < 40]
    targets1 = [c for c in b if math.hypot(c[0] - 64, c[1] - 64) < 48]
    anchors0 = [c for c in a if math.hypot(c[0] - 64, c[1] - 64) > 65]
    anchors1 = [c for c in b if math.hypot(c[0] - 64, c[1] - 64) > 65]
    if len(anchors0) < 4 or len(anchors1) < 4:
        return emit("UNKNOWN", "ANCHORS_MISSING")
    if len(targets0) != 7 or len(targets1) != 7:
        return emit("REJECT", "FEATURE_COUNT")
    c0 = (sum(x for x, _, _ in targets0) / 7, sum(y for _, y, _ in targets0) / 7)
    c1 = (sum(x for x, _, _ in targets1) / 7, sum(y for _, y, _ in targets1) / 7)
    if math.dist(c0, c1) > 2.0:
        return emit("REJECT", "OFF_AXIS")
    if symmetric(targets0):
        return emit("UNKNOWN", "RADIAL_AMBIGUITY")

    # Match each inner component to the nearest component in the next frame.
    available = list(targets1)
    scales, area_ratios = [], []
    for x, y, area in targets0:
        if not available:
            break
        j = min(range(len(available)), key=lambda k: math.dist((x, y), available[k][:2]))
        xx, yy, aa = available.pop(j)
        r0, r1 = math.dist((x, y), (64, 64)), math.dist((xx, yy), (64, 64))
        if r0 > 3:
            scales.append(r1 / r0)
            area_ratios.append(aa / area)
    if len(scales) < 6:
        return emit("REJECT", "TRACK_LOSS")
    med = sorted(scales)[len(scales) // 2]
    mad = sorted(abs(x - med) for x in scales)[len(scales) // 2]
    if mad > 0.10:
        return emit("REJECT", "INCOHERENT_FLOW")
    if max(area_ratios) - min(area_ratios) > 0.25:
        return emit("REJECT", "SHAPE_CHANGE")

    # Compare far-field anchor centroids; any common-mode drift is a veto.
    drift = max(min(math.dist(x[:2], y[:2]) for y in anchors1) for x in anchors0)
    if drift > 2.0:
        return emit("REJECT", "ANCHOR_MOTION")
    if med < 1.20:
        return emit("REJECT", "EXPANSION_BELOW_GATE")
    dt = row["t"][1] - row["t"][0]
    tau = dt / (med - 1.0)
    cue = tau <= 0.30
    return emit("CUE" if cue else "REJECT",
                "IMAGE_GEOMETRY_TTC" if cue else "TTC_ABOVE_GATE",
                scale=round(med, 6), tau_s=round(tau, 6),
                simulated_release=bool(cue))


def main():
    source = Path(sys.argv[1])
    dest = Path(sys.argv[2])
    root = source.parent
    doc = json.loads(source.read_text())
    results = []
    for row in doc["rows"]:
        results.append({"opaque_id": row["opaque_id"], **decide(row, root)})
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps({"schema": "looming-candidate-v1", "rows": results},
                               indent=2) + "\n")


if __name__ == "__main__":
    main()
