"""Bind a model-visible target patch to a later exact current observation."""


SCHEMA = "post-model-target-revalidation-v1"


def receipt(mint, resolution, source_observation, current_observation, model_call_id):
    if type(mint) is not dict or mint.get("status") != "VALID" or \
            not isinstance(mint.get("handle"), str):
        raise ValueError("valid target mint required")
    if type(resolution) is not dict or resolution.get("eligible") is not True or \
            resolution.get("status") not in ("VALID", "REVALIDATED") or \
            resolution.get("handle") != mint["handle"] or \
            resolution.get("patch_sha256") != mint.get("patch_sha256"):
        raise ValueError("matching current target resolution required")
    if type(model_call_id) is not str or not model_call_id:
        raise ValueError("model call id required")
    for observation in (source_observation, current_observation):
        if type(observation) is not dict or type(observation.get("sequence")) is not int or \
                type(observation.get("capture_ns")) is not int or \
                type(observation.get("pointer_binding")) is not dict or \
                observation.get("exact") is not True:
            raise ValueError("exact bound observations required")
    if current_observation["sequence"] <= source_observation["sequence"] or \
            current_observation["capture_ns"] <= source_observation["capture_ns"]:
        raise ValueError("strictly later current observation required")
    if current_observation["pointer_binding"] != source_observation["pointer_binding"]:
        raise ValueError("unchanged current binding required")
    if resolution.get("sequence") != current_observation["sequence"]:
        raise ValueError("resolution must bind current observation")
    return {"schema": SCHEMA, "status": "CURRENT_PATCH_MATCH_NO_AUTHORITY",
        "model_call_id": model_call_id, "handle": mint["handle"],
        "model_source_sequence": source_observation["sequence"],
        "current_sequence": current_observation["sequence"],
        "model_source_capture_ns": source_observation["capture_ns"],
        "current_capture_ns": current_observation["capture_ns"],
        "pointer_binding": current_observation["pointer_binding"],
        "patch_sha256": resolution["patch_sha256"],
        "resolved_point": resolution["point"],
        "grants_semantic_authority": False, "grants_input_authority": False}
