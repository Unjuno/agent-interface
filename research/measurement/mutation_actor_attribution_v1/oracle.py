from __future__ import annotations

VALID_EXTERNAL = {"THIS_SESSION_OTHER_INTENT", "EXTERNAL_PROCESS", "HUMAN", "OS"}
FIELDS = ("session_id", "intent_id", "action_id", "target_id", "delta_kind")

def _id_ok(v):
    if not isinstance(v, str) or not v or len(v) > 96: return False
    return set(v) <= set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-:.")

def replay_expected(record):
    malformed = False
    if not isinstance(record, dict) or any(not _id_ok(record.get(k)) for k in FIELDS):
        return _out("UNATTRIBUTED", "UNKNOWN", True, True)
    mutation = record.get("mutation")
    if mutation is False: return _out("NO_MUTATION", "UNKNOWN", False, False)
    if mutation is not True: return _out("UNATTRIBUTED", "UNKNOWN", True, True)
    a, m = record.get("action_time_ms"), record.get("mutation_time_ms")
    if type(a) is not int or type(m) is not int or m < a:
        return _out("UNATTRIBUTED", "UNKNOWN", True, True)
    claims = []; ws = record.get("witnesses")
    if not isinstance(ws, list): ws = []
    for w in ws:
        if not isinstance(w, dict):
            malformed = True; continue
        cls = w.get("actor_class")
        if cls not in {"THIS_INTENT", *VALID_EXTERNAL, "UNKNOWN"}:
            malformed = True; continue
        t = w.get("time_ms")
        if type(t) is not int or not (a <= t <= m): continue
        if cls == "THIS_INTENT":
            if all(w.get(k) == record.get(k) for k in FIELDS): claims.append(cls)
        elif cls == "THIS_SESSION_OTHER_INTENT":
            same_context = (w.get("session_id") == record["session_id"] and
                            w.get("target_id") == record["target_id"] and
                            w.get("delta_kind") == record["delta_kind"])
            different = (w.get("intent_id") != record["intent_id"] or w.get("action_id") != record["action_id"])
            if same_context and different: claims.append(cls)
        elif cls in {"EXTERNAL_PROCESS", "HUMAN", "OS"}:
            if w.get("target_id") == record["target_id"] and w.get("delta_kind") == record["delta_kind"]:
                claims.append(cls)
    if malformed: claims.append("UNKNOWN")
    concrete = set(x for x in claims if x != "UNKNOWN"); has_unknown = "UNKNOWN" in claims
    if len(concrete) != 1 or has_unknown:
        return _out("UNATTRIBUTED", "UNKNOWN", True, malformed)
    actor = next(iter(concrete))
    if actor == "THIS_INTENT": return _out("SELF_CONFIRMED", actor, False, malformed)
    return _out("EXTERNAL_CONFIRMED", actor, True, malformed)

def _out(state, actor_class, invalidate, malformed):
    return {"state": state, "actor_class": actor_class, "invalidate": invalidate,
            "grants_authority": False, "verifies_task_success": False, "malformed": malformed}
