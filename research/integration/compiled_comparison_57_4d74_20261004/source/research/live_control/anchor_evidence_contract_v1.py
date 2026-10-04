"""Bind an accept-or-expand decision to one verified anchor receipt."""


def validate(value, readiness):
    required = {"op", "receipt_index", "point_space", "point", "motion_model",
                "evidence_kind"}
    if not isinstance(value, dict) or set(value) != required:
        raise ValueError("invalid anchor evidence fields")
    if (value["op"] not in ("target_reference", "expand_search")
            or value["receipt_index"] != 1
            or value["point_space"] != "source_observation_pixels"
            or value["motion_model"] != "surface_origin_translation"
            or value["evidence_kind"] != "persistent_hover_tooltip"):
        raise ValueError("invalid anchor evidence semantics")
    if (not isinstance(readiness, dict) or readiness.get("status") != "READY"
            or len(readiness.get("receipts", [])) != 1):
        raise ValueError("exactly one verified hover receipt required")
    point = value["point"]
    if (not isinstance(point, dict) or set(point) != {"x", "y"}
            or type(point["x"]) is not int or type(point["y"]) is not int):
        raise ValueError("integer anchor point required")
    receipt = readiness["receipts"][0]
    if [point["x"], point["y"]] != receipt["point"]:
        raise ValueError("anchor point does not match cited receipt")
    if value["op"] == "target_reference":
        return {"status": "EVIDENCE_BOUND", "point": receipt["point"],
                "receipt": receipt,
                "authority": "reference only; ordinary input admission remains required"}
    return {"status": "EXPANSION_REQUIRED", "anchor_point": receipt["point"],
            "receipt": receipt,
            "authority": "observation decision only; grants no target or input authority"}
