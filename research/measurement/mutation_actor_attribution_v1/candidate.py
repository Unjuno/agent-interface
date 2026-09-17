from __future__ import annotations

ACTOR_CLASSES = {
    "THIS_INTENT",
    "THIS_SESSION_OTHER_INTENT",
    "EXTERNAL_PROCESS",
    "HUMAN",
    "OS",
    "UNKNOWN",
}
EXTERNAL_CLASSES = {"THIS_SESSION_OTHER_INTENT", "EXTERNAL_PROCESS", "HUMAN", "OS"}

def _valid_id(x):
    return isinstance(x, str) and 1 <= len(x) <= 96 and all(c.isalnum() or c in "_-:." for c in x)

def _lineage_tuple(obj):
    return tuple(obj.get(k) for k in ("session_id", "intent_id", "action_id", "target_id", "delta_kind"))

def classify_lineage_bound(record):
    required = ("session_id", "intent_id", "action_id", "target_id", "delta_kind")
    if not isinstance(record, dict) or any(not _valid_id(record.get(k)) for k in required):
        return {"state": "UNATTRIBUTED", "actor_class": "UNKNOWN", "invalidate": True,
                "grants_authority": False, "verifies_task_success": False, "malformed": True}
    if record.get("mutation") is not True:
        if record.get("mutation") is False:
            return {"state": "NO_MUTATION", "actor_class": "UNKNOWN", "invalidate": False,
                    "grants_authority": False, "verifies_task_success": False, "malformed": False}
        return {"state": "UNATTRIBUTED", "actor_class": "UNKNOWN", "invalidate": True,
                "grants_authority": False, "verifies_task_success": False, "malformed": True}
    at = record.get("action_time_ms"); mt = record.get("mutation_time_ms")
    if not isinstance(at, int) or not isinstance(mt, int) or mt < at:
        return {"state": "UNATTRIBUTED", "actor_class": "UNKNOWN", "invalidate": True,
                "grants_authority": False, "verifies_task_success": False, "malformed": True}
    witnesses = record.get("witnesses", [])
    if not isinstance(witnesses, list): witnesses = []
    current = _lineage_tuple(record); supported = set(); malformed_witness = False
    for w in witnesses:
        if not isinstance(w, dict):
            malformed_witness = True; continue
        cls = w.get("actor_class")
        if cls not in ACTOR_CLASSES:
            malformed_witness = True; continue
        wt = w.get("time_ms")
        if not isinstance(wt, int) or wt < at or wt > mt: continue
        if cls == "THIS_INTENT":
            if _lineage_tuple(w) == current: supported.add("THIS_INTENT")
        elif cls == "THIS_SESSION_OTHER_INTENT":
            if (w.get("session_id") == record["session_id"] and
                w.get("target_id") == record["target_id"] and
                w.get("delta_kind") == record["delta_kind"] and
                (w.get("intent_id") != record["intent_id"] or w.get("action_id") != record["action_id"])):
                supported.add(cls)
        elif cls in {"EXTERNAL_PROCESS", "HUMAN", "OS"}:
            if w.get("target_id") == record["target_id"] and w.get("delta_kind") == record["delta_kind"]:
                supported.add(cls)
    if malformed_witness: supported.add("UNKNOWN")
    concrete = {x for x in supported if x != "UNKNOWN"}
    if len(concrete) == 1 and "UNKNOWN" not in supported:
        cls = next(iter(concrete))
        if cls == "THIS_INTENT":
            return {"state": "SELF_CONFIRMED", "actor_class": cls, "invalidate": False,
                    "grants_authority": False, "verifies_task_success": False, "malformed": False}
        if cls in EXTERNAL_CLASSES:
            return {"state": "EXTERNAL_CONFIRMED", "actor_class": cls, "invalidate": True,
                    "grants_authority": False, "verifies_task_success": False, "malformed": False}
    return {"state": "UNATTRIBUTED", "actor_class": "UNKNOWN", "invalidate": True,
            "grants_authority": False, "verifies_task_success": False, "malformed": malformed_witness}

def classify_temporal_nearest(record):
    if not isinstance(record, dict) or record.get("mutation") is not True:
        return "NO_MUTATION" if isinstance(record, dict) and record.get("mutation") is False else "UNATTRIBUTED"
    at = record.get("action_time_ms"); mt = record.get("mutation_time_ms")
    if isinstance(at, int) and isinstance(mt, int) and 0 <= mt - at <= 500:
        return "SELF_CONFIRMED"
    return "UNATTRIBUTED"
