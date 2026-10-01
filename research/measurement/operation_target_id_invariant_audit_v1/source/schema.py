from __future__ import annotations

VISIBLE_KEYS = {
    "intent_id","observation_id","state_epoch","binding_id","allowed_operations",
    "payload_ref_present","candidates"
}
FORBIDDEN_VISIBLE_KEYS = {
    "acceptable","oracle","oracle_facts","chosen_label","teacher_label","future_effect",
    "post_state","evaluator_state","hidden_truth","negative_reason","split_group_id"
}
EXECUTABLE = {"CLICK","TYPE_TEXT","SCROLL"}
NONEXEC = {"NO_LOCAL_ACTION","YIELD"}


def canon_disp(d):
    op=d["op"]
    out={"op":op}
    if "target" in d: out["target"]=d["target"]
    if "payload_ref" in d: out["payload_ref"]=d["payload_ref"]
    if "reason" in d: out["reason"]=d["reason"]
    return out


def disp_key(d):
    d=canon_disp(d)
    return tuple((k,d[k]) for k in sorted(d))
