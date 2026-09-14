"""Verify a click-free animated placement preview by its stable change mask."""
import hashlib
from pathlib import Path

from PIL import Image, ImageChops


def crop(path, box):
    with Image.open(path) as opened:
        return opened.convert("RGB").crop(tuple(box))


def mask_against(base, observed):
    difference = ImageChops.difference(base, observed)
    mask = bytes(1 if pixel != (0, 0, 0) else 0 for pixel in difference.getdata())
    return mask, sum(mask)


def verify(records, steps, point, box, runtime_dir, baseline_image):
    expected = [{"op": "pointer_move", "x": point[0], "y": point[1]},
                {"op": "settle", "quiet_ms": 100, "timeout_ms": 1200},
                {"op": "observe"}]
    if steps != expected:
        raise ValueError("world hover program mismatch")
    admissions = [row for row in records if row.get("event") == "pointer_admission"]
    if [(row.get("step"), row.get("operation"), row.get("payload")) for row in admissions] != [
            (0, "move", {"x": point[0], "y": point[1]})]:
        raise ValueError("world receipt must contain one bound move and no button input")
    settles = [row for row in records if row.get("event") == "settle_result"]
    if len(settles) != 1 or settles[0].get("reason") not in ("pixel_quiet", "timeout"):
        raise ValueError("bounded settle result required")
    observations = [row for row in records if row.get("event") == "observation" and row.get("step") in (1, 2)]
    if len(observations) < 4 or not any(row.get("step") == 2 for row in observations):
        raise ValueError("multi-frame dwell and persistent observation required")
    binding = observations[0].get("pointer_binding")
    if binding is None or any(row.get("pointer_binding") != binding or row.get("focus_samples_match") is not True
                              for row in observations):
        raise ValueError("world preview binding or focus changed")
    runtime_dir = Path(runtime_dir); base = crop(baseline_image, box)
    mask_hashes = []; changed_counts = []; frame_hashes = []
    for row in observations:
        observed = crop(runtime_dir / Path(row["image"]).name, box)
        mask, count = mask_against(base, observed)
        mask_hashes.append(hashlib.sha256(mask).hexdigest()); changed_counts.append(count)
        frame_hashes.append(hashlib.sha256(observed.tobytes()).hexdigest())
    if len(set(mask_hashes)) != 1 or min(changed_counts) < 1000:
        raise ValueError("animated placement preview lacks a stable bounded change mask")
    last = observations[-1]; last_crop = crop(runtime_dir / Path(last["image"]).name, box)
    receipt = {"receipt_index": 1, "point": point,
        "dwell_sequences": [row["sequence"] for row in observations],
        "last_image": Path(last["image"]).name,
        "evidence": {"box": box, "size": list(last_crop.size),
            "changed_pixels_each_frame": changed_counts, "stable_mask_sha256": mask_hashes[0],
            "last_pixels_sha256": hashlib.sha256(last_crop.tobytes()).hexdigest(),
            "distinct_frame_crops": len(set(frame_hashes)), "settle_reason": settles[0]["reason"]},
        "authority": "animated observation evidence only; grants no input authority"}
    return {"status": "READY", "binding": binding, "receipts": [receipt],
            "authority": "composed world-preview evidence only; grants no input authority"}
