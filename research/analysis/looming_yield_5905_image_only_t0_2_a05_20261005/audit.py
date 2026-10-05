"""Independent raw-only auditor; deliberately does not import candidate.py."""

import base64
import gzip
import hashlib
import json
import math
import sys


N = 128
PIXEL_GRID = (0.005, 0.01, 0.02, 0.04, 0.08)
GROWTH_GRID = (1.02, 1.05, 1.10, 1.15, 1.25)
TTC_GRID = (1.5, 2.0, 2.5, 2.8, 3.0, 4.0)
LATENCY = 0.20


def _decode(frame):
    try:
        raw = base64.b64decode(frame["pgm_b64"], validate=True)
    except (KeyError, ValueError, TypeError) as exc:
        raise ValueError("frame_image_invalid") from exc
    prefix = b"P5\n128 128\n255\n"
    if not raw.startswith(prefix) or len(raw) != len(prefix) + N * N:
        raise ValueError("frame_pgm_invalid")
    digest = hashlib.sha256(raw).hexdigest()
    if frame.get("sha256") != digest:
        raise ValueError("frame_hash_mismatch")
    return raw[len(prefix):], digest


def _regions(pixels, lower, upper):
    """Return pixel clusters via an independently written stack traversal."""
    eligible = bytearray(lower <= shade <= upper for shade in pixels)
    visited = bytearray(N * N)
    regions = []
    for seed in range(N * N):
        if not eligible[seed] or visited[seed]:
            continue
        todo = [seed]
        visited[seed] = 1
        coords = []
        while todo:
            pos = todo.pop()
            x, y = pos % N, pos // N
            coords.append((x, y))
            if x and eligible[pos - 1] and not visited[pos - 1]:
                visited[pos - 1] = 1
                todo.append(pos - 1)
            if x + 1 < N and eligible[pos + 1] and not visited[pos + 1]:
                visited[pos + 1] = 1
                todo.append(pos + 1)
            if y and eligible[pos - N] and not visited[pos - N]:
                visited[pos - N] = 1
                todo.append(pos - N)
            if y + 1 < N and eligible[pos + N] and not visited[pos + N]:
                visited[pos + N] = 1
                todo.append(pos + N)
        count = len(coords)
        mx = sum(p[0] for p in coords) / count
        my = sum(p[1] for p in coords) / count
        xx = sum((p[0] - mx) ** 2 for p in coords) / count
        yy = sum((p[1] - my) ** 2 for p in coords) / count
        xy = sum((p[0] - mx) * (p[1] - my) for p in coords) / count
        disc = math.sqrt((xx - yy) ** 2 + 4 * xy ** 2)
        major, minor = (xx + yy + disc) / 2, (xx + yy - disc) / 2
        ratio = math.sqrt(major / minor) if minor > 0 else math.inf
        width = max(p[0] for p in coords) - min(p[0] for p in coords) + 1
        height = max(p[1] for p in coords) - min(p[1] for p in coords) + 1
        regions.append({"area": count, "cx": mx, "cy": my,
                        "shape_fill": count / (width * height),
                        "axis_ratio": ratio})
    return sorted(regions, key=lambda row: row["area"], reverse=True)


def inspect_frame(frame):
    """Reconstruct candidate-visible features directly from one encoded frame."""
    pixels, digest = _decode(frame)
    targets = _regions(pixels, 181, 255)
    markers = _regions(pixels, 80, 130)
    marker_points = [(i % N, i // N) for i, shade in enumerate(pixels)
                     if 80 <= shade <= 130]
    if not targets or len(markers) < 4 or len(marker_points) < 4:
        raise ValueError("target_or_scale_reference_missing")
    radius = math.sqrt(sum((x - 64) ** 2 + (y - 64) ** 2
                           for x, y in marker_points) / len(marker_points))
    target = targets[0]
    return {"sha256": digest, "area": target["area"],
            "radius_px": math.sqrt(target["area"] / math.pi),
            "cx": target["cx"], "cy": target["cy"],
            "shape_fill": target["shape_fill"],
            "axis_ratio": target["axis_ratio"], "marker_scale_px": radius}


def frame_measurement_matches(reconstructed, claimed):
    keys = ("sha256", "area", "radius_px", "cx", "cy", "shape_fill",
            "axis_ratio", "marker_scale_px")
    return all(reconstructed.get(key) == claimed.get(key) for key in keys)


def _expected(sequence):
    observations = sequence["frames"]
    if type(observations) is not list or len(observations) != 5:
        raise ValueError("sequence_requires_five_frames")
    features = []
    byte_frames = []
    for frame in observations:
        row = inspect_frame(frame)
        row.update({"t_s": frame.get("t_s"), "track_id": frame.get("track_id")})
        features.append(row)
        pixels, _ = _decode(frame)
        byte_frames.append(pixels)
    times = [row["t_s"] for row in features]
    tracks = [row["track_id"] for row in features]
    if any(type(t) not in (int, float) for t in times) or any(
            b <= a for a, b in zip(times, times[1:])):
        return _unknown(features, "invalid_capture_clock")
    gaps = [b - a for a, b in zip(times, times[1:])]
    if max(gaps) > 0.15:
        return _unknown(features, "capture_gap")
    if any(type(t) is not str for t in tracks) or len(set(tracks)) != 1:
        return _unknown(features, "track_identity_changed")
    drift = math.hypot(features[-1]["cx"] - features[0]["cx"],
                       features[-1]["cy"] - features[0]["cy"])
    fills = [row["shape_fill"] for row in features]
    ratios = [row["axis_ratio"] for row in features]
    if drift > 4:
        return _unknown(features, "lateral_motion")
    if min(fills) < 0.50 or max(fills) > 0.92 or max(ratios) > 1.50:
        return _unknown(features, "shape_or_occlusion")
    bg_ratio = features[-1]["marker_scale_px"] / features[0]["marker_scale_px"]
    if abs(bg_ratio - 1.0) > 0.05:
        return _unknown(features, "global_scale_changed")
    radii = [row["radius_px"] for row in features]
    dt = times[-1] - times[-2]
    dr = radii[-1] - radii[-2]
    ttc = radii[-1] * dt / dr if dr > 0 else None
    changed = sum(abs(a - b) >= 32 for a, b in
                  zip(byte_frames[0], byte_frames[-1])) / (N * N)
    metrics = {"pixel_change_fraction": changed,
               "target_radius_growth_ratio": radii[-1] / radii[0],
               "secant_ttc_s": ttc}
    gate = {"valid_clock": True, "stable_track": True,
            "centroid_drift_px": drift, "shape_fill_min": min(fills),
            "shape_fill_max": max(fills), "axis_ratio_max": max(ratios),
            "background_scale_ratio": bg_ratio}
    return _scored("TRACKABLE", None, features, gate, metrics)


def _unknown(features, reason):
    return _scored("UNKNOWN", reason, features, {}, {})


def _scored(status, reason, features, gate, metrics):
    usable = status == "TRACKABLE"
    pixel = metrics.get("pixel_change_fraction")
    growth = metrics.get("target_radius_growth_ratio")
    ttc = metrics.get("secant_ttc_s")
    return {"status": status, "reason": reason, "frames": features,
            "gate": gate, "metrics": metrics, "yield_latency_s": LATENCY,
            "pixel_grid": {str(x): bool(usable and pixel is not None and pixel >= x)
                           for x in PIXEL_GRID},
            "growth_grid": {str(x): bool(usable and growth is not None and growth >= x)
                            for x in GROWTH_GRID},
            "ttc_grid": {str(x): bool(usable and ttc is not None and LATENCY < ttc <= x)
                         for x in TTC_GRID}}


def audit(observations, truth, raw):
    errors = []
    source = {row["sequence_id"]: row for row in observations["sequences"]}
    results = {row["sequence_id"]: row for row in raw["sequences"]}
    if len(source) != len(observations["sequences"]):
        errors.append("duplicate_observation_id")
    if len(results) != len(raw["sequences"]) or set(source) != set(results):
        errors.append("sequence_set")
    for sid, sequence in source.items():
        if sid not in results:
            continue
        try:
            expected = _expected(sequence)
        except (KeyError, TypeError, ValueError, ZeroDivisionError) as exc:
            errors.append("raw_decode:" + sid + ":" + str(exc))
            continue
        claimed = results[sid]
        for field in ("status", "reason", "gate", "metrics", "yield_latency_s",
                      "pixel_grid", "growth_grid", "ttc_grid"):
            if expected[field] != claimed.get(field):
                errors.append("reconstruct:" + sid + ":" + field)
        if expected["frames"] != claimed.get("frames"):
            errors.append("frame_features:" + sid)

    positive = set(truth["contact_cases"])
    controls = set(truth["control_labels"])
    if positive & controls or not (positive | controls) <= set(source):
        errors.append("truth_sequence_partition")
    if "animation-twin-1" in controls:
        controls.remove("animation-twin-1")
    frontiers = {}
    for method in ("pixel", "growth", "ttc"):
        key = method + "_grid"
        points = []
        thresholds = list(results.get(next(iter(source), ""), {}).get(key, {}))
        for threshold in thresholds:
            tp = sum(bool(results.get(sid, {}).get(key, {}).get(threshold))
                     for sid in positive)
            fp = sum(bool(results.get(sid, {}).get(key, {}).get(threshold))
                     for sid in controls)
            points.append({"threshold": threshold, "tp": tp, "fp": fp})
        frontiers[method] = {"points": points,
                             "max_tp_at_fp_0": max((p["tp"] for p in points
                                                    if p["fp"] == 0), default=0)}
    for sid in positive:
        if sid not in results or sid not in truth["contact_cases"]:
            errors.append("approach_missing:" + sid)
            continue
        result = results[sid]
        lead = truth["contact_cases"][sid]["contact_at_s"] - (
            result["frames"][-1]["t_s"] + LATENCY)
        if result["status"] != "TRACKABLE" or not any(result["ttc_grid"].values()) or lead <= 0:
            errors.append("approach_not_released:" + sid)
    for sid in controls:
        if sid not in results:
            errors.append("control_missing:" + sid)
            continue
        result = results[sid]
        if result["status"] != "UNKNOWN" or any(
                any(result[key].values()) for key in ("pixel_grid", "growth_grid", "ttc_grid")):
            errors.append("control_not_abstained:" + sid)
    twin = "animation-twin-1"
    if twin in source and "approach-1" in source and twin in results and "approach-1" in results:
        left, right = source["approach-1"], source[twin]
        left_input = [(f["t_s"], f["track_id"], f["pgm_b64"]) for f in left["frames"]]
        right_input = [(f["t_s"], f["track_id"], f["pgm_b64"]) for f in right["frames"]]
        if left_input != right_input:
            errors.append("twin_input_not_identical")
        lout = {k: v for k, v in results["approach-1"].items() if k != "sequence_id"}
        rout = {k: v for k, v in results[twin].items() if k != "sequence_id"}
        if lout != rout:
            errors.append("twin_semantic_output_mismatch")
    no_increment = (frontiers["ttc"]["max_tp_at_fp_0"] <=
                    max(frontiers["pixel"]["max_tp_at_fp_0"],
                        frontiers["growth"]["max_tp_at_fp_0"]))
    if no_increment:
        errors.append("no_incremental_value_at_zero_false_yield")
    return {"audit": "PASS_RAW_RECONSTRUCTION" if not errors else "FAIL_RAW_RECONSTRUCTION",
            "errors": errors, "checked_sequences": len(source),
            "frontier": frontiers, "incremental_value": not no_increment,
            "disposition": "PASS_METHOD_SCOPED_WITH_IDENTIFIABILITY_LIMIT"
            if not errors else "FAIL_OR_STOP"}


def audit_regression(observations, truth, screen):
    """Recompute OLS-TTC and trigger grids from raw PGM, without candidate code."""
    errors = []
    claimed = screen.get("per_sequence", {})
    source = {sequence["sequence_id"]: sequence
              for sequence in observations.get("sequences", [])}
    if set(source) != set(claimed):
        errors.append("regression_sequence_set")
    audited = {}
    for sid, sequence in source.items():
        try:
            expected = _expected(sequence)
            points = expected["frames"]
            times = [row["t_s"] for row in points]
            radii = [row["radius_px"] for row in points]
            estimate = None
            if expected["status"] == "TRACKABLE":
                mean_t = sum(times) / 5
                mean_r = sum(radii) / 5
                slope = sum((t - mean_t) * (r - mean_r)
                            for t, r in zip(times, radii)) / sum(
                                (t - mean_t) ** 2 for t in times)
                estimate = radii[-1] / slope if slope > 0 else None
            actual = claimed.get(sid, {})
            if expected["status"] != actual.get("status"):
                errors.append("trackability:" + sid)
            got = actual.get("regression_ttc_s")
            if estimate is None:
                if got is not None:
                    errors.append("regression_ttc:" + sid)
            elif type(got) not in (int, float) or not math.isclose(
                    estimate, got, rel_tol=1e-12, abs_tol=1e-12):
                errors.append("regression_ttc:" + sid)
            want_grid = {str(limit): bool(
                expected["status"] == "TRACKABLE" and estimate is not None and
                LATENCY < estimate <= limit) for limit in TTC_GRID}
            if want_grid != actual.get("regression_grid"):
                errors.append("regression_grid:" + sid)
            for key, field in (("pixel_grid", "pixel_grid"),
                               ("growth_grid", "growth_grid"),
                               ("secant_grid", "ttc_grid")):
                if expected[field] != actual.get(key):
                    errors.append(key + ":" + sid)
            audited[sid] = {"status": expected["status"],
                            "reason": expected["reason"],
                            "pixel_grid": expected["pixel_grid"],
                            "growth_grid": expected["growth_grid"],
                            "secant_grid": expected["ttc_grid"],
                            "regression_ttc_s": estimate,
                            "regression_grid": want_grid}
        except (KeyError, TypeError, ValueError, ZeroDivisionError) as exc:
            errors.append("regression_decode:" + sid + ":" + str(exc))
    positives = set(truth["contact_cases"])
    controls = set(truth["control_labels"]) - {"animation-twin-1"}
    methods = {"pixel": "pixel_grid", "growth": "growth_grid",
               "secant": "secant_grid", "regression": "regression_grid"}
    frontiers = {}
    for method, field in methods.items():
        points = []
        for threshold in next(iter(audited.values()))[field]:
            tp = sum(bool(audited[sid][field][threshold]) for sid in positives
                     if sid in audited)
            fp = sum(bool(audited[sid][field][threshold]) for sid in controls
                     if sid in audited)
            points.append({"threshold": threshold, "tp": tp, "fp": fp})
        frontiers[method] = {"points": points,
                             "max_tp_at_fp_0": max((p["tp"] for p in points
                                                    if p["fp"] == 0), default=0)}
    leads = {}
    for sid in positives:
        if sid not in audited or sid not in truth["contact_cases"]:
            errors.append("positive_missing:" + sid)
            continue
        last_t = source[sid]["frames"][-1]["t_s"]
        lead = truth["contact_cases"][sid]["contact_at_s"] - (last_t + LATENCY)
        triggered = any(audited[sid]["regression_grid"].values())
        if triggered and lead <= 0:
            errors.append("nonpositive_release_lead:" + sid)
        leads[sid] = {"triggered": triggered, "analytic_release_lead_s": lead}
    twin_match = None
    if "approach-1" in source and "animation-twin-1" in source:
        twin_match = (
            [(f["t_s"], f["track_id"], f["pgm_b64"]) for f in source["approach-1"]["frames"]] ==
            [(f["t_s"], f["track_id"], f["pgm_b64"]) for f in source["animation-twin-1"]["frames"]] and
            audited.get("approach-1") == audited.get("animation-twin-1"))
        if not twin_match:
            errors.append("identical_twin_mismatch")
    no_increment = (frontiers["regression"]["max_tp_at_fp_0"] <=
                    max(frontiers["pixel"]["max_tp_at_fp_0"],
                        frontiers["growth"]["max_tp_at_fp_0"]))
    return {"audit": "PASS_RAW_REGRESSION_RECONSTRUCTION" if not errors
            else "FAIL_RAW_REGRESSION_RECONSTRUCTION",
            "errors": errors, "checked_sequences": len(audited),
            "frontiers": frontiers, "approach_leads": leads,
            "identical_twin_matches": twin_match,
            "incremental_value": "NO_INCREMENTAL_VALUE" if no_increment
            else "INCREMENTAL_SIGNAL_ON_THIS_FIXTURE",
            "reconstructed": audited}


def _read_json(path):
    opener = gzip.open if path.endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as stream:
        return json.load(stream)


def main(observation_path, truth_path, raw_path, output_path):
    report = audit(_read_json(observation_path), _read_json(truth_path),
                   _read_json(raw_path))
    with open(output_path, "w", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, sort_keys=True, indent=2)
        stream.write("\n")
    print(json.dumps({"audit": report["audit"], "errors": report["errors"],
                      "disposition": report["disposition"]}, sort_keys=True))
    return 0 if not report["errors"] else 1


def regression_main(observation_path, truth_path, screen_path, output_path):
    report = audit_regression(_read_json(observation_path),
                              _read_json(truth_path), _read_json(screen_path))
    with open(output_path, "w", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, sort_keys=True, indent=2)
        stream.write("\n")
    print(json.dumps({key: value for key, value in report.items()
                      if key != "reconstructed"}, sort_keys=True))
    return 0 if not report["errors"] else 1


if __name__ == "__main__":
    if len(sys.argv) == 6 and sys.argv[1] == "--regression":
        raise SystemExit(regression_main(*sys.argv[2:]))
    if len(sys.argv) != 5:
        raise SystemExit("usage: audit.py OBSERVATIONS.json[.gz] TRUTH.json[.gz] "
                         "RAW.json AUDIT.json")
    raise SystemExit(main(*sys.argv[1:]))
