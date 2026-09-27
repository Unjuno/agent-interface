"""Independent raw-XWD auditor for Issue #4466; does not import the runner."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import sys

EXPECTED_ORDER = (
    [("target_only", "target", i) for i in range(1, 4)]
    + [("decoy_overlapping", role, i) for i in range(1, 4) for role in ("target", "decoy")]
    + [("decoy_moved", role, i) for i in range(1, 4) for role in ("target", "decoy")]
)
RGB_MASKS = (0xFF0000, 0x00FF00, 0x0000FF)


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def parse_xwd_bytes(data):
    if len(data) < 100:
        raise ValueError("short XWD")
    h = struct.unpack(">25I", data[:100])
    header_size, version = h[:2]
    width, height, byte_order, bpp, stride = h[4], h[5], h[7], h[11], h[12]
    ncolors, masks = h[19], h[14:17]
    offset = header_size + ncolors * 12
    if version != 7 or bpp not in (24, 32) or bpp % 8:
        raise ValueError("unsupported XWD header")
    if tuple(masks) != RGB_MASKS:
        raise ValueError("unexpected RGB masks")
    if stride < width * (bpp // 8) or offset + height * stride != len(data):
        raise ValueError("inconsistent XWD length/stride")
    order = "little" if byte_order == 0 else "big"
    nbytes = bpp // 8
    raw_pixels, rgb_pixels = [], []
    mask = masks[0] | masks[1] | masks[2]
    for y in range(height):
        for x in range(width):
            pos = offset + y * stride + x * nbytes
            raw = int.from_bytes(data[pos:pos + nbytes], order)
            raw_pixels.append(raw)
            rgb_pixels.append(raw & mask)
    rgb_serialized = b"".join(value.to_bytes(4, "little") for value in rgb_pixels)
    return {"width": width, "height": height, "depth": h[3], "bits_per_pixel": bpp,
            "bytes_per_line": stride, "rgb_masks": [hex(x) for x in masks],
            "raw_pixels": raw_pixels, "rgb_pixels": rgb_pixels,
            "rgb_colors": len(set(rgb_pixels)), "rgb_sha256": sha256_bytes(rgb_serialized),
            "file_sha256": sha256_bytes(data), "file_bytes": len(data)}


def changed_pixels(left, right, width):
    changed = [i for i, (a, b) in enumerate(zip(left, right)) if a != b]
    xy = [(i % width, i // width) for i in changed]
    bbox = None if not xy else [min(x for x, _ in xy), min(y for _, y in xy),
                                max(x for x, _ in xy), max(y for _, y in xy)]
    return len(changed), bbox


def comparison_report(left_row, right_row, left_img, right_img):
    count, bbox = changed_pixels(left_img["rgb_pixels"], right_img["rgb_pixels"], left_img["width"])
    raw_changed = sum(a != b for a, b in zip(left_img["raw_pixels"], right_img["raw_pixels"]))
    return {"left": left_row["artifact"], "right": right_row["artifact"],
            "left_file_sha256": left_img["file_sha256"], "right_file_sha256": right_img["file_sha256"],
            "left_rgb_sha256": left_img["rgb_sha256"], "right_rgb_sha256": right_img["rgb_sha256"],
            "changed_rgb_pixels": count, "changed_raw_pixel_values": raw_changed,
            "changed_ignored_bits_only": raw_changed - count, "bbox": bbox}


def validate_order(rows):
    actual = [(row.get("stage"), row.get("role"), row.get("index")) for row in rows]
    if actual != EXPECTED_ORDER:
        raise ValueError("capture count/order mismatch")


def synthetic_xwd(pixels, width, height):
    bpp = 32
    h = [100, 7, 2, 24, width, height, 0, 0, 32, 0, 32, bpp,
         width * 4, 4, RGB_MASKS[0], RGB_MASKS[1], RGB_MASKS[2], 8, 256, 0,
         width, height, 0, 0, 0]
    data = bytearray(struct.pack(">25I", *h))
    for value in pixels:
        data.extend(int(value).to_bytes(4, "little"))
    return bytes(data)


def run_self_test():
    rows = [{"stage": s, "role": r, "index": i} for s, r, i in EXPECTED_ORDER]
    validate_order(rows)
    for corrupted in (rows[:-1], rows[1:] + rows[:1]):
        try:
            validate_order(corrupted)
        except ValueError:
            pass
        else:
            raise AssertionError("capture order corruption was accepted")
    before = parse_xwd_bytes(synthetic_xwd([0x00112233, 0x00445566], 2, 1))
    padding_only = parse_xwd_bytes(synthetic_xwd([0xFF112233, 0x00445566], 2, 1))
    one_rgb_changed = parse_xwd_bytes(synthetic_xwd([0x00112234, 0x00445566], 2, 1))
    assert before["rgb_pixels"] == padding_only["rgb_pixels"]
    assert before["rgb_sha256"] == padding_only["rgb_sha256"]
    assert before["rgb_pixels"] != one_rgb_changed["rgb_pixels"]
    n, bbox = changed_pixels(before["rgb_pixels"], one_rgb_changed["rgb_pixels"], 2)
    assert (n, bbox) == (1, [0, 0, 0, 0])
    print(json.dumps({"self_test": "PASS", "capture_order_corruption_rejected": True,
                      "padding_only_change_ignored": True, "rgb_change_detected": True,
                      "changed_pixel_count": n, "bbox": bbox}, sort_keys=True))


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def parse_identity(snapshot):
    window = snapshot["window"]
    xprop, xwininfo = window["xprop"], window["xwininfo"]
    pid = re.search(r"_NET_WM_PID\(CARDINAL\) = (\d+)", xprop)
    title = re.search(r'WM_NAME\(STRING\) = "([^"]*)"', xprop)
    geom = {}
    for key, pattern in (("x", r"Absolute upper-left X:\s*(-?\d+)"),
                         ("y", r"Absolute upper-left Y:\s*(-?\d+)"),
                         ("width", r"Width:\s*(\d+)"),
                         ("height", r"Height:\s*(\d+)")):
        match = re.search(pattern, xwininfo)
        geom[key] = int(match.group(1)) if match else None
    return {"xid": int(window["xid"]), "pid": int(pid.group(1)) if pid else None,
            "title": title.group(1) if title else None, "geometry": geom,
            "viewable": "Map State: IsViewable" in xwininfo,
            "focus": window.get("input_focus_special"),
            "active_window": window.get("root_active_window")}


def source_audit(repo, freeze):
    results, errors = {}, []
    for rel, expected in freeze.get("source_sha256", {}).items():
        path = repo / rel
        if not path.is_file():
            results[rel] = {"present": False}
            errors.append("source_missing:" + rel)
            continue
        actual = sha256_bytes(path.read_bytes()).upper()
        results[rel] = {"present": True, "expected": expected, "actual": actual,
                        "match": actual == expected.upper()}
        if actual != expected.upper():
            errors.append("source_hash_mismatch:" + rel)
    return results, errors


def audit(evidence, repo, freeze_path):
    errors = []
    freeze = read_json(freeze_path)
    if freeze.get("schema") != "issue4466_gtk_visibility_freeze_v1":
        errors.append("freeze_schema")
    source_results, source_errors = source_audit(repo, freeze)
    errors.extend(source_errors)

    summary_path = evidence / "run-summary.json"
    cleanup_path = evidence / "cleanup.json"
    if not summary_path.is_file() or not cleanup_path.is_file():
        return {"decision": "STOP_EVIDENCE_MISSING", "errors": errors + ["summary_or_cleanup_missing"],
                "source_audit": source_results, "formal_2606_acceptance": False}
    summary, cleanup = read_json(summary_path), read_json(cleanup_path)
    if summary.get("allocation") != freeze.get("allocation"):
        errors.append("allocation_id")
    if summary.get("status") != "RUN_COMPLETED_PENDING_INDEPENDENT_AUDIT":
        errors.append("runner_status")
    if summary.get("model_calls") != 0 or summary.get("provider_calls") != 0:
        errors.append("model_or_provider_calls")
    if summary.get("input_emitter_processes") != []:
        errors.append("input_emitter_processes_not_empty")
    if summary.get("target_effect_exists") is not False or summary.get("target_events_exist") is not False:
        errors.append("target_effect_or_events_present")
    if (evidence / "target-effect.json").exists() or (evidence / "target-events.jsonl").exists():
        errors.append("target_effect_or_events_file_exists")

    rows = summary.get("captures", [])
    try:
        validate_order(rows)
    except ValueError as exc:
        errors.append(str(exc))
    capture_images = {}
    artifact_manifest = {}
    for row in rows:
        name = row.get("artifact", "")
        path = evidence / name
        if not path.is_file():
            errors.append("capture_missing:" + name)
            continue
        data = path.read_bytes()
        image = parse_xwd_bytes(data)
        artifact_manifest[name] = {"sha256": image["file_sha256"], "bytes": image["file_bytes"]}
        capture_images[name] = image
        for field, actual in (("sha256", image["file_sha256"]), ("bytes", image["file_bytes"]),
                              ("width", image["width"]), ("height", image["height"]),
                              ("rgb_sha256", image["rgb_sha256"]), ("rgb_colors", image["rgb_colors"])):
            if row.get(field) != actual:
                errors.append("capture_metadata_mismatch:" + name + ":" + field)
        if image["width"] != 400 or image["height"] != 180:
            errors.append("capture_geometry:" + name)

    target_by_stage = {}
    decoy_by_stage = {}
    for row in rows:
        (target_by_stage if row["role"] == "target" else decoy_by_stage).setdefault(row["stage"], []).append(row)
    repeated_comparisons = []
    for stage in ("target_only", "decoy_overlapping", "decoy_moved"):
        group = target_by_stage.get(stage, [])
        if len(group) != 3:
            errors.append("target_rows_per_stage:" + stage)
            continue
        for a, b in zip(group, group[1:]):
            ia, ib = capture_images.get(a["artifact"]), capture_images.get(b["artifact"])
            if ia is None or ib is None:
                continue
            comparison = comparison_report(a, b, ia, ib)
            comparison["stage"] = stage
            repeated_comparisons.append(comparison)
            if comparison["changed_rgb_pixels"] != 0:
                errors.append("within_stage_rgb_instability:" + stage)

    transitions = [("target_only", 2, "decoy_overlapping", 0),
                   ("decoy_overlapping", 2, "decoy_moved", 0)]
    transition_results = []
    for left_stage, left_i, right_stage, right_i in transitions:
        left_rows, right_rows = target_by_stage.get(left_stage, []), target_by_stage.get(right_stage, [])
        if len(left_rows) != 3 or len(right_rows) != 3:
            continue
        left_row, right_row = left_rows[left_i], right_rows[right_i]
        left_img, right_img = capture_images.get(left_row["artifact"]), capture_images.get(right_row["artifact"])
        if left_img is None or right_img is None:
            continue
        comparison = comparison_report(left_row, right_row, left_img, right_img)
        transition_results.append(comparison)
        if comparison["changed_rgb_pixels"] != 400 * 180 or comparison["bbox"] != [0, 0, 399, 179]:
            errors.append("transition_not_full_frame:" + left_stage + "->" + right_stage)

    baseline, overlap, restored = (target_by_stage.get(name, []) for name in
                                   ("target_only", "decoy_overlapping", "decoy_moved"))
    if len(baseline) == len(overlap) == len(restored) == 3:
        base_img = capture_images.get(baseline[0]["artifact"])
        restore_img = capture_images.get(restored[0]["artifact"])
        if base_img and any(capture_images.get(row["artifact"], {}).get("rgb_sha256") != base_img["rgb_sha256"]
                            for row in baseline[1:]):
            errors.append("baseline_rgb_hash_not_stable")
        if base_img and any(capture_images.get(row["artifact"], {}).get("rgb_sha256") != base_img["rgb_sha256"]
                            for row in restored):
            errors.append("restored_target_rgb_hash_mismatch")
        for row in overlap:
            image = capture_images.get(row["artifact"])
            if image and (image["rgb_colors"] != 1 or any(image["rgb_pixels"])):
                errors.append("overlapped_target_not_black:" + row["artifact"])
        if base_img and restore_img and base_img["rgb_sha256"] != restore_img["rgb_sha256"]:
            errors.append("target_not_restored_to_baseline")

    for stage in ("decoy_overlapping", "decoy_moved"):
        group = decoy_by_stage.get(stage, [])
        if len(group) != 3:
            errors.append("decoy_rows_per_stage:" + stage)
        for row in group:
            image = capture_images.get(row["artifact"])
            if image and image["rgb_colors"] <= 1:
                errors.append("decoy_has_no_visible_content:" + row["artifact"])

    snapshots = summary.get("state_snapshots", [])
    state_by_stage = {item.get("stage"): item for item in snapshots}
    if [item.get("stage") for item in snapshots] != ["target_only", "decoy_overlapping", "decoy_moved"]:
        errors.append("state_snapshot_order")
    identities = {}
    for stage in ("target_only", "decoy_overlapping", "decoy_moved"):
        item = state_by_stage.get(stage, {})
        for role in ("target", "decoy") if stage != "target_only" else ("target",):
            snapshot = item.get(role)
            if not snapshot:
                errors.append("state_snapshot_missing:" + stage + ":" + role)
                continue
            identity = parse_identity(snapshot)
            identities[(stage, role)] = identity
            if identity["pid"] is None or identity["title"] != "AgentInterfaceGtkFixture":
                errors.append("identity_invalid:" + stage + ":" + role)
            if not identity["viewable"]:
                errors.append("window_not_viewable:" + stage + ":" + role)
            expected_xy = {"target_only": (0, 0), "decoy_overlapping": (0, 0),
                           "decoy_moved": ((400, 0) if role == "decoy" else (0, 0))}[stage]
            geom = identity["geometry"]
            if (geom["x"], geom["y"], geom["width"], geom["height"]) != (*expected_xy, 400, 180):
                errors.append("window_geometry_mismatch:" + stage + ":" + role)
    if identities:
        target_id = identities.get(("decoy_overlapping", "target"))
        decoy_id = identities.get(("decoy_overlapping", "decoy"))
        if target_id and decoy_id and (target_id["xid"] == decoy_id["xid"] or target_id["pid"] == decoy_id["pid"]):
            errors.append("decoy_identity_not_distinct")
        if target_id and decoy_id and target_id["title"] != decoy_id["title"]:
            errors.append("window_titles_not_matching")
        target_ids = {identities.get((stage, "target"), {}).get("xid")
                      for stage in ("target_only", "decoy_overlapping", "decoy_moved")}
        target_pids = {identities.get((stage, "target"), {}).get("pid")
                       for stage in ("target_only", "decoy_overlapping", "decoy_moved")}
        decoy_ids = {identities.get((stage, "decoy"), {}).get("xid")
                     for stage in ("decoy_overlapping", "decoy_moved")}
        decoy_pids = {identities.get((stage, "decoy"), {}).get("pid")
                      for stage in ("decoy_overlapping", "decoy_moved")}
        if len(target_ids) != 1 or len(target_pids) != 1:
            errors.append("target_identity_not_stable")
        if len(decoy_ids) != 1 or len(decoy_pids) != 1:
            errors.append("decoy_identity_not_stable")

    move = summary.get("decoy_reposition", {})
    if move != {"xid": summary.get("decoy_xid"), "requested_x": 400, "requested_y": 0,
                "stack_mode": "Above", "display_sync_completed": True}:
        errors.append("decoy_reposition_receipt")
    if summary.get("target_xid") != (identities.get(("decoy_overlapping", "target")) or {}).get("xid"):
        errors.append("target_xid_mismatch")
    if summary.get("decoy_xid") != (identities.get(("decoy_overlapping", "decoy")) or {}).get("xid"):
        errors.append("decoy_xid_mismatch")

    process_by_role = {row.get("role"): row for row in cleanup if row.get("returncode") is not None}
    if set(process_by_role) != {"target", "decoy", "xvfb"}:
        errors.append("cleanup_process_roles")
    if process_by_role.get("xvfb", {}).get("returncode") != 0:
        errors.append("xvfb_cleanup")
    if len(cleanup) != 3:
        errors.append("cleanup_count")
    for role, stage, identity_role in (("target", "decoy_overlapping", "target"),
                                       ("decoy", "decoy_overlapping", "decoy")):
        row = process_by_role.get(role)
        identity = identities.get((stage, identity_role))
        if row and identity and row.get("pid") != identity["pid"]:
            errors.append("cleanup_pid_mismatch:" + role)

    for path in sorted(evidence.rglob("*")):
        if path.is_file() and path.name not in ("audit.json",):
            artifact_manifest[str(path.relative_to(evidence)).replace("\\", "/")] = {
                "sha256": sha256_bytes(path.read_bytes()), "bytes": path.stat().st_size}
    decision = "PASS_NO_INPUT_STABILITY_GATE_CALIBRATED" if not errors else "HOLD_NO_INPUT_STABILITY_UNRESOLVED"
    identity_report = {stage + "/" + role: value
                       for (stage, role), value in identities.items()}
    return {"decision": decision, "scope": "posthoc audit v2 of the single frozen #4466 allocation",
            "allocation": summary.get("allocation"), "expected_capture_count": len(EXPECTED_ORDER),
            "actual_capture_count": len(rows), "repeated_target_comparisons": repeated_comparisons,
            "stage_transition_comparisons": transition_results, "identities": identity_report,
            "cleanup": cleanup, "source_audit": source_results, "errors": errors,
            "artifact_manifest": artifact_manifest, "model_calls": 0, "provider_calls": 0,
            "formal_2606_acceptance": False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence", nargs="?", type=Path)
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--freeze", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        run_self_test()
        return
    if args.evidence is None or args.freeze is None or args.out is None:
        parser.error("evidence, --freeze and --out are required unless --self-test is selected")
    result = audit(args.evidence.resolve(), args.repo.resolve(), args.freeze.resolve())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    if result["errors"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
