"""Validate the typed-property flat world receipt result."""


def validate(value, readiness):
    required = {"op", "receipt_index", "point_space", "points", "motion_model", "evidence_kind", "relation", "reason"}
    if not isinstance(value, dict) or set(value) != required or value["receipt_index"] != 1:
        raise ValueError("exact one-receipt result required")
    if value["evidence_kind"] != "animated_placement_preview_context": raise ValueError("world evidence kind required")
    if not isinstance(value["points"], list) or len(value["points"]) > 1: raise ValueError("zero or one point required")
    if value["op"] == "needs_decision":
        if value["points"] or value["point_space"] != "not_applicable" or value["motion_model"] != "not_applicable" or value["relation"] != "not_applicable":
            raise ValueError("world abstention must carry no executable point")
        if value["reason"] not in ("no_match", "ambiguous_relation", "unreadable_evidence"):
            raise ValueError("invalid world abstention reason")
        return {"status": "NEEDS_DECISION", "reason": value["reason"], "point": None}
    if value["op"] != "target_reference" or len(value["points"]) != 1 or value["reason"] != "matched":
        raise ValueError("invalid positive world receipt result")
    raw = value["points"][0]
    if not isinstance(raw, dict) or set(raw) != {"x", "y"}: raise ValueError("exact point required")
    point = [raw["x"], raw["y"]]
    if point != readiness["receipts"][0]["point"]: raise ValueError("world receipt point mismatch")
    if value["point_space"] != "source_observation_pixels" or value["motion_model"] != "surface_origin_translation":
        raise ValueError("invalid world point binding")
    if value["relation"] != "directly_above_copper_source": raise ValueError("task relation not established")
    return {"status": "EVIDENCE_BOUND", "receipt_index": 1, "point": point, "relation": value["relation"]}
