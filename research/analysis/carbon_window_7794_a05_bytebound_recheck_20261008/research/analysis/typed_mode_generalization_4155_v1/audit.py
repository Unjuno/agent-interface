"""Independent raw-only auditor. Does not import study.py."""
from __future__ import annotations

import hashlib
import json
import math
import sys
from collections import Counter
from pathlib import Path

MODES = ("FOCUS_LOST", "TARGET_STALE", "MODAL_BLOCKED", "APP_BUSY", "LAYOUT_CHANGED")
ACTION = {"FOCUS_LOST": "REBIND", "TARGET_STALE": "YIELD",
          "MODAL_BLOCKED": "WAIT_OBSERVE", "APP_BUSY": "WAIT_OBSERVE",
          "LAYOUT_CHANGED": "REOBSERVE"}
P = {
    "FOCUS_LOST": (.88,.20,.12,.12,.12,.22),
    "TARGET_STALE": (.15,.88,.12,.12,.22,.72),
    "MODAL_BLOCKED": (.12,.26,.88,.10,.18,.20),
    "APP_BUSY": (.12,.20,.12,.88,.20,.78),
    "LAYOUT_CHANGED": (.12,.38,.18,.16,.88,.70),
}
TRAIN_SEEDS = (415571, 415572, 415573)
FORMAL_SEEDS = (415581, 415582, 415583)
LABELS = tuple(sorted(set(ACTION.values())))
ALPHA, MINP, MINM = 1.0, .65, .15
TRAIN_PER_MODE = 96


def canon(x):
    return json.dumps(x, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def sha(x):
    return hashlib.sha256(canon(x)).hexdigest()


def regen(seed, n, split, block):
    import random
    r = random.Random(seed)
    out = []
    for m in MODES:
        for k in range(n):
            f = [int(r.random() < q) for q in P[m]]
            if block == "SINGLE_MISSING":
                for j in {MODES.index(m), r.randrange(6)}: f[j] = None
            elif block == "MULTI_MISSING":
                for j in r.sample(range(6), 3): f[j] = None
            elif block == "NUISANCE_SHIFT":
                f[5] = 1 - f[5]
            elif block == "COMPOSITION_HOLDOUT":
                masks = {"FOCUS_LOST":(0,5),"TARGET_STALE":(1,5),
                         "MODAL_BLOCKED":(2,1),"APP_BUSY":(3,5),
                         "LAYOUT_CHANGED":(4,1)}
                for j in masks[m]: f[j] = None
            out.append({"row_id":f"{split}:{seed}:{block}:{m}:{k}","split":split,
                        "seed":seed,"block":block,"mode":m,"features":f,
                        "expected":ACTION[m]})
    return out


def regen_controls(seed):
    prototypes={"FOCUS_LOST":[1,0,0,0,0,0],"TARGET_STALE":[0,1,0,0,0,1],
                "MODAL_BLOCKED":[0,0,1,0,0,0],"APP_BUSY":[0,0,0,1,0,1],
                "LAYOUT_CHANGED":[0,0,0,0,1,0]}
    out=[]
    for m in MODES:
        f=prototypes[m]
        out.append({"row_id":f"control:{seed}:FULL_DETERMINISTIC:{m}","split":"control",
                    "seed":seed,"block":"CONTROL","mode":m,"features":f,
                    "expected":ACTION[m]})
    out += [
        {"row_id":f"control:{seed}:UNKNOWN_ALL_MISSING","split":"control","seed":seed,
         "block":"CONTROL","mode":"UNKNOWN","features":[None]*6,"expected":"YIELD"},
        {"row_id":f"control:{seed}:CONTRADICTORY","split":"control","seed":seed,
         "block":"CONTROL","mode":"UNKNOWN","features":[1]*6,"expected":"YIELD"},
    ]
    return out


def train(rows, classes, field):
    n=Counter(z[field] for z in rows)
    one={c:[0]*6 for c in classes}; seen={c:[0]*6 for c in classes}
    for z in rows:
        c=z[field]
        for j,x in enumerate(z["features"]):
            if x is not None:
                seen[c][j]+=1; one[c][j]+=int(x)
    return {"n":n,"one":one,"seen":seen,"total":len(rows)}


def probs(m, labels, features):
    logs={}
    for c in labels:
        v=math.log((m["n"].get(c,0)+ALPHA)/(m["total"]+ALPHA*len(labels)))
        for j,x in enumerate(features):
            if x is None: continue
            p=(m["one"][c][j]+ALPHA)/(m["seen"][c][j]+2*ALPHA)
            v+=math.log(p if x else 1-p)
        logs[c]=v
    top=max(logs.values()); denom=sum(math.exp(v-top) for v in logs.values())
    return {c:math.exp(v-top)/denom for c,v in logs.items()}


def decision(p, mapping):
    agg={}
    for c,v in p.items(): agg[mapping[c]]=agg.get(mapping[c],0)+v
    ordered=sorted(agg.items(),key=lambda z:(-z[1],z[0]))
    conf=ordered[0][1]; margin=conf-(ordered[1][1] if len(ordered)>1 else 0)
    ok=conf>=MINP and margin>=MINM
    return {"action":ordered[0][0] if ok else "YIELD","emitted":True,
            "abstained_to_yield":not ok,
            "confidence":round(conf,12),"margin":round(margin,12),
            "posterior":{k:round(v,12) for k,v in sorted(agg.items())}}


def predict(dm, mm, row):
    return {"direct":decision(probs(dm,LABELS,row["features"]),{x:x for x in LABELS}),
            "mode":decision(probs(mm,MODES,row["features"]),ACTION)}


def summarize(rows, arm):
    actions=[r["predictions"][arm]["action"] for r in rows]
    wrong=sum(a!=r["expected"] for a,r in zip(actions,rows))
    wrong_recovery=sum(a not in ("YIELD","ABSTAIN") and a!=r["expected"]
                       for a,r in zip(actions,rows))
    actionable_correct=sum(a==r["expected"] and a not in ("YIELD","ABSTAIN")
                           for a,r in zip(actions,rows))
    return {"n":len(rows),"wrong_disposition":wrong,
            "wrong_disposition_rate":wrong/len(rows) if rows else 0,
            "wrong_recovery":wrong_recovery,
            "wrong_recovery_rate":wrong_recovery/len(rows) if rows else 0,
            "unnecessary_yield":sum(a=="YIELD" and r["expected"]!="YIELD" for a,r in zip(actions,rows)),
            "safe_recovery_coverage":actionable_correct/len(rows) if rows else 0,
            "actionable_coverage":sum(a not in ("YIELD","ABSTAIN") for a in actions)/len(rows) if rows else 0}


def audit(raw, training_seeds=TRAIN_SEEDS, formal_seeds=FORMAL_SEEDS):
    errors=[]; block_stats={}; ctrl_stats={"unknown":0,"contradictory":0,"full_mismatch":0}
    if raw.get("schema")!="typed-mode-generalization-formal-v1" or raw.get("issue")!=4844:
        errors.append("identity")
    if raw.get("policy")!={"alpha":1.0,"minimum_posterior":.65,"minimum_margin":.15,
                            "mode_to_disposition":ACTION}:
        errors.append("policy-binding")
    if raw.get("disposition")!=ACTION:
        errors.append("disposition-binding")
    if len(raw.get("seeds",[]))!=3: errors.append("seed-count")
    if raw.get("seed_schedule")!={"support":list(training_seeds),"heldout":list(formal_seeds)}:
        errors.append("seed-schedule")
    seen_ids=set()
    for idx, bundle in enumerate(raw.get("seeds",[])):
        seed=formal_seeds[idx]; support_seed=training_seeds[idx]
        if bundle.get("seed")!=seed or bundle.get("support_seed")!=support_seed:
            errors.append(f"seed-binding:{idx}"); continue
        support=regen(support_seed,TRAIN_PER_MODE,"support","COMPLETE")
        if bundle.get("support_rows")!=len(support) or bundle.get("support_digest")!=sha(support):
            errors.append(f"support:{seed}")
        direct=train(support,LABELS,"expected"); mode=train(support,MODES,"mode")
        expected_blocks=("COMPLETE","SINGLE_MISSING","MULTI_MISSING","COMPOSITION_HOLDOUT","NUISANCE_SHIFT")
        if [x.get("name") for x in bundle.get("blocks",[])]!=list(expected_blocks):
            errors.append(f"block-order:{seed}")
        for block in bundle.get("blocks",[]):
            name=block["name"]; expected=regen(seed,64,"heldout",name); rows=block.get("rows",[])
            if len(rows)!=len(expected): errors.append(f"row-count:{seed}:{name}"); continue
            if [x.get("row_id") for x in rows]!=[x["row_id"] for x in expected]:
                errors.append(f"row-id:{seed}:{name}")
            for actual, oracle in zip(rows,expected):
                if any(actual.get(k)!=oracle.get(k) for k in ("split","seed","block","mode","features","expected")):
                    errors.append(f"row-content:{actual.get('row_id')}"); break
                if actual["row_id"] in seen_ids: errors.append("duplicate-id")
                seen_ids.add(actual["row_id"])
                if actual.get("predictions")!=predict(direct,mode,oracle):
                    errors.append(f"prediction:{actual['row_id']}"); break
            for arm in ("direct","mode"):
                block_stats.setdefault(name,{arm:[]})
                block_stats[name].setdefault(arm,[]).append(summarize(rows,arm))
        controls=regen_controls(seed)
        actual_controls=bundle.get("controls",[])
        if len(actual_controls)!=len(controls): errors.append(f"control-count:{seed}")
        for actual,oracle in zip(actual_controls,controls):
            if any(actual.get(k)!=oracle.get(k) for k in ("row_id","split","seed","block","mode","features","expected")):
                errors.append(f"control-content:{seed}"); continue
            if actual.get("predictions")!=predict(direct,mode,oracle): errors.append(f"control-prediction:{seed}")
            tag=oracle["row_id"].split(":")[-1]
            if tag=="UNKNOWN_ALL_MISSING":
                ctrl_stats["unknown"]+=int(all(actual["predictions"][a]["action"]=="YIELD" for a in ("direct","mode")))
            elif tag=="CONTRADICTORY":
                ctrl_stats["contradictory"]+=int(all(actual["predictions"][a]["action"]=="YIELD" for a in ("direct","mode")))
            else:
                ctrl_stats["full_mismatch"]+=int(actual["predictions"]["direct"]["action"]!=oracle["expected"] or actual["predictions"]["mode"]["action"]!=oracle["expected"] or actual["predictions"]["direct"]["action"]!=actual["predictions"]["mode"]["action"])
    partial=("SINGLE_MISSING","MULTI_MISSING","COMPOSITION_HOLDOUT")
    gate_rows=[]
    for block in partial:
        d=[x for x in block_stats.get(block,{}).get("direct",[])]
        m=block_stats.get(block,{}).get("mode",[])
        agg={arm:{key:sum(row[key] for row in rows) for key in ("n","wrong_recovery","unnecessary_yield")}
             for arm,rows in (("direct",d),("mode",m))}
        for arm in agg:
            stats=d if arm=="direct" else m
            agg[arm]["wrong_recovery_rate"]=agg[arm]["wrong_recovery"]/agg[arm]["n"] if agg[arm]["n"] else 0
            agg[arm]["safe_recovery_coverage"]=sum(row["safe_recovery_coverage"]*row["n"] for row in stats)/agg[arm]["n"] if agg[arm]["n"] else 0
        di=agg["direct"]["wrong_recovery_rate"]; mi=agg["mode"]["wrong_recovery_rate"]
        relative=0 if di==0 else (di-mi)/di
        loss=agg["direct"]["safe_recovery_coverage"]-agg["mode"]["safe_recovery_coverage"]
        gate_rows.append({"block":block,"arms":agg,"relative_wrong_recovery_reduction":relative,"safe_recovery_coverage_loss":loss,
                          "pass_block":di>0 and relative>=.25 and loss<=.05 and mi<=di})
    status="STOP_AUDIT" if errors else "FAIL_DIAGNOSIS_STILL_REDUNDANT"
    if errors==[] and (ctrl_stats["unknown"]!=3 or ctrl_stats["contradictory"]!=3 or ctrl_stats["full_mismatch"]):
        status="FAIL_MODE_MISROUTES_RECOVERY"
    elif errors==[] and all(g["pass_block"] for g in gate_rows): status="PASS_TYPED_MODE_GENERALIZATION_SCOPED"
    elif errors==[] and any(g["safe_recovery_coverage_loss"]>.05 for g in gate_rows): status="HOLD_COVERAGE_TRADEOFF"
    elif errors==[] and any(g["relative_wrong_recovery_reduction"]>0 for g in gate_rows): status="HOLD_MIXED_PARTIAL_RESULT"
    return {"schema":"typed-mode-generalization-audit-v1","status":status,"errors":errors,
            "control_counts":ctrl_stats,"partial_gates":gate_rows,"block_stats":block_stats,
            "row_count":len(seen_ids)}


def main():
    if len(sys.argv)!=3: print("usage: audit.py INPUT.json OUTPUT.json",file=sys.stderr); return 2
    src=Path(sys.argv[1]); dst=Path(sys.argv[2])
    if dst.exists(): print("output-exists",file=sys.stderr); return 3
    raw=json.loads(src.read_bytes())
    result=audit(raw)
    dst.write_bytes(canon(result)+b"\n")
    print(json.dumps({"status":result["status"],"errors":len(result["errors"]),
                      "rows":result["row_count"]},sort_keys=True))
    return 0 if not result["errors"] else 1


if __name__=="__main__": raise SystemExit(main())
