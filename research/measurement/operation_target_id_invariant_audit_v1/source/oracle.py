from __future__ import annotations
from schema import canon_disp

# Independent semantic oracle: it consumes fixture facts, not generator expected labels.
def acceptable_from_facts(f):
    if f["hard_invalid"]:
        return [canon_disp({"op":"YIELD","reason":"STALE_STATE"})]
    if f["unsupported_operation"]:
        return [canon_disp({"op":"YIELD","reason":"UNSUPPORTED_OPERATION"})]
    if f["required_payload"] and not f["payload_available"]:
        return [canon_disp({"op":"YIELD","reason":"PAYLOAD_MISSING"})]
    if f["semantic_no_action"]:
        return [canon_disp({"op":"NO_LOCAL_ACTION","reason":"ALREADY_SATISFIED"})]
    valid=[t for t in f["targets"] if t["present"] and t["compatible"]]
    if f["requires_target"] and not valid:
        return [canon_disp({"op":"YIELD","reason":"MISSING_TARGET"})]
    if f["ambiguous"]:
        return [canon_disp({"op":"YIELD","reason":"AMBIGUOUS_TARGET"})]
    if f["operation"]=="TYPE_TEXT":
        return [canon_disp({"op":"TYPE_TEXT","target":valid[0]["id"],"payload_ref":f["payload_ref"]})]
    if f["operation"] in ("CLICK","SCROLL"):
        return [canon_disp({"op":f["operation"],"target":t["id"]}) for t in valid if t["acceptable"]]
    raise ValueError("oracle unsupported operation")
