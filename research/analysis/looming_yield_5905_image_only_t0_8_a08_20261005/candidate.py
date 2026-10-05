import json
import math
import sys
from pathlib import Path


def read_pgm(path):
    data = path.read_bytes()
    parts = data.split(b"\n", 3)
    if len(parts) != 4 or parts[0] != b"P5" or parts[1] != b"256 256" or parts[2] != b"255":
        raise ValueError("bad PGM header")
    return parts[3]


def measure(image):
    white = [i for i, value in enumerate(image) if value == 255]
    if not white:
        return {"area": 0, "radius": 0.0}
    xs = [i % 256 for i in white]
    ys = [i // 256 for i in white]
    return {"area": len(white), "radius": ((max(xs)-min(xs)+1)+(max(ys)-min(ys)+1))/4.0}


def main(root):
    root = Path(root)
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    rows = []
    for case in manifest["cases"]:
        frames = []
        for frame in case["frames"]:
            frames.append((frame, read_pgm(root / frame["path"]), measure(read_pgm(root / frame["path"]))))
        reasons = []
        times = [f[0]["timestamp_ms"] for f in frames]
        tracks = [f[0]["track_id"] for f in frames]
        areas = [f[2]["area"] for f in frames]
        if any(b <= a for a, b in zip(times, times[1:])):
            reasons.append("timestamp_not_strictly_increasing")
        if len(set(tracks)) != 1:
            reasons.append("track_identity_changed")
        if any(a <= 0 for a in areas):
            reasons.append("target_not_visible")
        if any(b < a * 0.90 for a, b in zip(areas, areas[1:])):
            reasons.append("visible_area_loss")
        pairs = []
        for i in range(1, len(frames)):
            prior_frame, prior_img, prior = frames[i-1]
            current_frame, current_img, current = frames[i]
            dt = current_frame["timestamp_ms"] - prior_frame["timestamp_ms"]
            diff = sum(a != b for a, b in zip(prior_img, current_img))
            growth = current["area"] / prior["area"] - 1.0 if prior["area"] else None
            dr = current["radius"] - prior["radius"]
            ttc = ((manifest["contact_radius_px"] - current["radius"]) * dt / dr) if dr > 0 and current["radius"] < manifest["contact_radius_px"] else None
            pairs.append({"timestamp_ms": current_frame["timestamp_ms"], "pixel_changed": diff,
                          "relative_area_growth": growth, "secant_ttc_ms": ttc})
        rows.append({"sequence_id": case["sequence_id"], "eligible": not reasons,
                     "reject_reasons": reasons, "pairs": pairs})
    out = {"schema": "looming-a05-candidate-v1", "rows": rows}
    Path("/output/candidate.json").write_text(json.dumps(out, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"rows": len(rows), "eligible": sum(r["eligible"] for r in rows), "output": "/output/candidate.json"}, sort_keys=True))


if __name__ == "__main__":
    main(sys.argv[1])
