#!/usr/bin/env python3
"""Independent raw-only reconstruction for retained Issue #2447 case 2447008."""
from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image


def main(root: Path, output: Path) -> int:
    errors: list[str] = []
    phase = root / "phase_recheck"
    result = json.loads((phase / "result.json").read_text(encoding="utf-8"))
    image_paths = [phase / name for name in result["frame_files"]]
    times = result["frame_capture_start_ns"]
    pairs = []
    for i, (left_path, right_path) in enumerate(zip(image_paths, image_paths[1:])):
        left = np.asarray(Image.open(left_path).convert("L"), dtype=np.uint8)[20:300, 20:620]
        right = np.asarray(Image.open(right_path).convert("L"), dtype=np.uint8)[20:300, 20:620]
        points = cv2.goodFeaturesToTrack(left, maxCorners=700, qualityLevel=.01,
                                         minDistance=6, blockSize=7)
        if points is None:
            count, median_dy = 0, None
        else:
            moved, status, _ = cv2.calcOpticalFlowPyrLK(
                left, right, points, None, winSize=(31, 31), maxLevel=4,
                criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, .01))
            if moved is None or status is None:
                count, median_dy = 0, None
            else:
                delta = moved[status[:, 0] == 1, 0, :] - points[status[:, 0] == 1, 0, :]
                delta = delta[np.hypot(delta[:, 0], delta[:, 1]) < 100]
                count = int(len(delta))
                median_dy = float(statistics.median(delta[:, 1])) if count >= 80 else None
        gap_ms = (times[i + 1] - times[i]) / 1_000_000
        eligible = gap_ms <= 100 and median_dy is not None
        pairs.append({"pair": i, "gap_ms": gap_ms, "tracks": count,
                      "median_dy_px": median_dy, "eligible": eligible,
                      "drop": bool(eligible and median_dy <= -20)})

    eligible_pairs = [p for p in pairs if p["eligible"]]
    reconstructed = ("DROP_COMPLETED" if any(p["drop"] for p in eligible_pairs)
                     else "NO_DROP" if eligible_pairs else "UNKNOWN")
    if reconstructed != "NO_DROP" or reconstructed != result.get("status"):
        errors.append("phase_status_mismatch")
    if sum(p["eligible"] for p in pairs) != 1:
        errors.append("eligible_pair_count_mismatch")
    if any(p["drop"] for p in pairs):
        errors.append("drop_signal_found")
    if result.get("input_emissions") != 0:
        errors.append("observer_input_not_zero")

    release_records = []
    for name in ("setup-owner-records.json", "phase1/owner-records.json",
                 "phase2/owner-records.json"):
        path = root / name
        if path.exists():
            release_records += [r for r in json.loads(path.read_text(encoding="utf-8"))
                                if r.get("event") == "owner_release"]
    all_empty = bool(release_records) and all(
        r.get("verified") is True and not r.get("keys_down") and not r.get("buttons_down")
        for r in release_records)
    if len(release_records) != 33 or not all_empty:
        errors.append("release_reconstruction_mismatch")

    report = {"schema": "issue2447-2447008-independent-raw-audit-v1",
              "decision": "PASS_RECONSTRUCTION_ONLY" if not errors else "HOLD_RECONSTRUCTION",
              "errors": errors, "reported_status": result.get("status"),
              "reconstructed_status": reconstructed, "pairs": pairs,
              "eligible_pair_count": len(eligible_pairs),
              "observer_input_emissions": result.get("input_emissions"),
              "release_count": len(release_records), "all_releases_verified_empty": all_empty,
              "formal_rows": 0, "retries": 0,
              "scope": "Independent code reanalysis of retained raw frames/logs only; not a new GUI allocation, fault-rate estimate, comparative result, or Issue #2447 acceptance."}
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1]), Path(sys.argv[2])))

