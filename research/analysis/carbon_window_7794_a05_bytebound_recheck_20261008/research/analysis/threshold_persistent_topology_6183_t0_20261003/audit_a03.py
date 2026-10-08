#!/usr/bin/env python3
"""Independent raw-only A03 replay and auditor corruption challenge."""
import copy
import json
import os
from collections import deque
from pathlib import Path

ROOT = Path(__file__).parent
OUT = Path(os.environ.get("OUT_DIR", ROOT))


def expand(case, palette, factor):
    raster = []
    for row in case["rows"]:
        decoded = [palette[c] for c in row]
        for _ in range(factor):
            raster.append([v for v in decoded for _ in range(factor)])
    ends = tuple((x*factor,y*factor) for x,y in case["endpoints"])
    return raster, ends


def route(image, ends, threshold):
    h,w = len(image),len(image[0]); start,goal=ends
    pending=[start] if image[start[1]][start[0]]>threshold else []
    seen=set(pending)
    while pending:
        x,y=pending.pop()
        if (x,y)==goal: return True
        for p in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
            px,py=p
            if 0<=px<w and 0<=py<h and p not in seen and image[py][px]>threshold:
                seen.add(p);pending.append(p)
    return False


def holes(image, threshold):
    h,w=len(image),len(image[0])
    bg={(x,y) for y in range(h) for x in range(w) if image[y][x]<=threshold}
    exterior=set()
    stack=[p for p in bg if p[0]==0 or p[1]==0 or p[0]==w-1 or p[1]==h-1]
    while stack:
        x,y=stack.pop()
        if (x,y) in exterior: continue
        exterior.add((x,y))
        stack.extend(p for p in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)) if p in bg and p not in exterior)
    remaining=bg-exterior; count=0
    while remaining:
        count+=1; stack=[remaining.pop()]
        while stack:
            x,y=stack.pop()
            for p in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
                if p in remaining: remaining.remove(p);stack.append(p)
    return count


def replay(image, ends, kind, threshold):
    return route(image,ends,threshold) if kind=="route" else holes(image,threshold)==1


def classify(votes):
    total=sum(votes)
    if total>=3: return "PRESENT"
    if total<=1: return "ABSENT"
    return "UNKNOWN"


def inspect_rows(rows, cases, labels, palette, scales, thresholds):
    errors=[]; expected_ids=[]; expected={}
    for c in cases:
        for scale in scales:
            image,ends=expand(c,palette,scale); ref,_=expand(next(x for x in cases if x["id"]==c["reference"]),palette,scale)
            flat=[v for r in image for v in r]; refflat=[v for r in ref for v in r]
            delta=sum(abs(a-b) for a,b in zip(flat,refflat))/(255*len(flat))
            pixel="PRESENT" if delta<=.02 else "ABSENT" if delta>=.10 else "UNKNOWN"
            single="PRESENT" if replay(image,ends,c["predicate"],128) else "ABSENT"
            votes=[replay(image,ends,c["predicate"],t) for t in thresholds]
            expected_id=f"{c['id']}@{scale}x"; expected_ids.append(expected_id)
            expected[expected_id]={"pixel":pixel,"single":single,"persistent":classify(votes),"truth":labels[c["id"]]["visual_truth"],"scale":scale,"base_id":c["id"],"threshold_matches":sum(votes),"pixel_visits":len(flat)*6}
    ids=[r.get("case_id") for r in rows]
    if len(ids)!=len(set(ids)): errors.append("duplicate_case_id")
    lookup={r.get("case_id"):r for r in rows}
    for cid in expected_ids:
        row=lookup.get(cid); exp=expected[cid]
        if row is None: errors.append(f"missing:{cid}");continue
        for method in ("pixel","single","persistent"):
            if row.get(method)!=exp[method]: errors.append(f"decision:{cid}:{method}")
        if row.get("threshold_matches")!=exp["threshold_matches"]: errors.append(f"threshold_count:{cid}")
        if row.get("pixel_visits")!=exp["pixel_visits"]: errors.append(f"cost:{cid}")
        if row.get("application_effect")!="UNKNOWN" or row.get("semantic_oracle_used") is not False: errors.append(f"effect_promotion:{cid}")
        if row.get("scale")!=exp["scale"] or row.get("base_id")!=exp["base_id"]: errors.append(f"identity:{cid}")
    extras=set(ids)-set(expected_ids)
    if extras: errors.append("unexpected_case_ids")
    metrics={m:{"correct":0,"coverage":0,"false_confident":0} for m in ("pixel","single","persistent")}
    for cid,exp in expected.items():
        row=lookup.get(cid)
        if row is None: continue
        truth=exp["truth"]
        for method in metrics:
            value=row.get(method)
            if truth!="UNKNOWN":
                metrics[method]["coverage"]+=value!="UNKNOWN"
                metrics[method]["correct"]+=value==truth
                metrics[method]["false_confident"]+=value not in ("UNKNOWN",truth)
            elif value!="UNKNOWN": metrics[method]["false_confident"]+=1
    scale_pairs=[]
    for c in cases:
        a,b=lookup.get(f"{c['id']}@1x"),lookup.get(f"{c['id']}@2x")
        if not a or not b or any(a.get(k)!=b.get(k) for k in ("pixel","single","persistent","application_effect")):
            errors.append(f"scale_invariance:{c['id']}")
        else: scale_pairs.append(c["id"])
    for scale in (1,2):
        a,b=lookup.get(f"hidden_twin_visible@{scale}x",{}),lookup.get(f"hidden_twin_overpass@{scale}x",{})
        if any(a.get(k)!=b.get(k) for k in ("pixel","single","persistent","application_effect")):
            errors.append(f"hidden_twin_visual_output_mismatch:{scale}x")
    return errors,metrics,{"expected_ids":expected_ids,"scale_pairs":scale_pairs}


def main():
    spec=json.loads((ROOT/"fixtures_a03.json").read_text())
    labels={x["id"]:x for x in json.loads((ROOT/"labels_a03.json").read_text())["labels"]}
    raw=json.loads((OUT/"candidate.raw.json").read_text())
    rows=raw.get("rows",[])
    errors,metrics,detail=inspect_rows(rows,spec["cases"],labels,spec["palette"],spec["scales"],spec["thresholds"])
    attacks=[]
    mutations=[]
    omitted=copy.deepcopy(rows); omitted.pop(); mutations.append(("omitted_row",omitted))
    duplicate=copy.deepcopy(rows); duplicate.append(copy.deepcopy(duplicate[0])); mutations.append(("duplicate_id",duplicate))
    flipped=copy.deepcopy(rows); flipped[0]["persistent"]="ABSENT"; mutations.append(("flipped_decision",flipped))
    promoted=copy.deepcopy(rows); promoted[0]["application_effect"]="CONFIRMED"; mutations.append(("fabricated_effect",promoted))
    required_errors={
      "omitted_row": "missing:", "duplicate_id": "duplicate_case_id",
      "flipped_decision": "decision:route_connected@1x:persistent",
      "fabricated_effect": "effect_promotion:route_connected@1x"
    }
    for name,mutant in mutations:
        mutation_errors,_,_=inspect_rows(mutant,spec["cases"],labels,spec["palette"],spec["scales"],spec["thresholds"])
        marker=required_errors[name]
        attacks.append({"mutation":name,"rejected":bool(mutation_errors),"expected_error_detected":any(e.startswith(marker) for e in mutation_errors),"errors":mutation_errors})
    gate={
      "rows":len(rows),"expected_rows":len(detail["expected_ids"]),"errors":errors,"metrics":metrics,
      "determinate_cases_per_scale":7,"determinate_coverage":{m:f"{v['coverage']}/14" for m,v in metrics.items()},
      "false_confident":{m:v["false_confident"] for m,v in metrics.items()},
      "scale_pairs":detail["scale_pairs"],"mutation_controls":attacks,
      "all_mutations_rejected":len(attacks)==4 and all(x["rejected"] and x["expected_error_detected"] for x in attacks),
      "persistent_beats_both_baselines":metrics["persistent"]["false_confident"]<metrics["pixel"]["false_confident"] and metrics["persistent"]["false_confident"]<metrics["single"]["false_confident"],
      "application_effect":"UNKNOWN for all candidate rows"
    }
    (OUT/"audit.json").write_text(json.dumps(gate,sort_keys=True,indent=2)+"\n")
    if errors or not gate["all_mutations_rejected"] or not gate["persistent_beats_both_baselines"]: raise SystemExit(1)


if __name__=="__main__": main()
