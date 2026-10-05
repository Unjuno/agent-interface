"""Image-only T0.2 comparator with a raster-stable shared trackability gate."""

import base64
import hashlib
import math


PIXEL_THRESHOLDS = (0.005, 0.01, 0.02, 0.04, 0.08)
GROWTH_THRESHOLDS = (1.02, 1.05, 1.10, 1.15, 1.25)
TTC_THRESHOLDS_S = (1.5, 2.0, 2.5, 2.8, 3.0, 4.0)
RELEASE_LATENCY_S = 0.20
FRAME_SIZE = 128
FRAME_PIXELS = FRAME_SIZE * FRAME_SIZE


def _decode(frame):
    if type(frame) is not dict:
        raise ValueError("frame_not_object")
    try:
        raw = base64.b64decode(frame["pgm_b64"], validate=True)
    except (KeyError, ValueError, TypeError) as exc:
        raise ValueError("frame_image_invalid") from exc
    header = b"P5\n128 128\n255\n"
    if not raw.startswith(header) or len(raw) != len(header) + FRAME_PIXELS:
        raise ValueError("frame_pgm_invalid")
    digest = hashlib.sha256(raw).hexdigest()
    if frame.get("sha256") != digest:
        raise ValueError("frame_hash_mismatch")
    return raw[len(header):], digest


def _components(pixels, low, high):
    mask = bytearray(1 if low <= value <= high else 0 for value in pixels)
    seen = bytearray(FRAME_PIXELS)
    components = []
    for origin, active in enumerate(mask):
        if not active or seen[origin]:
            continue
        seen[origin] = 1
        stack = [origin]
        xs = []
        ys = []
        while stack:
            index = stack.pop()
            x, y = index % FRAME_SIZE, index // FRAME_SIZE
            xs.append(x)
            ys.append(y)
            for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if 0 <= nx < FRAME_SIZE and 0 <= ny < FRAME_SIZE:
                    neighbor = ny * FRAME_SIZE + nx
                    if mask[neighbor] and not seen[neighbor]:
                        seen[neighbor] = 1
                        stack.append(neighbor)
        area = len(xs)
        mean_x, mean_y = sum(xs) / area, sum(ys) / area
        cxx = sum((x - mean_x) ** 2 for x in xs) / area
        cyy = sum((y - mean_y) ** 2 for y in ys) / area
        cxy = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys)) / area
        root = math.sqrt(max(0.0, (cxx - cyy) ** 2 + 4 * cxy * cxy))
        eig_max = (cxx + cyy + root) / 2
        eig_min = (cxx + cyy - root) / 2
        axis_ratio = math.sqrt(eig_max / eig_min) if eig_min > 0 else math.inf
        width, height = max(xs) - min(xs) + 1, max(ys) - min(ys) + 1
        components.append({
            "area": area, "cx": mean_x, "cy": mean_y,
            "fill_ratio": area / (width * height),
            "axis_ratio": axis_ratio,
        })
    return sorted(components, key=lambda item: item["area"], reverse=True)


def _marker_scale(pixels):
    points = [(index % FRAME_SIZE, index // FRAME_SIZE)
              for index, value in enumerate(pixels) if 80 <= value <= 130]
    if len(points) < 4:
        return None
    return math.sqrt(sum((x - 64) ** 2 + (y - 64) ** 2
                         for x, y in points) / len(points))


def _semantic(sequence_id, status, reason, features, gate=None, metrics=None):
    trackable = status == "TRACKABLE"
    pixel = metrics.get("pixel_change_fraction") if metrics else None
    growth = metrics.get("target_radius_growth_ratio") if metrics else None
    ttc = metrics.get("secant_ttc_s") if metrics else None
    return {
        "sequence_id": sequence_id,
        "status": status,
        "reason": reason,
        "frames": features,
        "gate": gate or {},
        "metrics": metrics or {},
        "yield_latency_s": RELEASE_LATENCY_S,
        "pixel_grid": {str(threshold): bool(trackable and pixel is not None and
                                           pixel >= threshold)
                       for threshold in PIXEL_THRESHOLDS},
        "growth_grid": {str(threshold): bool(trackable and growth is not None and
                                            growth >= threshold)
                        for threshold in GROWTH_THRESHOLDS},
        "ttc_grid": {str(threshold): bool(trackable and ttc is not None and
                                          RELEASE_LATENCY_S < ttc <= threshold)
                     for threshold in TTC_THRESHOLDS_S},
    }


def analyze(sequence):
    """Return only pixel-, timestamp-, and track-derived measurements."""
    if (type(sequence) is not dict or type(sequence.get("sequence_id")) is not str or
            type(sequence.get("frames")) is not list or len(sequence["frames"]) != 5):
        raise ValueError("sequence_requires_five_frames")
    features, pixel_frames, marker_scales = [], [], []
    for frame in sequence["frames"]:
        pixels, digest = _decode(frame)
        targets = _components(pixels, 181, 255)
        markers = _components(pixels, 80, 130)
        if not targets or len(markers) < 4:
            raise ValueError("target_or_scale_reference_missing")
        target = targets[0]
        marker_scale = _marker_scale(pixels)
        if marker_scale is None or marker_scale <= 0:
            raise ValueError("scale_reference_invalid")
        features.append({
            "t_s": frame.get("t_s"),
            "track_id": frame.get("track_id"),
            "sha256": digest,
            "area": target["area"],
            "radius_px": math.sqrt(target["area"] / math.pi),
            "cx": target["cx"], "cy": target["cy"],
            "shape_fill": target["fill_ratio"],
            "axis_ratio": target["axis_ratio"],
            "marker_scale_px": marker_scale,
        })
        pixel_frames.append(pixels)
        marker_scales.append(marker_scale)

    times = [item["t_s"] for item in features]
    tracks = [item["track_id"] for item in features]
    if any(type(t) not in (int, float) for t in times) or any(
            later <= earlier for earlier, later in zip(times, times[1:])):
        return _semantic(sequence["sequence_id"], "UNKNOWN", "invalid_capture_clock", features)
    gaps = [later - earlier for earlier, later in zip(times, times[1:])]
    if max(gaps) > 0.15:
        return _semantic(sequence["sequence_id"], "UNKNOWN", "capture_gap", features)
    if any(type(track) is not str for track in tracks) or len(set(tracks)) != 1:
        return _semantic(sequence["sequence_id"], "UNKNOWN", "track_identity_changed", features)

    drift = math.hypot(features[-1]["cx"] - features[0]["cx"],
                       features[-1]["cy"] - features[0]["cy"])
    fill_values = [item["shape_fill"] for item in features]
    axis_values = [item["axis_ratio"] for item in features]
    if drift > 4:
        return _semantic(sequence["sequence_id"], "UNKNOWN", "lateral_motion", features)
    if min(fill_values) < 0.50 or max(fill_values) > 0.92 or max(axis_values) > 1.50:
        return _semantic(sequence["sequence_id"], "UNKNOWN", "shape_or_occlusion", features)
    background_ratio = marker_scales[-1] / marker_scales[0]
    if abs(background_ratio - 1.0) > 0.05:
        return _semantic(sequence["sequence_id"], "UNKNOWN", "global_scale_changed", features)

    radius = [item["radius_px"] for item in features]
    dt = times[-1] - times[-2]
    dr = radius[-1] - radius[-2]
    ttc = radius[-1] * dt / dr if dr > 0 else None
    delta_fraction = sum(abs(a - b) >= 32 for a, b in
                         zip(pixel_frames[0], pixel_frames[-1])) / FRAME_PIXELS
    metrics = {
        "pixel_change_fraction": delta_fraction,
        "target_radius_growth_ratio": radius[-1] / radius[0],
        "secant_ttc_s": ttc,
    }
    gate = {
        "valid_clock": True,
        "stable_track": True,
        "centroid_drift_px": drift,
        "shape_fill_min": min(fill_values),
        "shape_fill_max": max(fill_values),
        "axis_ratio_max": max(axis_values),
        "background_scale_ratio": background_ratio,
    }
    return _semantic(sequence["sequence_id"], "TRACKABLE", None, features, gate, metrics)
