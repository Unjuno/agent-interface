import hashlib
import json
import os
from pathlib import Path
import random
import sys

ROOT = Path(sys.argv[1])
INPUT = ROOT / "observations"
TRUTH = ROOT / "truth"
INPUT.mkdir(parents=True, exist_ok=True)
TRUTH.mkdir(parents=True, exist_ok=True)
W = H = 256
CONTACT_RADIUS = 96
TIMES = [0, 350, 800, 1275, 1600]  # fixed control cadence
rng = random.Random(20261007)


def pgm(cx, cy, radius, occlude=False, scale_bg=0):
    pixels = bytearray(W * H)
    for y in range(H):
        dy = y - cy
        for x in range(W):
            dx = x - cx
            if dx * dx + dy * dy <= radius * radius:
                pixels[y * W + x] = 255
            elif scale_bg and ((x - 190) ** 2 + (y - 128) ** 2 <= scale_bg * scale_bg):
                pixels[y * W + x] = 96
    if occlude:
        for y in range(H // 3, H):
            start = y * W + W // 2
            pixels[start : start + W // 2] = b"\0" * (W // 2)
    return b"P5\n256 256\n255\n" + pixels


def write_sequence(name, family, contact_ms, frames, truth):
    folder = INPUT / name
    folder.mkdir(parents=True, exist_ok=True)
    records = []
    for i, (ts, track, payload) in enumerate(frames):
        fn = f"frame_{i:02d}.pgm"
        (folder / fn).write_bytes(payload)
        records.append({"timestamp_ms": ts, "track_id": track, "path": f"{name}/{fn}"})
    truth.append({"sequence_id": name, "family": family, "contact_ms": contact_ms})
    return {"sequence_id": name, "frames": records}


latent = []
for i in range(24):
    contact = 2500 + round(i * (9000 - 2500) / 23)
    r0 = 23 + rng.randrange(0, 23)
    cx = 124 + rng.randrange(-6, 7)
    cy = 130 + rng.randrange(-6, 7)
    speed = (CONTACT_RADIUS - r0) / (contact / 1000.0)
    frames = []
    times = [0]
    for lo, hi in ((280, 420), (320, 520), (300, 500), (300, 520)):
        times.append(times[-1] + rng.randint(lo, hi))
    for ts in times:
        radius = max(1, round(r0 + speed * (ts / 1000.0)))
        frames.append((ts, "tracked-object", pgm(cx, cy, radius)))
    latent.append(("approach", contact, frames))

controls = [
    ("control", None, [(t, "tracked-object", pgm(128, 128, 42 + i * 4, scale_bg=24 + i * 3)) for i, t in enumerate(TIMES)]),
    ("control", None, [(t, "tracked-object", pgm(58 + i * 32, 128, 47)) for i, t in enumerate(TIMES)]),
    ("control", None, [(t, "tracked-object", pgm(128, 128, 51)) for t in TIMES]),
    ("control", None, [(t, "tracked-object", pgm(128, 128, 48 + i * 8, occlude=i >= 2)) for i, t in enumerate(TIMES)]),
    ("control", None, [(t, "tracked-object" if i < 3 else "alternate-object", pgm(128, 128, 48 + i * 8)) for i, t in enumerate(TIMES)]),
    ("control", None, [(t if i < 3 else t - 900, "tracked-object", pgm(128, 128, 48 + i * 8)) for i, t in enumerate(TIMES)]),
]
latent.extend(controls)
rng.shuffle(latent)
cases = []
truth = []
for i, (family, contact, frames) in enumerate(latent):
    opaque = f"item_{i:02d}"
    cases.append(write_sequence(opaque, family, contact, frames, truth))

manifest = {"schema": "looming-image-a09-v1", "width": W, "height": H,
            "contact_radius_px": CONTACT_RADIUS, "decision_margin_ms": 100,
            "cases": cases}
(INPUT / "manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8")
(TRUTH / "sealed_truth.json").write_text(json.dumps(truth, sort_keys=True, indent=2) + "\n", encoding="utf-8")
hashes = {}
for path in sorted(p for p in INPUT.rglob("*") if p.is_file()):
    hashes[str(path.relative_to(INPUT)).replace(os.sep, "/")] = hashlib.sha256(path.read_bytes()).hexdigest()
(ROOT / "input.sha256.json").write_text(json.dumps(hashes, sort_keys=True, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"cases": len(cases), "frames": len(hashes) - 1,
                  "manifest_sha256": hashes["manifest.json"],
                  "truth_sha256": hashlib.sha256((TRUTH / "sealed_truth.json").read_bytes()).hexdigest()}, sort_keys=True))




