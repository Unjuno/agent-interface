import copy
from collections import defaultdict

def expected_effect(scenario):
    return scenario in {"stable","semantic_same","unrelated_change"}

def expected_snapshot(s):
    return {
        "stable":{"target_version":0,"action_allowed":1,"unrelated_version":0},
        "semantic_same":{"target_version":1,"action_allowed":1,"unrelated_version":0},
        "predicate_invalid":{"target_version":1,"action_allowed":0,"unrelated_version":0},
        "unrelated_change":{"target_version":0,"action_allowed":1,"unrelated_version":1},
    }[s]

def audit_rows(rows):
    metrics=defaultdict(lambda:{"cases":0,"effects":0,"stale_effects":0,"false_rejects":0})
    errors=[]
    for r in rows:
        p=r["policy"]; s=r["scenario"]; d=r["delivery"]; cid=r["case_id"]
        m=metrics[p]; m["cases"]+=1
        if (d["decision"]=="effect") != (d["effect_count"]==1):
            errors.append((cid,"decision_effect_mismatch"))
        effect=d["effect_count"]==1
        if effect:m["effects"]+=1
        gt=expected_effect(s)
        if effect and not gt:m["stale_effects"]+=1
        if (not effect) and gt:m["false_rejects"]+=1
        if r["pre_delivery_context"] != expected_snapshot(s):
            errors.append((cid,"bad_pre_snapshot"))
        pre=r["pre_delivery_context"]
        if (d["target_version"],d["action_allowed"],d["unrelated_version"]) != (pre["target_version"],pre["action_allowed"],pre["unrelated_version"]):
            errors.append((cid,"decision_snapshot_mismatch"))
        if not r["sender_committed"]:
            errors.append((cid,"sender_not_committed"))
    return dict(metrics), errors

def corruption_test(rows):
    tests={}
    a=copy.deepcopy(rows[0]); a["delivery"]["effect_count"]=0
    tests["effect_count"]=audit_rows([a])[1]
    b=copy.deepcopy(next(r for r in rows if r["scenario"]=="predicate_invalid")); b["pre_delivery_context"]["action_allowed"]=1
    tests["predicate_snapshot"]=audit_rows([b])[1]
    c=copy.deepcopy(rows[0]); c["sender_committed"]=False
    tests["sender_flag"]=audit_rows([c])[1]
    return tests
