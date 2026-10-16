"""Bind a semantic target selection to a verified meaning-free hover receipt."""


def validate(value, readiness):
    required = {"op", "receipt_index", "point_space", "point", "motion_model",
                "evidence_kind"}
    if not isinstance(value, dict) or set(value) != required:
        raise ValueError("invalid evidence target fields")
    if (value["op"] != "target_reference"
            or value["point_space"] != "source_observation_pixels"
            or value["motion_model"] != "surface_origin_translation"
            or value["evidence_kind"] != "persistent_hover_tooltip"):
        raise ValueError("invalid evidence target semantics")
    if not isinstance(readiness, dict) or readiness.get("status") != "READY":
        raise ValueError("verified hover readiness required")
    index = value["receipt_index"]
    if type(index) is not int or not 1 <= index <= len(readiness.get("receipts", [])):
        raise ValueError("receipt index outside verified evidence")
    point = value["point"]
    if (not isinstance(point, dict) or set(point) != {"x", "y"}
            or type(point["x"]) is not int or type(point["y"]) is not int):
        raise ValueError("integer selected point required")
    receipt = readiness["receipts"][index - 1]
    if [point["x"], point["y"]] != receipt["point"]:
        raise ValueError("selected point does not match cited receipt")
    return {"status": "EVIDENCE_BOUND", "point": receipt["point"],
            "receipt_index": index, "receipt": receipt,
            "authority": "reference only; ordinary input admission remains required"}
