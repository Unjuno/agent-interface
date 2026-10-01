import copy
from collections import defaultdict

def expected_effect(scenario):
    return scenario in {"stable", "unrelated_change"}

def expected_snapshot(scenario):
    return {
        "stable": {"target_version":0,"other_version":0,"global_epoch":0},
        "relevant_change": {"target_version":1,"other_version":0,"global_epoch":1},
        "unrelated_change": {"target_version":0,"other_version":1,"global_epoch":1},
    }[scenario]

def audit_rows(rows):
    metrics = defaultdict(lambda: {"cases":0, "effects":0, "stale_effects":0, "false_rejects":0, "wrong_context_snapshot":0})
    errors = []
    for r in rows:
        cid=r["case_id"]; p=r["policy"]; s=r["scenario"]; d=r["delivery"]
        m=metrics[p]; m["cases"] += 1
        if d["decision"] not in {"effect","reject","duplicate"}:
            errors.append((cid,"invalid_decision"))
        if (d["decision"]=="effect") != (d["effect_count"]==1):
            errors.append((cid,"decision_effect_count_mismatch"))
        effect = d["effect_count"] == 1
        if effect: m["effects"] += 1
        gt = expected_effect(s)
        if effect and not gt: m["stale_effects"] += 1
        if (not effect) and gt: m["false_rejects"] += 1
        pre = r["pre_delivery_context"]
        snap=(d["target_version"],d["other_version"],d["global_epoch"])
        exp=(pre["target_version"],pre["other_version"],pre["global_epoch"])
        if snap != exp:
            m["wrong_context_snapshot"] += 1
            errors.append((cid,"delivery_snapshot_mismatch"))
        if not r["sender_committed"]:
            errors.append((cid, "sender_not_committed"))
        if pre != expected_snapshot(s):
            errors.append((cid, "bad_pre_delivery_snapshot"))
    return dict(metrics), errors

def corruption_test(rows):
    cases=[]
    a=copy.deepcopy(rows[0]); a["sender_committed"]=False; cases.append(("sender_flag",a))
    b=copy.deepcopy(rows[0]); b["delivery"]["effect_count"]=0; cases.append(("effect_count",b))
    rel=next(r for r in rows if r["scenario"]=="relevant_change")
    c=copy.deepcopy(rel); c["pre_delivery_context"]["target_version"]=0; cases.append(("context",c))
    out={}
    for name,row in cases:
        _, errs=audit_rows([row])
        out[name]=errs
    return out
