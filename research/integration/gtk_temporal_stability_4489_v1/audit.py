"""Independent raw-XWD, window-identity, schedule, and stability auditor."""
import argparse
import collections
import hashlib
import json
import os
from pathlib import Path
import re
import struct


def parse_xwd(raw):
    if len(raw) < 100:
        raise ValueError("short_header")
    header = struct.unpack(">25I", raw[:100])
    if header[1] != 7 or header[2] != 2:
        raise ValueError("not_xwd_zpixmap")
    width, height, byte_order, bpp, stride = header[4], header[5], header[7], header[11], header[12]
    ncolors = header[19]
    start = header[0] + ncolors * 12
    bytes_per_pixel = bpp // 8
    if width <= 0 or height <= 0 or bytes_per_pixel not in (3, 4) or stride < width * bytes_per_pixel:
        raise ValueError("unsupported_or_invalid_xwd_layout")
    if len(raw) < start + stride * height:
        raise ValueError("truncated_pixel_data")
    endian = "little" if byte_order == 0 else "big"
    pixels = []
    for y in range(height):
        line = []
        base = start + y * stride
        for x in range(width):
            pos = base + x * bytes_per_pixel
            line.append(int.from_bytes(raw[pos:pos + bytes_per_pixel], endian))
        pixels.append(line)
    return {"width": width, "height": height, "pixels": pixels,
            "sha256": hashlib.sha256(raw).hexdigest()}


def diff(a, b):
    if (a["width"], a["height"]) != (b["width"], b["height"]):
        raise ValueError("frame_dimensions_changed")
    points = [(x, y) for y in range(a["height"]) for x in range(a["width"])
              if a["pixels"][y][x] != b["pixels"][y][x]]
    if points:
        xs, ys = zip(*points)
        bounds = [min(xs), min(ys), max(xs), max(ys)]
    else:
        bounds = None
    return {"count": len(points), "bbox": bounds, "coords": points}


def mask_from(images, halo=1):
    volatile = set()
    for image in images[1:]:
        volatile.update(diff(images[0], image)["coords"])
    width, height = images[0]["width"], images[0]["height"]
    out = set()
    for x, y in volatile:
        for dy in range(-halo, halo + 1):
            for dx in range(-halo, halo + 1):
                if 0 <= x + dx < width and 0 <= y + dy < height:
                    out.add((x + dx, y + dy))
    return out


def live_window(display_name, xid):
    from Xlib import X, display
    dpy = display.Display(display_name)
    try:
        win = dpy.create_resource_object("window", int(xid))
        attrs = win.get_attributes()
        geom = win.get_geometry()
        pid_atom = dpy.intern_atom("_NET_WM_PID")
        prop = win.get_full_property(pid_atom, X.AnyPropertyType)
        pid = int(prop.value[0]) if prop is not None and len(prop.value) else None
        title = win.get_wm_name()
        if isinstance(title, bytes):
            title = title.decode("utf-8", "replace")
        return {"xid": int(xid), "pid": pid, "title": title,
                "geometry": [int(geom.x), int(geom.y), int(geom.width), int(geom.height)],
                "map_state": int(attrs.map_state)}
    finally:
        dpy.close()


def audit(root, live):
    root = Path(root)
    manifest = json.loads((root / "manifest.json").read_text())
    schedule = manifest["schedule"]
    rows = [json.loads(line) for line in (root / "captures.jsonl").read_text().splitlines()]
    errors = []
    expected = schedule["pre_decoy_captures"] + schedule["post_decoy_captures"]
    if len(rows) != expected:
        errors.append("capture_denominator")
    order = [("pre_decoy", i + 1) for i in range(schedule["pre_decoy_captures"])] + [
        ("post_decoy", i + 1) for i in range(schedule["post_decoy_captures"])]
    if [(r.get("phase"), r.get("index")) for r in rows] != order:
        errors.append("capture_order")
    parsed = []
    for row in rows:
        path = root / row["path"]
        raw = path.read_bytes()
        frame = parse_xwd(raw)
        if hashlib.sha256(raw).hexdigest() != row["sha256"]:
            errors.append("frame_hash:" + row["path"])
        if row["capture_end_ns"] < row["capture_start_ns"]:
            errors.append("capture_clock:" + row["path"])
        if row["identity_before"] != row["identity_after"]:
            errors.append("window_or_focus_changed_during_capture:" + row["path"])
        identity = row["identity_before"]
        parsed.append((row, frame))
    if len({r[0]["identity_before"]["xid"] for r in parsed}) != 1:
        errors.append("target_xid_changed")
    target_identity_snapshots = [manifest.get(k) for k in
                                 ("target_identity_initial", "target_identity_after_decoy", "target_identity_final")]
    if any(item is None for item in target_identity_snapshots) or \
       not all(item == target_identity_snapshots[0] for item in target_identity_snapshots[1:]):
        errors.append("target_identity_or_focus_changed_across_decoy")
    entry_xid = manifest.get("target_entry_xid")
    focus_ids = {row["identity_before"]["focus_xid"] for row, _ in parsed}
    if entry_xid is None or focus_ids != {entry_xid}:
        errors.append("target_entry_focus_context_not_stable")
    target_pid = manifest["target_pid"]
    decoy_pid = manifest["decoy_pid"]
    target_xid = manifest["target_xid"]
    decoy_xid = manifest["decoy_xid"]
    target_identity_strings = [row["identity_before"]["xprop"] for row, _ in parsed]
    if any((m := re.search(r"_NET_WM_PID[^=]*=\s*(\d+)", s)) is None or
           int(m.group(1)) != target_pid for s in target_identity_strings):
        errors.append("target_pid_receipt_mismatch")
    if live and (not (Path("/proc") / str(target_pid)).exists() or
                 not (Path("/proc") / str(decoy_pid)).exists()):
        errors.append("process_not_live_during_audit")
    target_live = live_window(manifest["display"], target_xid) if live else None
    decoy_live = live_window(manifest["display"], decoy_xid) if live else None
    if live:
        for label, info, pid in (("target", target_live, target_pid), ("decoy", decoy_live, decoy_pid)):
            if info["pid"] != pid or info["title"] != "AgentInterfaceGtkFixture":
                errors.append(label + "_live_identity")
            if info["map_state"] != 2:
                errors.append(label + "_not_viewable")
        if target_live["xid"] == decoy_live["xid"] or target_live["pid"] == decoy_live["pid"]:
            errors.append("decoy_not_independent_window")
        if target_live["geometry"][2:] != decoy_live["geometry"][2:]:
            errors.append("decoy_geometry_mismatch")
        tx, ty, tw, th = target_live["geometry"]
        dx, dy, dw, dh = decoy_live["geometry"]
        if tx < dx + dw and dx < tx + tw and ty < dy + dh and dy < ty + th:
            errors.append("decoy_overlaps_target")
    else:
        target_geom = manifest["target_identity_final"]["geometry"]
        decoy_geom = manifest["decoy_identity"]["geometry"]
        tx, ty = target_geom["Absolute upper-left X"], target_geom["Absolute upper-left Y"]
        tw, th = target_geom["Width"], target_geom["Height"]
        dx, dy = decoy_geom["Absolute upper-left X"], decoy_geom["Absolute upper-left Y"]
        dw, dh = decoy_geom["Width"], decoy_geom["Height"]
        if (tw, th) != (dw, dh):
            errors.append("decoy_geometry_mismatch")
        if tx < dx + dw and dx < tx + tw and ty < dy + dh and dy < ty + th:
            errors.append("decoy_overlaps_target")
    target_initial = parse_xwd((root / "frames/target-initial.xwd").read_bytes())
    decoy_frame = parse_xwd((root / "frames/decoy-saved-looking.xwd").read_bytes())
    decoy_difference = diff(target_initial, decoy_frame)
    if decoy_difference["count"] == 0:
        errors.append("saved_looking_decoy_image_not_distinct")
    groups = collections.defaultdict(list)
    for row, frame in parsed:
        groups[row["identity_before"]["focus_xid"]].append((row, frame))
    decisions = []
    masks = {}
    for focus, group in groups.items():
        baseline_n = schedule["baseline_captures_per_focus_context"]
        if len(group) < baseline_n:
            for row, _ in group:
                decisions.append({"path": row["path"], "focus_xid": focus,
                                  "decision": "REBASELINE_INCOMPLETE_CONTEXT"})
            continue
        baseline = [item[1] for item in group[:baseline_n]]
        raw_volatile = set()
        for image in baseline[1:]:
            raw_volatile.update(diff(baseline[0], image)["coords"])
        raw_coords = sorted([list(p) for p in raw_volatile], key=lambda p: (p[1], p[0]))
        raw_bbox = ([min(x for x, _ in raw_coords), min(y for _, y in raw_coords),
                     max(x for x, _ in raw_coords), max(y for _, y in raw_coords)]
                    if raw_coords else None)
        mask = mask_from(baseline, schedule["volatile_mask_halo_px"])
        masks[str(focus)] = {"volatile_pixel_count_with_halo": len(mask),
                             "raw_volatile_pixel_count": len(raw_volatile),
                             "raw_volatile_bbox": raw_bbox,
                             "raw_volatile_coords": raw_coords,
                             "calibration_paths": [x[0]["path"] for x in group[:baseline_n]]}
        reference = baseline[0]
        for row, frame in group[baseline_n:]:
            changes = diff(reference, frame)
            outside = [(x, y) for x, y in changes["coords"] if (x, y) not in mask]
            decision = "STABLE_WITHIN_CALIBRATED_MASK" if not outside else "FAIL_UNCALIBRATED_PIXEL_CHANGE"
            decisions.append({"path": row["path"], "focus_xid": focus, "decision": decision,
                              "changed_pixel_count": changes["count"], "changed_bbox": changes["bbox"],
                              "outside_mask_count": len(outside),
                              "outside_mask_bbox": ([min(x for x, y in outside), min(y for x, y in outside),
                                                     max(x for x, y in outside), max(y for x, y in outside)]
                                                    if outside else None)})
            if outside:
                errors.append("uncalibrated_change:" + row["path"])
    path_order = {row["path"]: i for i, (row, _) in enumerate(parsed)}
    decisions.sort(key=lambda d: path_order[d["path"]])
    # Independently construct two valid synthetic XWD byte strings and detect a changed pixel.
    fields = [100, 7, 2, 24, 2, 2, 0, 0, 32, 0, 32, 32, 8, 4,
              0x00ff0000, 0x0000ff00, 0x000000ff, 8, 256, 0,
              2, 2, 0, 0, 0]
    synthetic_base = struct.pack(">25I", *fields) + bytes(16)
    synthetic_changed = struct.pack(">25I", *fields) + bytes(12) + (1).to_bytes(4, "little")
    synthetic_diff = diff(parse_xwd(synthetic_base), parse_xwd(synthetic_changed))
    synthetic_detected = (synthetic_diff["count"] == 1 and synthetic_diff["bbox"] == [1, 1, 1, 1])
    if not synthetic_detected:
        errors.append("synthetic_changed_region_control_failed")
    candidate = json.loads((root / "candidate_decisions.json").read_text())
    if candidate.get("decisions") != decisions:
        errors.append("candidate_independent_decision_mismatch")
    if candidate.get("masks") != masks:
        errors.append("candidate_independent_mask_mismatch")
    if candidate.get("synthetic_positive_control") is not True:
        errors.append("candidate_synthetic_control_failed")
    calibration_paths = [p for item in masks.values() for p in item["calibration_paths"]]
    evaluated_paths = [d["path"] for d in decisions]
    if len(calibration_paths) + len(evaluated_paths) != len(rows) or \
       set(calibration_paths + evaluated_paths) != {r["path"] for r in rows}:
        errors.append("candidate_row_coverage")
    events = root / "target-events.jsonl"
    event_rows = events.read_text().splitlines() if events.exists() else []
    if event_rows or (root / "effect.json").exists():
        errors.append("target_input_or_effect_seen")
    if manifest.get("input_events") != 0 or manifest.get("target_operations") != 0:
        errors.append("manifest_input_boundary")
    if not live:
        cleanup_path = root / "cleanup.json"
        if not cleanup_path.exists():
            errors.append("cleanup_record_missing")
        else:
            cleanup = json.loads(cleanup_path.read_text())
            cleanup_roles = {x["role"] for x in cleanup}
            if cleanup_roles != {"target", "decoy", "xvfb"} or any(x["returncode"] is None for x in cleanup):
                errors.append("cleanup_incomplete")
            if next((x["returncode"] for x in cleanup if x["role"] == "xvfb"), None) != 0:
                errors.append("xvfb_cleanup_status")
            if any((Path("/proc") / str(pid)).exists() for pid in (target_pid, decoy_pid)):
                errors.append("fixture_process_leak")
    result = {"schema": "issue-4466-independent-audit-v1",
              "decision": "PASS_NO_INPUT_STABILITY_GATE_CALIBRATED" if not errors else "HOLD_NO_INPUT_STABILITY_GATE",
              "capture_rows": len(rows), "pre_decoy_rows": sum(r["phase"] == "pre_decoy" for r in rows),
              "post_decoy_rows": sum(r["phase"] == "post_decoy" for r in rows),
              "focus_context_counts": {str(k): len(v) for k, v in groups.items()},
              "stability_decisions": decisions, "calibrated_masks": masks,
              "decoy_target_pixel_difference": {"count": decoy_difference["count"],
                                                 "bbox": decoy_difference["bbox"]},
              "synthetic_changed_region_detected": synthetic_detected,
              "candidate_decisions_matched": candidate.get("decisions") == decisions,
              "target_events": len(event_rows), "effect_file_present": (root / "effect.json").exists(),
              "live_target": target_live, "live_decoy": decoy_live, "errors": errors}
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("root")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--output", default="AUDIT_RESULT.json")
    args = parser.parse_args()
    result = audit(args.root, args.live)
    (Path(args.root) / args.output).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True), flush=True)
    raise SystemExit(0 if not result["errors"] else 1)
