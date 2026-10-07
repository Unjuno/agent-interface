"""Fast no-authority selection probe over an already reconstructed exact frame."""
import hashlib
import struct
from collections import namedtuple
from pathlib import Path

import numpy as np
from PIL import Image


SCHEMA = "inkscape-visible-selection-frame-probe-v1"
RECONCILIATION_SCHEMA = "exact-frame-artifact-reconciliation-v1"
ExactFrame = namedtuple("ExactFrame", "width height mode pixels")


def frame_sha256(frame):
    header = b"AIFR1\0" + frame.mode.encode("ascii") + b"\0" + struct.pack(
        "!II", frame.width, frame.height)
    return hashlib.sha256(header + frame.pixels).hexdigest()


def _validate_plan(plan):
    if (type(plan) is not dict or
            plan.get("schema") != "inkscape-red-target-plan-v1" or
            plan.get("grants_input_authority") is not False):
        raise ValueError("exact no-authority source plan required")


def _rgb(frame):
    if frame.mode != "RGB":
        raise ValueError("RGB exact frame required")
    expected = frame.width * frame.height * 3
    if len(frame.pixels) != expected:
        raise ValueError("invalid exact frame byte length")
    return np.frombuffer(frame.pixels, dtype=np.uint8).reshape(
        frame.height, frame.width, 3)


def score_frame(plan, frame, *, edge_tolerance=1, coverage_minimum=0.8,
                expansion=18, per_side_minimum=10):
    _validate_plan(plan)
    pixels = _rgb(frame)
    left, top, right, bottom = plan["roi"]
    if not (0 <= left < right <= frame.width and
            0 <= top < bottom <= frame.height):
        raise ValueError("ROI outside exact frame")
    roi = pixels[top:bottom, left:right]
    red = (roi[:, :, 0] >= 240) & (roi[:, :, 1] <= 20) & (roi[:, :, 2] <= 20)
    ys, xs = np.nonzero(red)
    support = None if len(xs) == 0 else {
        "bbox": [int(xs.min()) + left, int(ys.min()) + top,
                 int(xs.max()) + left + 1, int(ys.max()) + top + 1],
        "red_pixels": int(len(xs)),
    }
    expected = plan["target"]
    expected_box = expected["bbox"]
    edge_delta = None if support is None else [
        support["bbox"][index] - expected_box[index] for index in range(4)]
    coverage = 0 if support is None else support["red_pixels"] / expected["red_pixels"]
    identity = (support is not None and
                all(abs(value) <= edge_tolerance for value in edge_delta) and
                coverage_minimum <= coverage <= 1.05)
    left, top, right, bottom = expected_box
    zones = {
        "left": [left-expansion, top-expansion, left, bottom+expansion],
        "right": [right, top-expansion, right+expansion, bottom+expansion],
        "top": [left, top-expansion, right, top],
        "bottom": [left, bottom, right, bottom+expansion],
    }
    if any(not (0 <= box[0] < box[2] <= frame.width and
                    0 <= box[1] < box[3] <= frame.height)
           for box in zones.values()):
        raise ValueError("selection zone outside exact frame")
    counts = {}
    for name, box in zones.items():
        zone = pixels[box[1]:box[3], box[0]:box[2]]
        counts[name] = int(np.count_nonzero(np.max(zone, axis=2) <= 50))
    handles = all(value >= per_side_minimum for value in counts.values())
    success = bool(identity and handles)
    return {
        "schema": SCHEMA,
        "success": success,
        "reason": ("target_identity_and_selection_handles_visible" if success else
                   "target_identity_changed" if not identity else
                   "selection_handles_missing"),
        "source_image_sha256": plan["source_image_sha256"],
        "scored_frame_sha256": frame_sha256(frame),
        "frame": {"width": frame.width, "height": frame.height, "mode": frame.mode},
        "expected_target": expected,
        "observed_support": support,
        "edge_delta": edge_delta,
        "red_coverage_ratio": coverage,
        "edge_tolerance": edge_tolerance,
        "coverage_minimum": coverage_minimum,
        "zones": zones,
        "dark_pixels": counts,
        "per_side_minimum": per_side_minimum,
        "target_identity_valid": bool(identity),
        "selection_handles_visible": bool(handles),
        "grants_input_authority": False,
    }


def load_exact_frame(image_path):
    with Image.open(image_path) as source:
        image = source.convert("RGB")
        return ExactFrame(image.width, image.height, image.mode, image.tobytes())


def reconcile_artifact(result, image_path):
    if (type(result) is not dict or result.get("schema") != SCHEMA or
            result.get("grants_input_authority") is not False):
        raise ValueError("exact no-authority frame result required")
    path = Path(image_path)
    artifact_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
    observed_frame_sha256 = frame_sha256(load_exact_frame(path))
    matches = observed_frame_sha256 == result["scored_frame_sha256"]
    return {
        "schema": RECONCILIATION_SCHEMA,
        "status": "MATCHED_EXACT_FRAME" if matches else "REJECTED_FRAME_MISMATCH",
        "scored_frame_sha256": result["scored_frame_sha256"],
        "artifact_frame_sha256": observed_frame_sha256,
        "artifact_sha256": artifact_sha256,
        "matches": matches,
        "grants_input_authority": False,
    }
