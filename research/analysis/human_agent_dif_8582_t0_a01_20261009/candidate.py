#!/usr/bin/env python3
"""Deterministic synthetic binary item response candidate for Issue #8582 T0."""
import argparse
import json
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parent


def supported(spec, scenario, group, stratum):
    if scenario == "no_common_support":
        return (group,stratum) in (("human_label","low"),("agent_label","high"))
    return True


def probability(spec, scenario, item, group, stratum):
    si=0 if stratum=="low" else 1
    p=spec["probabilities"][scenario][item][si]
    delta=spec.get("effect_modifiers",{}).get(scenario,{}).get(item,{})
    if group=="agent_label": p += delta.get(f"agent_{stratum}_delta",0)
    return p


def rows_for(spec):
    rows=[]
    for scenario in spec["scenarios"]:
        for group in spec["groups"]:
            for stratum in spec["strata"]:
                if not supported(spec,scenario,group,stratum):
                    continue
                for item in spec["items"]:
                    p=probability(spec,scenario,item,group,stratum)
                    for replicate in range(spec["replicates_per_supported_cell"]):
                        y=int(replicate < p)
                        if scenario=="missing_unknown" and item=="target_uniform" and group=="agent_label" and stratum=="high" and replicate<50:
                            y=None
                        rows.append({"scenario":scenario,"group":group,"stratum":stratum,"item":item,"replicate":replicate,"outcome":y})
    return rows


def estimates(rows):
    cells=defaultdict(list)
    for r in rows:
        if r["outcome"] is not None: cells[(r["group"],r["stratum"],r["item"])].append(r["outcome"])
    means={k:sum(v)/len(v) for k,v in cells.items() if v}
    return cells,means


def classify_scenario(spec, scenario, rows):
    cells,means=estimates(rows)
    common=[]
    for s in spec["strata"]:
        if all((g,s,item) in means for g in spec["groups"] for item in spec["items"]): common.append(s)
    if not common: return {"disposition":"HOLD_COMMON_SUPPORT","items":{i:"HOLD_COMMON_SUPPORT" for i in spec["items"]}}
    anchor_effect=max((abs(means[("agent_label",s,a)]-means[("human_label",s,a)]) for s in common for a in ("anchor_a","anchor_b")),default=0)
    if anchor_effect >= spec["effect_threshold"]:
        return {"disposition":"HOLD_ANCHOR_INVALID","items":{i:"HOLD_ANCHOR_INVALID" for i in spec["items"]}}
    result={}
    for item in spec["items"]:
        if item.startswith("anchor_"):
            result[item]="ANCHOR_REFERENCE"; continue
        if any(len(cells.get((g,s,item),[])) < spec["min_known_per_cell"] for g in spec["groups"] for s in common):
            result[item]="UNKNOWN_LOW_SUPPORT"; continue
        disc=abs(sum(means[(g,"high",item)] for g in spec["groups"])/2-sum(means[(g,"low",item)] for g in spec["groups"])/2) if len(common)==2 else 0
        if disc < 0.05:
            result[item]="LOW_INFORMATION"; continue
        diffs=[means[("agent_label",s,item)]-means[("human_label",s,item)] for s in common]
        threshold=spec["effect_threshold"]
        active=[d for d in diffs if abs(d)>=threshold]
        if len(active)==len(diffs) and active and all(d>0 for d in active) or len(active)==len(diffs) and active and all(d<0 for d in active):
            result[item]="UNIFORM_DIF"
        elif any(d>=threshold for d in diffs) and any(d<=-threshold for d in diffs):
            result[item]="NONUNIFORM_DIF"
        else:
            result[item]="NO_FLAG"
    return {"disposition":"ESTIMABLE","items":result}


def summarize(spec, rows):
    by={s:[r for r in rows if r["scenario"]==s] for s in spec["scenarios"]}
    out={}
    for scenario,rs in by.items():
        cells,means=estimates(rs)
        group_means={}
        for item in spec["items"]:
            for group in spec["groups"]:
                vals=[r["outcome"] for r in rs if r["item"]==item and r["group"]==group and r["outcome"] is not None]
                group_means[f"{item}:{group}"]=sum(vals)/len(vals) if vals else None
        item_diffs={}
        for item in spec["items"]:
            item_diffs[item]={s:means.get(("agent_label",s,item),None)-means.get(("human_label",s,item),None) if ("agent_label",s,item) in means and ("human_label",s,item) in means else None for s in spec["strata"]}
        out[scenario]={"row_count":len(rs),"known_count":sum(r["outcome"] is not None for r in rs),"group_marginal_means":group_means,"within_stratum_differences":item_diffs,"classification":classify_scenario(spec,scenario,rs)}
    return out


def run(spec):
    rows=rows_for(spec)
    return {"schema":"issue-8582-candidate-raw-v1","allocation":spec["allocation"],"rows":rows,"scenario_results":summarize(spec,rows),"authority":"NONE"}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--spec",default=str(ROOT/"spec.json")); ap.add_argument("--output",default=str(ROOT/"results/candidate.raw.json")); a=ap.parse_args(); out=Path(a.output)
    if out.exists(): raise SystemExit("refusing existing formal output")
    raw=run(json.loads(Path(a.spec).read_text())); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(raw,sort_keys=True,separators=(",",":"))+"\n"); print(json.dumps({"allocation":raw["allocation"],"rows":len(raw["rows"]),"scenarios":len(raw["scenario_results"]),"output":str(out)},sort_keys=True))

if __name__=="__main__": main()
