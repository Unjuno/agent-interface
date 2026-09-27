"""Candidate no-input stability gate, separate from the independent auditor."""
import collections
import json
from pathlib import Path

from xwd_pixels import changed_pixels, read_xwd, volatile_mask, volatile_pixels


def evaluate_capture_rows(root, rows, schedule):
    groups = collections.defaultdict(list)
    images = {}
    for row in rows:
        raw = (Path(root) / row["path"]).read_bytes()
        images[row["path"]] = read_xwd(raw)
        groups[row["identity_before"]["focus_xid"]].append(row)
    decisions = []
    masks = {}
    n = schedule["baseline_captures_per_focus_context"]
    for focus, group in groups.items():
        if len(group) < n:
            decisions.extend({"path": r["path"], "focus_xid": focus,
                              "decision": "REBASELINE_INCOMPLETE_CONTEXT"} for r in group)
            continue
        baseline_rows = group[:n]
        baseline_images = [images[r["path"]] for r in baseline_rows]
        raw_volatile = volatile_pixels(baseline_images)
        raw_coords = sorted([list(p) for p in raw_volatile], key=lambda p: (p[1], p[0]))
        if raw_coords:
            raw_bbox = [min(x for x, _ in raw_coords), min(y for _, y in raw_coords),
                        max(x for x, _ in raw_coords), max(y for _, y in raw_coords)]
        else:
            raw_bbox = None
        mask = volatile_mask(baseline_images, schedule["volatile_mask_halo_px"])
        masks[str(focus)] = {"volatile_pixel_count_with_halo": len(mask),
                             "raw_volatile_pixel_count": len(raw_volatile),
                             "raw_volatile_bbox": raw_bbox,
                             "raw_volatile_coords": raw_coords,
                             "calibration_paths": [r["path"] for r in baseline_rows]}
        reference = baseline_images[0]
        for row in group[n:]:
            delta = changed_pixels(reference, images[row["path"]])
            outside = [(x, y) for x, y in delta["coords"] if (x, y) not in mask]
            if outside:
                bbox = [min(x for x, _ in outside), min(y for _, y in outside),
                        max(x for x, _ in outside), max(y for _, y in outside)]
            else:
                bbox = None
            decisions.append({"path": row["path"], "focus_xid": focus,
                              "decision": "STABLE_WITHIN_CALIBRATED_MASK" if not outside
                                         else "FAIL_UNCALIBRATED_PIXEL_CHANGE",
                              "changed_pixel_count": delta["count"],
                              "changed_bbox": delta["bbox"],
                              "outside_mask_count": len(outside),
                              "outside_mask_bbox": bbox})
    decisions.sort(key=lambda d: next(i for i, r in enumerate(rows) if r["path"] == d["path"]))
    return {"algorithm": "per-focus first-8 baseline; union changed pixels dilated by 1px; compare subsequent images to baseline[0]",
            "decisions": decisions, "masks": masks}


def synthetic_positive_control():
    """A valid two-by-two synthetic XWD with one changed pixel must be detected."""
    import struct
    fields = [100, 7, 2, 24, 2, 2, 0, 0, 32, 0, 32, 32, 8, 4,
              0x00ff0000, 0x0000ff00, 0x000000ff, 8, 256, 0,
              2, 2, 0, 0, 0]
    baseline = struct.pack(">25I", *fields) + bytes(16)
    changed = struct.pack(">25I", *fields) + bytes(12) + (1).to_bytes(4, "little")
    return changed_pixels(read_xwd(baseline), read_xwd(changed)) == {
        "count": 1, "bbox": [1, 1, 1, 1], "coords": [(1, 1)]}


def main(root):
    root = Path(root)
    manifest = json.loads((root / "manifest.json").read_text())
    rows = [json.loads(line) for line in (root / "captures.jsonl").read_text().splitlines()]
    result = evaluate_capture_rows(root, rows, manifest["schedule"])
    result["synthetic_positive_control"] = synthetic_positive_control()
    (root / "candidate_decisions.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    return result


if __name__ == "__main__":
    import sys
    print(json.dumps(main(sys.argv[1]), sort_keys=True))
