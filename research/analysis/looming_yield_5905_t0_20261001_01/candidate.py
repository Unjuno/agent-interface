import base64
import hashlib
import json
import math
import sys


def pgm(radius, n=256, samples=4):
    pixels = bytearray(n * n)
    offsets = [(i + 0.5) / samples - 0.5 for i in range(samples)]
    extent = min(n // 2 - 1, int(math.ceil(radius + 1)))
    for y in range(n // 2 - extent, n // 2 + extent + 1):
        for x in range(n // 2 - extent, n // 2 + extent + 1):
            covered = 0
            for oy in offsets:
                for ox in offsets:
                    if (x + ox - n / 2) ** 2 + (y + oy - n / 2) ** 2 <= radius * radius:
                        covered += 1
            pixels[y * n + x] = round(255 * covered / (samples * samples))
    return f"P5\n{n} {n}\n255\n".encode() + bytes(pixels)


def measure_radius(frame, n=256):
    header, pixels = frame.split(b"\n255\n", 1)
    if header != f"P5\n{n} {n}".encode() or len(pixels) != n*n:
        raise ValueError("invalid_frame")
    return math.sqrt(sum(pixels) / 255.0 / math.pi)


def run(fixture):
    out = {"allocation": fixture["allocation"], "frames": [], "cases": []}
    cfg = fixture["render"]
    for case in fixture["cases"]:
        if case["kind"] == "control":
            signals = case["signals"]
            times = signals.get("timestamps", [0.0, 0.1])
            tracks = signals.get("track_ids", ["track-1", "track-1"])
            for i, t in enumerate(times):
                frame = pgm(8 + i)
                out["frames"].append({"case":case["id"],"index":i,"t":t,"track":tracks[i],"source":"session-1","bytes_b64":base64.b64encode(frame).decode(),"sha256":hashlib.sha256(frame).hexdigest()})
            reason = None
            if signals.get("center_shift_px", 0) > 4:
                reason = "off_axis"
            elif abs(signals.get("background_scale_ratio", 1.0)-1.0) > 0.05:
                reason = "camera_scale_changed"
            elif signals.get("expansion_residual_fraction", 0) > 0.10:
                reason = "target_motion_not_rigid"
            elif signals.get("occluded", False):
                reason = "occluded"
            elif len(set(tracks)) > 1:
                reason = "track_identity_changed"
            elif any(b <= a for a, b in zip(times, times[1:])):
                reason = "timestamps_not_increasing"
            elif signals.get("hazard_visible", False) and signals.get("expansion_rate", 0) <= 0:
                reason = "nonlooming_hazard"
            out["cases"].append({"id":case["id"],"status":"UNKNOWN" if reason else "NO_CUE","reason":reason,"release_requested":False,"safe":False})
            continue
        radii = []
        count = int(math.ceil((case["z0"] / case["speed"]) / cfg["dt"]))
        times = [round(i * cfg["dt"], 10) for i in range(count)]
        observed = []
        for i, t in enumerate(times):
            z = case["z0"] - case["speed"] * t
            radius = cfg["K"] / z
            frame = pgm(radius, cfg["width"], cfg["supersample"])
            observed_radius = measure_radius(frame, cfg["width"])
            radii.append((t, observed_radius))
            out["frames"].append({"case":case["id"],"index":i,"t":t,"track":"track-1","source":"session-1","bytes_b64":base64.b64encode(frame).decode(),"sha256":hashlib.sha256(frame).hexdigest()})
        decision = None
        for i in range(1, len(radii)):
            t0, r0 = radii[i-1]
            t1, r1 = radii[i]
            rate = (r1-r0)/(t1-t0)
            estimate = r1/rate if rate > 0 else None
            truth = (case["z0"]-case["speed"]*t1)/case["speed"]
            if estimate is not None and estimate <= cfg["threshold_ttc_s"]:
                decision = {"frame_index":i,"t":t1,"estimate_s":estimate,"truth_s":truth,"release_at_s":t1+cfg["release_latency_s"],"contact_at_s":case["z0"]/case["speed"]}
                break
        out["cases"].append({"id":case["id"],"status":"CUE" if decision else "NO_CUE","decision":decision,"release_requested":bool(decision),"safe":False})
    return out


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as f:
        result = run(json.load(f))
    with open(sys.argv[2], "w", encoding="utf-8") as f:
        json.dump(result, f, sort_keys=True, separators=(",", ":"))
        f.write("\n")
