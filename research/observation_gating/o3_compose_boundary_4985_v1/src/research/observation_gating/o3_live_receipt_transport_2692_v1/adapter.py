"""Fail-open adapter from live transport receipt into the existing O3 gate."""
from gate import evaluate_region
from transport import digest, effect_reference


def evaluate_delivery(request, receipt, source_event, trusted_window, frame_bytes, region_bytes, arrival_ns):
    reasons = []
    if not isinstance(receipt, dict):
        return {"admitted": False, "reason": "malformed_receipt",
                "model_escalation_eligible": True, "action_emissions": 0}
    required = ("observation_id", "intent_epoch", "region_id", "source_window",
                "source_pid", "source_generation", "capture_start_ns", "capture_end_ns",
                "focus_xid", "coverage", "freshness", "effect_binding",
                "effect_binding_ref", "full_frame_sha256", "region_frame_sha256")
    if any(key not in receipt for key in required):
        reasons.append("missing_receipt_field")
    if receipt.get("observation_id") != request.get("observation_id"):
        reasons.append("stale_observation")
    if receipt.get("intent_epoch") != request.get("intent_epoch"):
        reasons.append("stale_intent")
    if receipt.get("region_id") != request.get("region_id"):
        reasons.append("region_mismatch")
    if receipt.get("source_window") != trusted_window.get("xid"):
        reasons.append("source_window_mismatch")
    if receipt.get("source_pid") != trusted_window.get("pid") or receipt.get("source_title") != trusted_window.get("title"):
        reasons.append("source_process_mismatch")
    if receipt.get("source_generation") != trusted_window.get("generation"):
        reasons.append("source_generation_mismatch")
    if receipt.get("focus_xid") != source_event.get("source_window_snapshot", {}).get("focus_xid"):
        reasons.append("focus_receipt_mismatch")
    if receipt.get("focus_stable") is not True:
        reasons.append("focus_changed_during_capture")
    if receipt.get("coverage") != "COMPLETE":
        reasons.append("incomplete_coverage")
    if receipt.get("freshness") != "CURRENT":
        reasons.append("stale_freshness")
    if receipt.get("effect_binding") != "BOUND":
        reasons.append("unbound_effect")
    if receipt.get("authority_grants") != 0 or receipt.get("ambiguous") is not False:
        reasons.append("unsafe_or_ambiguous_receipt")
    if not isinstance(receipt.get("capture_start_ns"), int) or not isinstance(receipt.get("capture_end_ns"), int) or receipt.get("capture_end_ns", 0) < receipt.get("capture_start_ns", 0):
        reasons.append("invalid_capture_clock")
    if type(arrival_ns) is not int or arrival_ns < receipt.get("capture_end_ns", 0):
        reasons.append("invalid_arrival_clock")
    max_age_ns = request.get("max_receipt_age_ns")
    if (type(max_age_ns) is not int or type(arrival_ns) is not int
            or type(receipt.get("capture_end_ns")) is not int
            or arrival_ns - receipt["capture_end_ns"] > max_age_ns):
        reasons.append("stale_arrival")
    if digest(frame_bytes) != receipt.get("full_frame_sha256") or digest(region_bytes) != receipt.get("region_frame_sha256"):
        reasons.append("frame_hash_mismatch")
    wanted_ref = effect_reference(request.get("observation_id"), request.get("intent_epoch"),
                                  request.get("region_id"), receipt.get("region_frame_sha256"))
    if receipt.get("effect_binding_ref") != wanted_ref:
        reasons.append("effect_binding_ref_mismatch")
    gate = evaluate_region(receipt,
                           observation_id=request.get("observation_id"),
                           intent_epoch=request.get("intent_epoch"),
                           region_id=request.get("region_id"),
                           trusted_source_window=trusted_window.get("xid"))
    if not gate.admitted:
        reasons.append("gate:" + gate.reason)
    admitted = not reasons
    return {"admitted": admitted,
            "reason": "admitted" if admitted else ";".join(reasons),
            "model_escalation_eligible": not admitted,
            "action_emissions": 0}
