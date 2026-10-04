"""Derive and locally repair semantic regions from verified target handles."""
import hashlib
import json

try:
    from .coordinate_frame_transform_v1 import translation
    from .target_relative_crop_semantic_probe_v1 import validate as validate_contract
except ImportError:
    from coordinate_frame_transform_v1 import translation
    from target_relative_crop_semantic_probe_v1 import validate as validate_contract


RELATION_SCHEMA = "target-semantic-region-relation-v1"
DERIVATION_SCHEMA = "target-handle-semantic-derivation-v1"
REPAIR_SCHEMA = "target-handle-semantic-repair-v1"


def _binding(observation):
    if type(observation) is not dict:
        raise ValueError("observation required")
    binding = observation.get("pointer_binding")
    if type(binding) is not dict or set(binding) != {"focus", "surface", "geometry"}:
        raise ValueError("coherent pointer binding required")
    if any(type(binding.get(key)) is not int or binding[key] in (0, 1)
           for key in ("focus", "surface")):
        raise ValueError("focus and surface required")
    translation("window_content", binding["geometry"], binding["geometry"])
    if type(observation.get("sequence")) is not int or observation["sequence"] < 1:
        raise ValueError("positive observation sequence required")
    return binding


def _relation(value):
    if (type(value) is not dict or set(value) != {"schema", "anchor", "offset", "size"}
            or value["schema"] != RELATION_SCHEMA or value["anchor"] != "target_box_origin"):
        raise ValueError("exact target relation required")
    offset, size = value["offset"], value["size"]
    if (type(offset) is not list or len(offset) != 2 or
            any(type(item) is not int for item in offset) or
            type(size) is not list or len(size) != 2 or
            any(type(item) is not int or item <= 0 for item in size) or
            size[0]*size[1] > 65536):
        raise ValueError("bounded integer relation required")
    return {"schema": RELATION_SCHEMA, "anchor": "target_box_origin",
            "offset": list(offset), "size": list(size)}


def _verified(mint_receipt, resolution, observation):
    binding = _binding(observation)
    if (type(mint_receipt) is not dict or mint_receipt.get("status") != "VALID" or
            not isinstance(mint_receipt.get("handle"), str) or
            not mint_receipt.get("authority", "").startswith("observational reference")):
        raise ValueError("verified observational handle receipt required")
    if (type(resolution) is not dict or resolution.get("eligible") is not True or
            resolution.get("status") not in ("VALID", "REVALIDATED") or
            resolution.get("handle") != mint_receipt["handle"] or
            resolution.get("sequence") != observation["sequence"] or
            not resolution.get("authority", "").startswith("resolution only")):
        raise ValueError("current verified handle resolution required")
    box = resolution.get("observed_box")
    if (type(box) is not list or len(box) != 4 or
            any(type(item) is not int for item in box) or box[2] <= 0 or box[3] <= 0):
        raise ValueError("resolved target box required")
    return binding, box


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True,
        separators=(",", ":")).encode()).hexdigest()


def derive_contract(probe_id, target_reference, mint_receipt, resolution,
                    observation, relation, expected_crop_sha256, success_reason):
    binding, target_box = _verified(mint_receipt, resolution, observation)
    relation = _relation(relation)
    left = target_box[0] + relation["offset"][0]
    top = target_box[1] + relation["offset"][1]
    right = left + relation["size"][0]
    bottom = top + relation["size"][1]
    geometry = binding["geometry"]
    local_box = [left-geometry[0], top-geometry[1],
                 right-geometry[0], bottom-geometry[1]]
    contract = validate_contract({
        "schema": "target-relative-rgb-crop-semantic-probe-v1",
        "probe_id": probe_id, "target_reference": target_reference,
        "coordinate_frame": "window_content", "source_surface": binding["surface"],
        "source_geometry": list(geometry), "box_in_frame": local_box,
        "expected_crop_sha256": expected_crop_sha256,
        "success_reason": success_reason,
        "allowed_transformations": ["window_translation"],
        "grants_input_authority": False})
    receipt = {"schema": DERIVATION_SCHEMA, "status": "DERIVED_NO_AUTHORITY",
        "handle": mint_receipt["handle"], "target_name": mint_receipt.get("name"),
        "handle_patch_sha256": resolution.get("patch_sha256"),
        "observation_sequence": observation["sequence"],
        "surface": binding["surface"], "geometry": list(geometry),
        "resolved_target_box": list(target_box), "relation": relation,
        "resolved_semantic_screen_box": [left, top, right, bottom],
        "semantic_box_in_frame": local_box, "contract_sha256": _digest(contract),
        "grants_input_authority": False}
    return {"contract": contract, "receipt": receipt}


def repair_contract(previous_contract, mint_receipt, resolution, observation, relation):
    previous = validate_contract(previous_contract)
    repaired = derive_contract(previous["probe_id"], previous["target_reference"],
        mint_receipt, resolution, observation, relation,
        previous["expected_crop_sha256"], previous["success_reason"])
    current = repaired["contract"]
    if current["source_surface"] != previous["source_surface"]:
        raise ValueError("local repair cannot cross surfaces")
    if current["source_geometry"] == previous["source_geometry"]:
        raise ValueError("geometry change required for repair")
    receipt = {"schema": REPAIR_SCHEMA, "status": "REPAIRED_NO_AUTHORITY",
        "prior_contract_sha256": _digest(previous),
        "repaired_contract_sha256": _digest(current),
        "prior_geometry": list(previous["source_geometry"]),
        "repaired_geometry": list(current["source_geometry"]),
        "handle_derivation": repaired["receipt"], "model_calls": 0,
        "grants_input_authority": False}
    return {"contract": current, "receipt": receipt}
