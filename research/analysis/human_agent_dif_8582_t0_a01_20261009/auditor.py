#!/usr/bin/env python3
"""Independent raw-only exact-count auditor for Issue #8582 T0."""
import argparse,copy,hashlib,itertools,json,math
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def oracle_rows(spec):
    out=[]; n=spec["replicates_per_supported_cell"]
    for scenario,group,stratum,item in itertools.product(spec["scenarios"],spec["groups"],spec["strata"],spec["items"]):
        if scenario=="no_common_support" and (group,stratum) not in (("human_label","low"),("agent_label","high")): continue
        p=spec["probabilities"][scenario][item][0 if stratum=="low" else 1]
        mod=spec.get("effect_modifiers",{}).get(scenario,{}).get(item,{})
        if group=="agent_label": p+=mod.get("agent_"+stratum+"_delta",0)
        if not 0<=p<=100: raise ValueError("probability range")
        for rep in range(n):
            y=int(rep<p)
            if scenario=="missing_unknown" and item=="target_uniform" and group=="agent_label" and stratum=="high" and rep<50: y=None
            out.append({"scenario":scenario,"group":group,"stratum":stratum,"item":item,"replicate":rep,"outcome":y})
    return Counter(tuple(sorted(x.items())) for x in out)

def count_means(rows):
    cells=defaultdict(lambda:[0,0])
    for r in rows:
        if r["outcome"] is not None:
            c=cells[(r["scenario"],r["group"],r["stratum"],r["item"])]
            c[0]+=r["outcome"]; c[1]+=1
    return {k:(v[0]/v[1] if v[1] else None) for k,v in cells.items()}, {k:v[1] for k,v in cells.items()}

def classify(spec,scenario,rows,means,known):
    strata=[]
    for s in spec["strata"]:
        if all(means.get((scenario,g,s,i)) is not None for g in spec["groups"] for i in spec["items"]): strata.append(s)
    if not strata: return {"disposition":"HOLD_COMMON_SUPPORT","items":{i:"HOLD_COMMON_SUPPORT" for i in spec["items"]}}
    anchor_max=0
    for s in strata:
        for a in ("anchor_a","anchor_b"):
            anchor_max=max(anchor_max,abs(means[(scenario,"agent_label",s,a)]-means[(scenario,"human_label",s,a)]))
    if anchor_max>=spec["effect_threshold"]:
        return {"disposition":"HOLD_ANCHOR_INVALID","items":{i:"HOLD_ANCHOR_INVALID" for i in spec["items"]}}
    labels={}
    for item in spec["items"]:
        if item in ("anchor_a","anchor_b"):
            labels[item]="ANCHOR_REFERENCE"; continue
        if any(known.get((scenario,g,s,item),0)<spec["min_known_per_cell"] for g in spec["groups"] for s in strata):
            labels[item]="UNKNOWN_LOW_SUPPORT"; continue
        if len(strata)==2:
            discr=abs((means[(scenario,"human_label","high",item)]+means[(scenario,"agent_label","high",item)]-means[(scenario,"human_label","low",item)]-means[(scenario,"agent_label","low",item)])/2)
        else: discr=0
        if discr<.05:
            labels[item]="LOW_INFORMATION"; continue
        diffs=[means[(scenario,"agent_label",s,item)]-means[(scenario,"human_label",s,item)] for s in strata]
        t=spec["effect_threshold"]
        same_sign=bool(diffs) and all(abs(x)>=t for x in diffs) and (all(x>0 for x in diffs) or all(x<0 for x in diffs))
        if same_sign: labels[item]="UNIFORM_DIF"
        elif any(x>=t for x in diffs) and any(x<=-t for x in diffs): labels[item]="NONUNIFORM_DIF"
        else: labels[item]="NO_FLAG"
    return {"disposition":"ESTIMABLE","items":labels}

def reconstruct(spec,rows):
    means,known=count_means(rows); result={}
    for scenario in spec["scenarios"]:
        sr=[r for r in rows if r["scenario"]==scenario]
        gm={}
        for item,group in itertools.product(spec["items"],spec["groups"]):
            vals=[r["outcome"] for r in sr if r["item"]==item and r["group"]==group and r["outcome"] is not None]
            gm[f"{item}:{group}"]=sum(vals)/len(vals) if vals else None
        diffs={item:{s:(means[(scenario,"agent_label",s,item)]-means[(scenario,"human_label",s,item)] if means.get((scenario,"agent_label",s,item)) is not None and means.get((scenario,"human_label",s,item)) is not None else None) for s in spec["strata"]} for item in spec["items"]}
        result[scenario]={"row_count":len(sr),"known_count":sum(x["outcome"] is not None for x in sr),"group_marginal_means":gm,"within_stratum_differences":diffs,"classification":classify(spec,scenario,sr,means,known)}
    return result

def check(raw,spec):
    if raw.get("schema")!="issue-8582-candidate-raw-v1" or raw.get("authority")!="NONE": raise ValueError("schema/authority")
    rows=raw.get("rows",[])
    if Counter(tuple(sorted(x.items())) for x in rows)!=oracle_rows(spec): raise ValueError("assigned item-response reconstruction")
    expected=reconstruct(spec,rows)
    if raw.get("scenario_results")!=expected: raise ValueError("candidate estimates/classifications differ from independent reconstruction")
    for scenario,res in expected.items():
        c=res["classification"]
        if scenario=="uniform_dif" and c["items"]["target_uniform"]!="UNIFORM_DIF": raise ValueError("uniform DIF missed")
        if scenario=="nonuniform_dif" and c["items"]["target_nonuniform"]!="NONUNIFORM_DIF": raise ValueError("nonuniform DIF missed")
        if scenario in ("invariant","placebo_labels") and any(v in ("UNIFORM_DIF","NONUNIFORM_DIF") for v in c["items"].values()): raise ValueError("null/placebo false flag")
        if scenario=="low_discrimination" and c["items"]["low_discrimination"]!="LOW_INFORMATION": raise ValueError("low discrimination not preserved")
        if scenario=="no_common_support" and c["disposition"]!="HOLD_COMMON_SUPPORT": raise ValueError("nonoverlap not held")
        if scenario=="invalid_anchors" and c["disposition"]!="HOLD_ANCHOR_INVALID": raise ValueError("invalid anchor accepted")
        if scenario=="missing_unknown" and c["items"]["target_uniform"]!="UNKNOWN_LOW_SUPPORT": raise ValueError("unknown imputed or certified")
    return {"rows_reconstructed":len(rows),"scenarios":len(expected),"checks":len(rows)+len(expected)*8,"errors":0}

def mutation_rejected(raw,spec,kind):
    x=copy.deepcopy(raw)
    if kind=="drop_response": x["rows"].pop()
    elif kind=="flip_label": x["rows"][0]["outcome"]=1-x["rows"][0]["outcome"]
    elif kind=="impute_unknown":
        r=next(r for r in x["rows"] if r["scenario"]=="missing_unknown" and r["item"]=="target_uniform" and r["group"]=="agent_label" and r["stratum"]=="high" and r["outcome"] is None); r["outcome"]=0
    elif kind=="false_uniform_null": x["scenario_results"]["invariant"]["classification"]["items"]["null_item"]="UNIFORM_DIF"
    elif kind=="accept_nonoverlap": x["scenario_results"]["no_common_support"]["classification"]["disposition"]="ESTIMABLE"
    elif kind=="ignore_bad_anchors": x["scenario_results"]["invalid_anchors"]["classification"]["disposition"]="ESTIMABLE"
    elif kind=="authority": x["authority"]="FAIRNESS_CERTIFIED"
    else: raise ValueError("unknown mutation")
    try: check(x,spec)
    except (ValueError,KeyError,TypeError,ZeroDivisionError): return True
    return False

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--spec",default=str(ROOT/"spec.json")); ap.add_argument("--raw",default=str(ROOT/"results/candidate.raw.json")); ap.add_argument("--output",default=str(ROOT/"results/audit.raw.json")); a=ap.parse_args(); out=Path(a.output)
    if out.exists(): raise SystemExit("refusing existing formal output")
    spec=json.loads(Path(a.spec).read_text()); rb=Path(a.raw).read_bytes(); raw=json.loads(rb); summary=check(raw,spec)
    controls={m:mutation_rejected(raw,spec,m) for m in ("drop_response","flip_label","impute_unknown","false_uniform_null","accept_nonoverlap","ignore_bad_anchors","authority")}
    if not all(controls.values()): raise ValueError("mutation control accepted")
    summary.update({"allocation":spec["allocation"],"disposition":"PASS_METHOD_SCOPED","mutation_controls":controls,"mutation_rejections":f"{sum(controls.values())}/{len(controls)}","candidate_raw_sha256":hashlib.sha256(rb).hexdigest(),"authority":"NONE"})
    out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(summary,sort_keys=True,separators=(",",":"))+"\n"); print(json.dumps(summary,sort_keys=True))
if __name__=="__main__": main()
