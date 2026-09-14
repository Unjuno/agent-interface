"""Strict candidate-to-point contract for verified hover evidence."""
from openttd_hover_evidence_v1 import CANDIDATES
from point_target_contract_v2 import runtime_reference as point_runtime_reference


def validate(value):
    if type(value) is not dict or set(value) != {
            "op", "candidate_id", "point_space", "point", "motion_model"}:
        raise ValueError("exact hover-target contract required")
    candidate = value.get("candidate_id")
    if candidate not in CANDIDATES:
        raise ValueError("preregistered candidate required")
    point_value = {key: value[key] for key in
                   ("op", "point_space", "point", "motion_model")}
    point_runtime_reference(point_value)
    point = [value["point"]["x"], value["point"]["y"]]
    if point != CANDIDATES[candidate]["point"]:
        raise ValueError("candidate and point must match")


def runtime_reference(value):
    validate(value)
    point_value = {key: value[key] for key in
                   ("op", "point_space", "point", "motion_model")}
    return {"candidate_id": value["candidate_id"],
            **point_runtime_reference(point_value)}
