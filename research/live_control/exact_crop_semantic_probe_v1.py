"""No-authority exact RGB crop predicate over a reconstructed frame."""
import copy
import hashlib
from pathlib import Path

import numpy as np

try:
    from .inkscape_selection_frame_probe_v1 import frame_sha256, load_exact_frame
except ImportError:
    from inkscape_selection_frame_probe_v1 import frame_sha256, load_exact_frame


CONTRACT_SCHEMA = "exact-rgb-crop-semantic-probe-v1"
SCORE_SCHEMA = "exact-rgb-crop-semantic-score-v1"
RECONCILIATION_SCHEMA = "exact-crop-artifact-reconciliation-v1"
FIELDS = {"schema", "probe_id", "box", "expected_crop_sha256",
          "success_reason", "grants_input_authority"}


def validate(contract):
    if type(contract) is not dict or set(contract) != FIELDS:
        raise ValueError("exact crop probe fields required")
    if contract["schema"] != CONTRACT_SCHEMA:
        raise ValueError("exact crop probe schema required")
    if not isinstance(contract["probe_id"], str) or not 1 <= len(contract["probe_id"]) <= 64:
        raise ValueError("bounded probe_id required")
    box = contract["box"]
    if type(box) is not list or len(box) != 4 or any(type(value) is not int for value in box):
        raise ValueError("integer [left,top,right,bottom] box required")
    if not (0 <= box[0] < box[2] and 0 <= box[1] < box[3] and
            (box[2]-box[0])*(box[3]-box[1]) <= 65536):
        raise ValueError("bounded nonempty crop required")
    digest = contract["expected_crop_sha256"]
    if (not isinstance(digest, str) or len(digest) != 64 or
            any(char not in "0123456789abcdef" for char in digest)):
        raise ValueError("lowercase SHA-256 required")
    if not isinstance(contract["success_reason"], str) or not contract["success_reason"]:
        raise ValueError("success_reason required")
    if contract["grants_input_authority"] is not False:
        raise ValueError("probe must grant no input authority")
    return copy.deepcopy(contract)


def score_frame(contract, frame):
    contract = validate(contract)
    if frame.mode != "RGB" or len(frame.pixels) != frame.width*frame.height*3:
        raise ValueError("valid RGB exact frame required")
    left, top, right, bottom = contract["box"]
    if right > frame.width or bottom > frame.height:
        raise ValueError("crop outside exact frame")
    pixels = np.frombuffer(frame.pixels, dtype=np.uint8).reshape(frame.height, frame.width, 3)
    observed = hashlib.sha256(pixels[top:bottom, left:right].tobytes()).hexdigest()
    success = observed == contract["expected_crop_sha256"]
    return {"schema": SCORE_SCHEMA, "probe_id": contract["probe_id"],
        "success": success,
        "reason": contract["success_reason"] if success else "expected_crop_missing",
        "box": list(contract["box"]), "observed_crop_sha256": observed,
        "expected_crop_sha256": contract["expected_crop_sha256"],
        "scored_frame_sha256": frame_sha256(frame),
        "frame": {"width": frame.width, "height": frame.height, "mode": frame.mode},
        "grants_input_authority": False}


def score_path(contract, image_path):
    return score_frame(contract, load_exact_frame(image_path))


def reconcile_artifact(result, image_path):
    if (type(result) is not dict or result.get("schema") != SCORE_SCHEMA or
            result.get("grants_input_authority") is not False):
        raise ValueError("exact no-authority crop result required")
    path = Path(image_path)
    artifact_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
    artifact_frame_sha256 = frame_sha256(load_exact_frame(path))
    matches = artifact_frame_sha256 == result["scored_frame_sha256"]
    return {"schema": RECONCILIATION_SCHEMA,
        "status": "MATCHED_EXACT_FRAME" if matches else "REJECTED_FRAME_MISMATCH",
        "scored_frame_sha256": result["scored_frame_sha256"],
        "artifact_frame_sha256": artifact_frame_sha256,
        "artifact_sha256": artifact_sha256, "matches": matches,
        "grants_input_authority": False}
