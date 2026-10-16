"""Validate selection or coordinate-free abstention over verified receipts."""


NEGATIVE_REASONS = {"no_match_in_observed_set", "ambiguous_evidence",
                    "unavailable_evidence", "search_budget_exhausted"}


def validate(value, readiness):
    required = {"op", "receipt_index", "point_space", "points", "motion_model",
                "evidence_kind", "diagnostic_reason"}
    if not isinstance(value, dict) or set(value) != required:
        raise ValueError("invalid evidence decision fields")
    if value["evidence_kind"] != "persistent_hover_tooltip":
        raise ValueError("persistent hover evidence required")
    if not isinstance(readiness, dict) or readiness.get("status") != "READY":
        raise ValueError("verified hover readiness required")
    receipts = readiness.get("receipts", [])
    if not isinstance(receipts, list) or not receipts:
        raise ValueError("one or more verified receipts required")
    points = value["points"]
    if not isinstance(points, list) or len(points) > 1:
        raise ValueError("zero or one selected point required")
    if value["op"] == "needs_decision":
        if (value["receipt_index"] != 0 or points
                or value["point_space"] != "not_applicable"
                or value["motion_model"] != "not_applicable"):
            raise ValueError("abstention must carry no receipt or executable point")
        if value["diagnostic_reason"] not in NEGATIVE_REASONS:
            raise ValueError("invalid abstention diagnostic")
        return {"status": "NEEDS_DECISION", "authority_class": "NO_TARGET_AUTHORITY",
                "diagnostic_reason": value["diagnostic_reason"],
                "observed_receipts": len(receipts), "point": None,
                "authority": "none; caller must not issue target button input"}
    if (value["op"] != "target_reference" or value["diagnostic_reason"] != "matched"
            or value["point_space"] != "source_observation_pixels"
            or value["motion_model"] != "surface_origin_translation"
            or len(points) != 1):
        raise ValueError("invalid positive evidence decision")
    index = value["receipt_index"]
    if type(index) is not int or not 1 <= index <= len(receipts):
        raise ValueError("receipt index outside verified evidence")
    raw = points[0]
    if (not isinstance(raw, dict) or set(raw) != {"x", "y"}
            or type(raw["x"]) is not int or type(raw["y"]) is not int):
        raise ValueError("integer selected point required")
    receipt = receipts[index - 1]
    if [raw["x"], raw["y"]] != receipt["point"]:
        raise ValueError("selected point does not match cited receipt")
    return {"status": "EVIDENCE_BOUND", "authority_class": "TARGET_REFERENCE_ONLY",
            "diagnostic_reason": "matched", "observed_receipts": len(receipts),
            "point": receipt["point"], "receipt_index": index, "receipt": receipt,
            "authority": "reference only; ordinary input admission remains required"}
