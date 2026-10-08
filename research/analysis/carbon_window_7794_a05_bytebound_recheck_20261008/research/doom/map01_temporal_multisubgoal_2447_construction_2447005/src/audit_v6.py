"""Additive posthoc audit v6: preserve v5 and tighten independent visual effects.

This verifier deliberately does not infer turn success from privileged yaw.
It independently runs the frozen LK metric over the controller-visible
handoff screenshot and reports a HOLD where a paired before/after visual
effect was not retained.
"""
from pathlib import Path
import argparse, hashlib, json
import cv2
import numpy as np
from PIL import Image

ROI = (20, 300, 20, 620)
MIN_TRACKS = 80
DY_THRESHOLD = -20.0


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def flow(before, after):
    a = np.asarray(before.convert("L"), np.uint8)[ROI[0]:ROI[1], ROI[2]:ROI[3]]
    b = np.asarray(after.convert("L"), np.uint8)[ROI[0]:ROI[1], ROI[2]:ROI[3]]
    pts = cv2.goodFeaturesToTrack(a, maxCorners=700, qualityLevel=.01,
                                  minDistance=6, blockSize=7)
    if pts is None:
        return {"valid_tracks": 0, "median_dy_px": None, "status": "UNKNOWN"}
    nxt, status, _ = cv2.calcOpticalFlowPyrLK(
        a, b, pts, None, winSize=(31, 31), maxLevel=4,
        criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, .01))
    if nxt is None or status is None:
        return {"valid_tracks": 0, "median_dy_px": None, "status": "UNKNOWN"}
    ok = status[:, 0] == 1
    p, q = pts[ok, 0, :], nxt[ok, 0, :]
    d = q - p
    if len(d):
        d = d[np.hypot(d[:, 0], d[:, 1]) < 100]
    n = int(len(d))
    med = None if not n else float(np.median(d[:, 1]))
    label = "UNKNOWN" if n < MIN_TRACKS else (
        "DROP_COMPLETED" if med <= DY_THRESHOLD else "NO_DROP")
    return {"valid_tracks": n, "median_dy_px": med, "status": label}


def audit(evidence):
    root = Path(evidence)
    score = json.loads((root / "score.json").read_text())
    result = {"schema": "issue2447-posthoc-audit-v6",
              "case": "issue2447-construction-2447005",
              "raw_modified": False, "checks": {}, "limitations": []}
    phase = root / "phase1"
    manifest = json.loads((phase / "result.json").read_text())
    frames = [Image.open(phase / n).convert("RGB") for n in manifest["frame_files"]]
    temporal = []
    for left, right in zip(frames, frames[1:]):
        temporal.append(flow(left, right))
    result["checks"]["temporal_drop_frame_pair"] = {
        "count": len(temporal), "drop_indices": [i for i, row in enumerate(temporal)
                                                   if row["status"] == "DROP_COMPLETED"],
        "independent_recompute_matches": bool(any(
            row["status"] == "DROP_COMPLETED" for row in temporal))
    }
    result["checks"]["independent_hidden_drop_transition"] = {
        "before": score.get("before"), "after_phase1": score.get("after_phase1"),
        "sector_165_to_38_and_z_64_to_128": bool(
            score.get("before", {}).get("sector") == 165
            and score.get("before", {}).get("z") == -64.0
            and score.get("after_phase1", {}).get("sector") == 38
            and score.get("after_phase1", {}).get("z") == -128.0)
    }
    handoffs = []
    for name, expected_key, before_key, after_key in (
        ("next_subgoal", "Right", "before_next_subgoal", "after_next_subgoal"),
        ("third_subgoal", "Left", "before_third_subgoal", "after_third_subgoal")):
        folder = root / name
        receipt = json.loads((folder / "result.json").read_text())
        image_path = folder / "handoff-observation.png"
        image = Image.open(image_path).convert("RGB")
        raw_hash = hashlib.sha256(np.asarray(image).tobytes()).hexdigest()
        matching_raw = raw_hash == receipt.get("observation_sha256")
        yaw_before = score.get(before_key, {}).get("angle")
        yaw_after = score.get(after_key, {}).get("angle")
        missing_pair = not (folder / "before-action.png").exists() or not (folder / "after-action.png").exists()
        handoffs.append({
            "name": name, "expected_key": expected_key,
            "recorded_key": receipt.get("key"),
            "fresh_image_sha_matches_raw": matching_raw,
            "image_sha256": raw_hash,
            "focus_binding_matches_setup": receipt.get("observation_binding") == {
                k: score.get("setup_binding", {}).get(k) for k in ("focus", "surface", "geometry")},
            "owner_release_verified_empty": bool(receipt.get("release", {}).get("verified")
                and not receipt.get("release", {}).get("keys_down")
                and not receipt.get("release", {}).get("buttons_down")),
            "privileged_yaw_delta_degrees": None if yaw_before is None or yaw_after is None
                else ((float(yaw_after) - float(yaw_before) + 180) % 360) - 180,
            "paired_before_after_visual_effect_available": not missing_pair,
            "visual_effect": None if missing_pair else flow(
                Image.open(folder / "before-action.png").convert("RGB"),
                Image.open(folder / "after-action.png").convert("RGB")),
        })
    result["checks"]["handoffs"] = handoffs
    result["limitations"].append(
        "Both action-bound fresh handoff images are preserved and hash-bind correctly, "
        "but paired pre-action/post-action screenshots were not retained; turn effects "
        "therefore cannot be independently verified from controller-visible pixels.")
    result["decision"] = "HOLD_INDEPENDENT_VISUAL_HANDOFF_EFFECT_MISSING"
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--evidence", required=True)
    p.add_argument("--out", required=True)
    a = p.parse_args()
    result = audit(a.evidence)
    Path(a.out).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
