"""Bind a positive world receipt or preserve a coordinate-free abstention."""


def validate(value, readiness):
    if not isinstance(value, dict) or value.get("receipt_index") != 1:
        raise ValueError("one declared receipt required")
    if value.get("evidence_kind") != "animated_placement_preview_context":
        raise ValueError("world preview evidence kind required")
    receipt = readiness["receipts"][0]
    if value.get("op") == "needs_decision":
        if set(value) != {"op", "receipt_index", "evidence_kind", "reason"}:
            raise ValueError("abstention must carry no executable target")
        if value["reason"] not in ("no_match", "ambiguous_relation", "unreadable_evidence"):
            raise ValueError("invalid abstention reason")
        return {"status": "NEEDS_DECISION", "reason": value["reason"], "point": None}
    required = {"op", "receipt_index", "point_space", "point", "motion_model", "evidence_kind", "relation"}
    if value.get("op") != "target_reference" or set(value) != required:
        raise ValueError("invalid positive world target")
    point = value["point"]
    if [point.get("x"), point.get("y")] != receipt["point"]:
        raise ValueError("world receipt point mismatch")
    if value["point_space"] != "source_observation_pixels" or value["motion_model"] != "surface_origin_translation":
        raise ValueError("invalid point binding")
    if value["relation"] != "directly_above_copper_source":
        raise ValueError("task relation not established")
    return {"status": "EVIDENCE_BOUND", "receipt_index": 1,
            "point": receipt["point"], "relation": value["relation"]}
