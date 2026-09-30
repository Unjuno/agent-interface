from __future__ import annotations
import argparse, base64, hashlib, json, math
from pathlib import Path

MODEL="qwen2.5vl:3b"; DIGEST="fb90415cde1ef08aa669ae74b082d49b158729b6db1ab183c941417d507e71a1"
ARMS=["RAW","BORDER_RULER","COARSE_GRID","CONTEXT_CROP","GRID_CONTEXT"]
def sha(b): return hashlib.sha256(b).hexdigest()
def iou(a,b):
    if not isinstance(a,list) or len(a)!=4 or not all(type(x)==int for x in a): return 0.0
    x1,y1=max(a[0],b[0]),max(a[1],b[1]); x2,y2=min(a[2],b[2]),min(a[3],b[3]); inter=max(0,x2-x1)*max(0,y2-y1)
    aa=max(0,a[2]-a[0])*max(0,a[3]-a[1]); ab=max(0,b[2]-b[0])*max(0,b[3]-b[1]); u=aa+ab-inter; return inter/u if u else 0.0
def source_box(box,mapping):
    if not isinstance(box,list) or len(box)!=4: return None
    if mapping["kind"]=="identity": return box
    cx1,cy1,cx2,cy2=mapping["crop"]; px,py=mapping["paste_xy"]; rw,rh=mapping["resized_wh"]
    sx=(cx2-cx1)/rw; sy=(cy2-cy1)/rh
    return [round((box[0]-px)*sx+cx1),round((box[1]-py)*sy+cy1),round((box[2]-px)*sx+cx1),round((box[3]-py)*sy+cy1)]
def norm_region_distance(pred,target):
    if pred is None: return None
    cx=(pred[0]+pred[2])/2; cy=(pred[1]+pred[3])/2
    dx=max(target[0]-cx,0,cx-target[2]); dy=max(target[1]-cy,0,cy-target[3])
    return math.hypot(dx,dy)/math.hypot(1280,800)
def presentation_box(box,mapping):
    if box is None: return None
    if mapping["kind"]=="identity": return list(box)
    x1,y1,x2,y2=mapping["crop"]; px,py=mapping["paste_xy"]; rw,rh=mapping["resized_wh"]
    return [round(px+(box[0]-x1)*rw/(x2-x1)),round(py+(box[1]-y1)*rh/(y2-y1)),round(px+(box[2]-x1)*rw/(x2-x1)),round(py+(box[3]-y1)*rh/(y2-y1))]
def audit_inputs(data:Path):
    pre=json.loads((data/"PREFORMAL.json").read_text(encoding="utf-8")); errors=[]
    formal=pre.get("formal_cases",[]); construction=pre.get("construction_cases",[])
    if len(formal)!=60 or len({c["source_case_id"] for c in formal})!=12: errors.append("formal_denominator")
    if sum(c["present"] for c in formal if c["arm"]=="RAW")!=10 or sum(not c["present"] for c in formal if c["arm"]=="RAW")!=2: errors.append("formal_class_balance")
    if len(construction)!=10 or len({c["source_case_id"] for c in construction})!=2: errors.append("construction_denominator")
    formal_seeds={c["seed"] for c in formal}; construction_seeds={c["seed"] for c in construction}
    if formal_seeds & construction_seeds: errors.append("construction_seed_overlap")
    for c in formal+construction:
        try:
            src=(data/c["source_path"]).read_bytes(); img=(data/c["image_path"]).read_bytes()
            if sha(src)!=c["source_sha256"] or sha(img)!=c["image_sha256"]: errors.append("input_hash:"+c["case_id"])
            if c["mapping"]["kind"] not in ("identity","crop_resize"): errors.append("mapping_kind:"+c["case_id"])
            if c["target_box"] is not None:
                shown=presentation_box(c["target_box"],c["mapping"]); restored=source_box(shown,c["mapping"])
                if any(abs(a-b)>1 for a,b in zip(restored,c["target_box"])): errors.append("mapping_roundtrip:"+c["case_id"])
        except Exception: errors.append("input_record:"+c.get("case_id","unknown"))
    expected={"RAW","BORDER_RULER","COARSE_GRID","CONTEXT_CROP","GRID_CONTEXT"}
    groups={}
    for c in formal: groups.setdefault(c["source_case_id"],[]).append(c["arm"])
    if any(sorted(v)!=sorted(expected) for v in groups.values()): errors.append("formal_arm_balance")
    return {"schema":"visual-encoding-570-r5-input-audit-v1","formal_cases":len(formal),"construction_cases":len(construction),"formal_source_cases":len(groups),"construction_source_cases":len({c['source_case_id'] for c in construction}),"errors":errors,"decision":"CONSTRUCTION_AUDIT_PASS" if not errors else "STOP_INPUT_OR_MAPPING"}
def audit(root:Path):
    errors=[]; pre=json.loads((root/"data"/"PREFORMAL.json").read_text(encoding="utf-8")); base=json.loads((root/"baseline.json").read_text()); baseline=base.get("memory_used_mib")
    samples=[json.loads(x) for x in (root/"sampler.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]; by_arm={a:[] for a in ARMS}; by_case={}
    for c in pre["formal_cases"]:
        f=root/"formal"/(c["case_id"]+".json")
        if not f.is_file(): errors.append("missing:"+c["case_id"]); continue
        r=json.loads(f.read_text(encoding="utf-8")); img=(root/"data"/c["image_path"]).read_bytes(); src=(root/"data"/c["source_path"]).read_bytes()
        if sha(img)!=c["image_sha256"] or r.get("image_sha256")!=c["image_sha256"]: errors.append("image_hash:"+c["case_id"])
        if sha(src)!=c["source_sha256"] or r.get("source_sha256")!=c["source_sha256"]: errors.append("source_hash:"+c["case_id"])
        if r.get("case_id")!=c["case_id"] or r.get("arm")!=c["arm"] or r.get("mapping")!=c["mapping"]: errors.append("case_binding:"+c["case_id"])
        if r.get("model")!=MODEL or r.get("expected_digest")!=DIGEST: errors.append("model:"+c["case_id"])
        q=r.get("request",{}); opts=q.get("options",{})
        if q.get("model")!=MODEL or q.get("stream") is not False or opts!={"temperature":0,"seed":c["seed"],"num_predict":128}: errors.append("request:"+c["case_id"])
        if r.get("request_sha256")!=sha(json.dumps(q,sort_keys=True,separators=(",",":")).encode()): errors.append("request_hash:"+c["case_id"])
        expected_map={"kind":"identity"}
        if c["arm"]=="CONTEXT_CROP": expected_map={"kind":"crop_resize","crop":[40,130,1240,700],"paste_xy":[40,58],"resized_wh":[1200,684]}
        if c["arm"]=="GRID_CONTEXT": expected_map={"kind":"crop_resize","crop":[40,130,1240,700],"paste_xy":[40,130],"resized_wh":[1200,570],"grid_step_px":200}
        if c.get("mapping")!=expected_map: errors.append("mapping_contract:"+c["case_id"])
        msg=q.get("messages",[{}])[0]
        if msg.get("content")!=pre["prompt"]: errors.append("prompt:"+c["case_id"])
        try:
            if sha(base64.b64decode(msg["images"][0],validate=True))!=c["image_sha256"]: errors.append("request_image:"+c["case_id"])
            out=json.loads(r["response"]["message"]["content"])
        except Exception: errors.append("response_parse:"+c["case_id"]); continue
        if r.get("error"): errors.append("request_error:"+c["case_id"])
        if set(out)!={"present","box"} or type(out.get("present")) is not bool: errors.append("schema:"+c["case_id"]); continue
        mapped=source_box(out.get("box"),c["mapping"]) if out["present"] else None
        hit=out["present"] and iou(mapped,c["target_box"])>=.5 if c["present"] else False
        abstain=(not c["present"] and out["present"] is False and out.get("box") is None)
        distance=norm_region_distance(mapped,c["target_box"]) if c["present"] and mapped else (1.0 if c["present"] else None)
        start,end=r.get("started_utc_ns",0),r.get("ended_utc_ns",0); overlap=[s for s in samples if start<=s.get("utc_ns",-1)<=end]
        placed=[s for s in overlap if isinstance(s.get("memory_used_mib"),int) and isinstance(baseline,int) and s["memory_used_mib"]>baseline and "gpu" in s.get("ollama_ps_stdout","").lower()]
        if not placed: errors.append("gpu_placement:"+c["case_id"])
        row={"case_id":c["case_id"],"source_case_id":c["source_case_id"],"arm":c["arm"],"present":c["present"],"hit":bool(hit),"abstain":bool(abstain),"iou":iou(mapped,c["target_box"]) if c["present"] and mapped else None,"normalized_region_distance":distance,"positive_gpu_samples":len(placed),"prediction_source_frame":mapped}
        by_arm[c["arm"]].append(row); by_case.setdefault(c["source_case_id"],[]).append(row)
    if len(pre["formal_cases"])!=60 or any(len(v)!=12 for v in by_arm.values()): errors.append("denominator_or_arm_count")
    if len(by_case)!=12 or any(sorted(r["arm"] for r in rows)!=sorted(ARMS) for rows in by_case.values()): errors.append("case_arm_binding")
    arms={}
    for a,rows in by_arm.items():
        pos=[r for r in rows if r["present"]]; neg=[r for r in rows if not r["present"]]
        arms[a]={"positive_hits":sum(r["hit"] for r in pos),"positive_total":len(pos),"absent_abstentions":sum(r["abstain"] for r in neg),"absent_total":len(neg),"mean_normalized_region_distance":sum(r["normalized_region_distance"] for r in pos if r["normalized_region_distance"] is not None)/len(pos) if pos else None}
    raw=arms.get("RAW",{}); qualified=[]
    for a in ("COARSE_GRID","CONTEXT_CROP","GRID_CONTEXT"):
        x=arms.get(a,{})
        if x and x["positive_hits"]>=raw.get("positive_hits",999) and x["absent_abstentions"]>=raw.get("absent_abstentions",999) and raw.get("mean_normalized_region_distance") is not None and raw["mean_normalized_region_distance"]-x["mean_normalized_region_distance"]>=.05: qualified.append(a)
    complete=all(len(v)==12 for v in by_arm.values()) and len(pre["formal_cases"])==60
    decision="HOLD_AUDIT_OR_GPU_GATE" if errors or not complete else ("PASS_ENCODING_GAIN_SCOPED" if qualified else "REJECT_NO_MATERIAL_ENCODING_GAIN")
    return {"schema":"visual-encoding-570-r5-independent-audit-v1","allocation":pre.get("allocation"),"decision":decision,"formal_complete":complete,"errors":errors,"arms":arms,"qualified_encodings":qualified,"rows":{k:v for k,v in by_arm.items()},"case_arm_completeness":{k:sorted(r["arm"] for r in v) for k,v in by_case.items()}}
def main():
    p=argparse.ArgumentParser(); p.add_argument("--root",type=Path,required=True); p.add_argument("--out",type=Path); p.add_argument("--inputs-only",action="store_true"); a=p.parse_args(); result=audit_inputs(a.root) if a.inputs_only else audit(a.root); s=json.dumps(result,indent=2,sort_keys=True)+"\n"; a.out.write_text(s,encoding="utf-8") if a.out else None; print(s,end="")
if __name__=="__main__": main()
