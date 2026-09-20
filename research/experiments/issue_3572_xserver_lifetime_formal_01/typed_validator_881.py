from __future__ import annotations

KNOWN = "KNOWN"
KNOWN_NULL = "KNOWN_NULL"
UNKNOWN = "UNKNOWN"
VALID_STATES = {KNOWN, KNOWN_NULL, UNKNOWN}

EXACT_MATCH = "EXACT_MATCH"
CORE_MATCH_REFINEMENT_UNKNOWN = "CORE_MATCH_REFINEMENT_UNKNOWN"
MISMATCH = "MISMATCH"
INVALID = "INVALID"


def known(value):
    if value is None:
        return {"state": KNOWN_NULL}
    return {"state": KNOWN, "value": value}


def field_evidence(mapping: dict, key: str):
    if key not in mapping:
        return {"state": UNKNOWN}
    return known(mapping[key])


def identity_from_context(context: dict, *, backend: str):
    return {
        "backend": known(backend),
        "top_level_client_id": field_evidence(context, "client_id"),
        "transient_for": field_evidence(context, "transient_for"),
    }


def _valid_evidence(e: object, *, mandatory: bool, value_type=None) -> bool:
    if not isinstance(e, dict) or e.get("state") not in VALID_STATES:
        return False
    state = e["state"]
    if mandatory and state != KNOWN:
        return False
    if state == KNOWN:
        if "value" not in e:
            return False
        if value_type is not None and not isinstance(e["value"], value_type):
            return False
    elif "value" in e:
        return False
    return True


def _semantic_value(e: dict):
    if e["state"] == KNOWN:
        return e["value"]
    if e["state"] == KNOWN_NULL:
        return None
    raise ValueError("UNKNOWN has no semantic value")


def classify(receipt: dict, current_identity: dict) -> dict:
    # Recovery evidence is observation-only. A receipt that claims task authority
    # is malformed regardless of identity equality.
    if receipt.get("authority") != "none":
        return {"classification": INVALID, "reason": "authority_not_none"}
    if receipt.get("task_input_granted") is not False:
        return {"classification": INVALID, "reason": "task_input_not_false"}
    if receipt.get("action_admission_eligible") is not False:
        return {"classification": INVALID, "reason": "action_admission_not_false"}

    r = receipt.get("identity")
    c = current_identity
    if not isinstance(r, dict) or not isinstance(c, dict):
        return {"classification": INVALID, "reason": "identity_not_mapping"}

    specs = {
        "backend": (True, str),
        "top_level_client_id": (True, int),
        "transient_for": (False, int),
    }
    for key, (mandatory, typ) in specs.items():
        if key not in r or key not in c:
            return {"classification": INVALID, "reason": f"missing_evidence:{key}"}
        if not _valid_evidence(r[key], mandatory=mandatory, value_type=typ):
            return {"classification": INVALID, "reason": f"invalid_receipt_evidence:{key}"}
        if not _valid_evidence(c[key], mandatory=mandatory, value_type=typ):
            return {"classification": INVALID, "reason": f"invalid_current_evidence:{key}"}

    for key in ("backend", "top_level_client_id"):
        if _semantic_value(r[key]) != _semantic_value(c[key]):
            return {"classification": MISMATCH, "reason": f"core_mismatch:{key}"}

    rt = r["transient_for"]
    ct = c["transient_for"]
    if UNKNOWN in (rt["state"], ct["state"]):
        return {
            "classification": CORE_MATCH_REFINEMENT_UNKNOWN,
            "reason": "core_match_transient_refinement_unknown",
        }
    if _semantic_value(rt) != _semantic_value(ct):
        return {"classification": MISMATCH, "reason": "refinement_mismatch:transient_for"}
    return {"classification": EXACT_MATCH, "reason": "all_observed_identity_equal"}
