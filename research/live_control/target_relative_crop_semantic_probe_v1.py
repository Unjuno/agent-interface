"""No-authority exact crop predicate bound to current surface geometry."""
import copy
import hashlib
from pathlib import Path

import numpy as np

try:
    from .coordinate_frame_transform_v1 import translation
    from .inkscape_selection_frame_probe_v1 import frame_sha256, load_exact_frame
except ImportError:
    from coordinate_frame_transform_v1 import translation
    from inkscape_selection_frame_probe_v1 import frame_sha256, load_exact_frame


CONTRACT_SCHEMA = "target-relative-rgb-crop-semantic-probe-v1"
SCORE_SCHEMA = "target-relative-rgb-crop-semantic-score-v1"
RECONCILIATION_SCHEMA = "target-relative-crop-artifact-reconciliation-v1"
FIELDS = {"schema", "probe_id", "target_reference", "coordinate_frame",
          "source_surface", "source_geometry", "box_in_frame",
          "expected_crop_sha256", "success_reason", "allowed_transformations",
          "grants_input_authority"}


def _geometry(value):
    translation("window_content", value, value)
    return list(value)


def validate(contract):
    if type(contract) is not dict or set(contract) != FIELDS:
        raise ValueError("exact target-relative probe fields required")
    if contract["schema"] != CONTRACT_SCHEMA:
        raise ValueError("target-relative probe schema required")
    for name in ("probe_id", "target_reference"):
        if not isinstance(contract[name], str) or not 1 <= len(contract[name]) <= 128:
            raise ValueError("bounded identifiers required")
    if contract["coordinate_frame"] != "window_content":
        raise ValueError("window_content frame required")
    if type(contract["source_surface"]) is not int or contract["source_surface"] in (0, 1):
        raise ValueError("source surface identifier required")
    geometry = _geometry(contract["source_geometry"])
    box = contract["box_in_frame"]
    if type(box) is not list or len(box) != 4 or any(type(value) is not int for value in box):
        raise ValueError("integer half-open box_in_frame required")
    left, top, right, bottom = box
    if not (0 <= left < right <= geometry[2] and 0 <= top < bottom <= geometry[3]
            and (right-left)*(bottom-top) <= 65536):
        raise ValueError("bounded box inside source surface required")
    digest = contract["expected_crop_sha256"]
    if (not isinstance(digest, str) or len(digest) != 64 or
            any(char not in "0123456789abcdef" for char in digest)):
        raise ValueError("lowercase SHA-256 required")
    if not isinstance(contract["success_reason"], str) or not contract["success_reason"]:
        raise ValueError("success_reason required")
    if contract["allowed_transformations"] != ["window_translation"]:
        raise ValueError("only window_translation may be allowed")
    if contract["grants_input_authority"] is not False:
        raise ValueError("probe must grant no input authority")
    return copy.deepcopy(contract)


def _binding_status(contract, binding):
    if (type(binding) is not dict or set(binding) != {"focus", "surface", "geometry"} or
            type(binding.get("focus")) is not int or binding.get("focus") in (0, 1) or
            type(binding.get("surface")) is not int or binding.get("surface") in (0, 1)):
        return "current_binding_unavailable", None
    try:
        current = _geometry(binding["geometry"])
    except ValueError:
        return "current_binding_unavailable", None
    if binding["surface"] != contract["source_surface"]:
        return "surface_changed", None
    source = contract["source_geometry"]
    if current[2:] != source[2:]:
        return "surface_size_changed", None
    delta = translation(contract["coordinate_frame"], source, current)
    left, top, right, bottom = contract["box_in_frame"]
    resolved = [current[0]+left, current[1]+top,
                current[0]+right, current[1]+bottom]
    return "CURRENT_TRANSLATED" if delta != [0, 0] else "CURRENT_EXACT", {
        "translation": delta, "resolved_box": resolved, "current_geometry": current}


def score_frame(contract, frame, binding):
    contract = validate(contract)
    if frame.mode != "RGB" or len(frame.pixels) != frame.width*frame.height*3:
        raise ValueError("valid RGB exact frame required")
    binding_status, resolution = _binding_status(contract, binding)
    observed = None; success = False
    if resolution is not None:
        left, top, right, bottom = resolution["resolved_box"]
        if not (0 <= left < right <= frame.width and 0 <= top < bottom <= frame.height):
            binding_status = "resolved_crop_outside_frame"; resolution = None
        else:
            pixels = np.frombuffer(frame.pixels, dtype=np.uint8).reshape(
                frame.height, frame.width, 3)
            observed = hashlib.sha256(
                pixels[top:bottom, left:right].tobytes()).hexdigest()
            success = observed == contract["expected_crop_sha256"]
    reason = (contract["success_reason"] if success else
              "expected_crop_missing" if observed is not None else binding_status)
    return {"schema": SCORE_SCHEMA, "probe_id": contract["probe_id"],
        "target_reference": contract["target_reference"], "success": success,
        "reason": reason, "binding_status": binding_status,
        "source_surface": contract["source_surface"],
        "source_geometry": list(contract["source_geometry"]),
        "current_surface": binding.get("surface") if type(binding) is dict else None,
        "current_geometry": None if resolution is None else resolution["current_geometry"],
        "translation": None if resolution is None else resolution["translation"],
        "resolved_box": None if resolution is None else resolution["resolved_box"],
        "observed_crop_sha256": observed,
        "expected_crop_sha256": contract["expected_crop_sha256"],
        "scored_frame_sha256": frame_sha256(frame),
        "frame": {"width": frame.width, "height": frame.height, "mode": frame.mode},
        "grants_input_authority": False}


def score_path(contract, image_path, binding):
    return score_frame(contract, load_exact_frame(image_path), binding)


def reconcile_artifact(result, image_path):
    if (type(result) is not dict or result.get("schema") != SCORE_SCHEMA or
            result.get("grants_input_authority") is not False):
        raise ValueError("target-relative no-authority result required")
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
