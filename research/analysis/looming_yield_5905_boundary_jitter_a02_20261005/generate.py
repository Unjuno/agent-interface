#!/usr/bin/env python3
"""Create opaque seeded PGM approach/control rows and auditor-only truth."""
import json
import math
import random
from pathlib import Path

SEED = 20261010
TIMES = [0, 220, 610, 1180, 1800]
CONTACT = 96
ROOT = Path(__file__).parent.resolve()


def pgm(radius, cx=128, cy=128, occlude=False, background_scale=0):
    r = max(2, int(radius))
    pixels = bytearray(256 * 256)
    for y in range(max(0, cy-r), min(256, cy+r+1)):
        for x in range(max(0, cx-r), min(256, cx+r+1)):
            if (x-cx)**2 + (y-cy)**2 <= r*r and not (occlude and x > cx and y < cy + r//2):
                pixels[y*256+x] = 255
    if background_scale:
        # Gray background grid scales around the frame center. It changes full
        # image pixels but is not part of the white-target geometry measurement.
        scale = 1.0 + 0.05 * background_scale
        for gy in range(-48, 49, 12):
            for gx in range(-48, 49, 12):
                x = round(128 + gx*scale); y = round(128 + gy*scale)
                if 0 <= x < 256 and 0 <= y < 256:
                    pixels[y*256+x] = 128
    return b"P5\n256 256\n255\n" + bytes(pixels)


def make_case(rng, idx, family, jitter, contact_ms=None, mode="approach"):
    ident = f"q{rng.getrandbits(64):016x}"
    seq_dir = ROOT / "bundle" / "observations" / ident
    seq_dir.mkdir(parents=True, exist_ok=True)
    frames = []
    base_radius = 24
    base_track = f"trk{rng.getrandbits(48):012x}"
    timestamps = TIMES.copy()
    if mode == "timestamp_regression":
        timestamps[3] = 500
    for j, ts in enumerate(TIMES):
        if mode == "approach":
            # Constant axial speed under a pinhole projection: r = fR/z.
            # The asymptotic scale is chosen per case before any jitter draw.
            scale = 1050 + (idx % 6) * 90
            tc = contact_ms
            ideal = CONTACT * scale / (scale + tc - ts)
            radius = ideal + rng.randint(-jitter, jitter) if jitter else ideal
            cx = cy = 128
        elif mode == "stationary_jitter":
            radius = base_radius + rng.randint(-jitter, jitter)
            cx = cy = 128
        elif mode == "lateral":
            radius = 28
            cx, cy = 100 + j*12, 128
        else:
            radius = 28
            cx = cy = 128
        track = base_track
        occlude = mode == "occlusion" and j == 3
        bg = (j+1) if mode == "background_scale" else 0
        data = pgm(radius, cx, cy, occlude=occlude, background_scale=bg)
        rel = f"{ident}/{j:02d}.pgm"
        (seq_dir / f"{j:02d}.pgm").write_bytes(data)
        if mode == "track_swap" and j == 3:
            track = f"trk{rng.getrandbits(48):012x}"
        frames.append({"timestamp_ms": timestamps[j], "track_id": track, "path": rel})
    return {"sequence_id": ident, "frames": frames}, {
        "sequence_id": ident, "family": family, "contact_ms": contact_ms,
        "jitter_px": jitter, "control_mode": mode,
    }


def generate():
    rng = random.Random(SEED)
    cases, truth = [], []
    idx = 0
    for jitter in (0, 1, 2, 3):
        for k in range(6):
            tc = 2550 + 75*k
            c, t = make_case(rng, idx, "approach", jitter, tc)
            cases.append(c); truth.append(t); idx += 1
    controls = [
        ("stationary_jitter", 1), ("stationary_jitter", 2), ("stationary_jitter", 3),
        ("background_scale", 0), ("background_scale", 0),
        ("lateral", 0), ("lateral", 0), ("occlusion", 0),
        ("track_swap", 0), ("timestamp_regression", 0),
        ("stationary", 0), ("stationary", 0),
    ]
    for mode, jitter in controls:
        c, t = make_case(rng, idx, "control", jitter, None, mode)
        cases.append(c); truth.append(t); idx += 1
    return {
        "manifest": {"schema": "unjuno.issue8112.observations.a02.v1",
                     "seed": SEED, "contact_radius_px": CONTACT,
                     "cases": cases},
        "truth": {"schema": "unjuno.issue8112.truth.a02.v1", "cases": truth},
    }


def write():
    bundle = ROOT / "bundle"
    obs = bundle / "observations"
    truth = bundle / "truth"
    obs.mkdir(parents=True, exist_ok=True); truth.mkdir(parents=True, exist_ok=True)
    data = generate()
    (obs / "manifest.json").write_text(json.dumps(data["manifest"], sort_keys=True, indent=2)+"\n")
    (truth / "sealed_truth.json").write_text(json.dumps(data["truth"], sort_keys=True, indent=2)+"\n")
    return data


if __name__ == "__main__":
    d = write()
    print(json.dumps({"seed": SEED, "cases": len(d["manifest"]["cases"]),
                      "approaches": sum(x["family"] == "approach" for x in d["truth"]["cases"]),
                      "controls": sum(x["family"] == "control" for x in d["truth"]["cases"])}))
