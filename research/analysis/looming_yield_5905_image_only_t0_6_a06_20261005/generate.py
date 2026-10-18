import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(sys.argv[1])
INPUT = ROOT / "observations"
TRUTH = ROOT / "truth"
INPUT.mkdir(parents=True, exist_ok=True)
TRUTH.mkdir(parents=True, exist_ok=True)
W = H = 256
CONTACT_RADIUS = 96
TIMES = [0, 400, 800, 1200, 1600]


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


cases = []
truth = []
for i in range(24):
    contact = 2800 + round(i * (7400 - 2800) / 23)
    r0 = 30 + (i % 4) * 3
    speed = (CONTACT_RADIUS - r0) / (contact / 1000.0)
    frames = []
    for ts in TIMES:
        radius = max(1, round(r0 + speed * (ts / 1000.0)))
        frames.append((ts, "target-A", pgm(128, 128, radius)))
    cases.append(write_sequence(f"approach_{i:02d}", "approach", contact, frames, truth))

# Six controls are deliberately diverse. Three violate the shared eligibility
# gate; the remaining three are eligible negatives and must abstain (UNKNOWN).
controls = [
    ("camera_scale", [(t, "target-A", pgm(128, 128, 40 + i * 5, scale_bg=25 + i * 3)) for i, t in enumerate(TIMES)], None),
    ("lateral_passage", [(t, "target-A", pgm(64 + i * 28, 128, 48)) for i, t in enumerate(TIMES)], None),
    ("stationary_hazard", [(t, "target-A", pgm(128, 128, 52)) for t in TIMES], None),
    ("occlusion", [(t, "target-A", pgm(128, 128, 48 + i * 8, occlude=i >= 2)) for i, t in enumerate(TIMES)], None),
    ("track_swap", [(t, "target-A" if i < 3 else "target-B", pgm(128, 128, 48 + i * 8)) for i, t in enumerate(TIMES)], None),
    ("timestamp_regression", [(t if i < 3 else t - 900, "target-A", pgm(128, 128, 48 + i * 8)) for i, t in enumerate(TIMES)], None),
]
for name, frames, contact in controls:
    cases.append(write_sequence(f"control_{name}", name, contact, frames, truth))

manifest = {"schema": "looming-a05-input-v1", "width": W, "height": H,
            "contact_radius_px": CONTACT_RADIUS, "decision_margin_ms": 100,
            "cases": cases}
(INPUT / "manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8")
(TRUTH / "sealed_truth.json").write_text(json.dumps(truth, sort_keys=True, indent=2) + "\n", encoding="utf-8")

hashes = {}
for path in sorted(p for p in INPUT.rglob("*") if p.is_file()):
    hashes[str(path.relative_to(INPUT)).replace(os.sep, "/")] = hashlib.sha256(path.read_bytes()).hexdigest()
(ROOT / "input.sha256.json").write_text(json.dumps(hashes, sort_keys=True, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"cases": len(cases), "approaches": 24, "controls": 6,
                  "input_files": len(hashes), "input_manifest_sha256": hashes["manifest.json"],
                  "truth_sha256": hashlib.sha256((TRUTH / "sealed_truth.json").read_bytes()).hexdigest()}, sort_keys=True))
