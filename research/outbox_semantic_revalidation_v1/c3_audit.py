import copy
from collections import defaultdict

def expected_effect(s): return s in {"stable","unrelated_change"}
def expected_snapshot(s):
    return {
      "stable":{"context_id":"A","action_allowed":1,"unrelated_version":0},
      "context_replaced":{"context_id":"B","action_allowed":1,"unrelated_version":0},
      "predicate_invalid":{"context_id":"A","action_allowed":0,"unrelated_version":0},
      "unrelated_change":{"context_id":"A","action_allowed":1,"unrelated_version":1},
    }[s]

def audit_rows(rows):
    metrics=defaultdict(lambda:{"cases":0,"effects":0,"wrong_context_or_stale_effects":0,"false_rejects":0})
    errors=[]
    for r in rows:
        cid=r["case_id"]; p=r["policy"]; s=r["scenario"]; d=r["delivery"]; m=metrics[p]; m["cases"]+=1
        if (d["decision"]=="effect") != (d["effect_count"]==1): errors.append((cid,"decision_effect_mismatch"))
        eff=d["effect_count"]==1
        if eff:m["effects"]+=1
        gt=expected_effect(s)
        if eff and not gt:m["wrong_context_or_stale_effects"]+=1
        if (not eff) and gt:m["false_rejects"]+=1
        pre=r["pre_delivery_context"]
        if pre!=expected_snapshot(s): errors.append((cid,"bad_pre_snapshot"))
        if (d["context_id"],d["action_allowed"],d["unrelated_version"])!=(pre["context_id"],pre["action_allowed"],pre["unrelated_version"]): errors.append((cid,"decision_snapshot_mismatch"))
        if not r["sender_committed"]: errors.append((cid,"sender_not_committed"))
    return dict(metrics),errors

def corruption_test(rows):
    out={}
    a=copy.deepcopy(rows[0]); a["delivery"]["effect_count"]=0; out["effect_count"]=audit_rows([a])[1]
    b=copy.deepcopy(next(x for x in rows if x["scenario"]=="context_replaced")); b["pre_delivery_context"]["context_id"]="A"; out["context_id"]=audit_rows([b])[1]
    c=copy.deepcopy(rows[0]); c["sender_committed"]=False; out["sender_flag"]=audit_rows([c])[1]
    return out
