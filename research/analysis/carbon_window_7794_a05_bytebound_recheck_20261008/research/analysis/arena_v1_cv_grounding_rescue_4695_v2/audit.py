#!/usr/bin/env python3
"""Independent oracle for v1 regression and v2 held-out panels; no detector imports."""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path
from PIL import Image
COLOR=(249,115,22); TOL=8; AREA_MIN,AREA_MAX=1600,12000; FILL_MIN=.86; AR_MIN,AR_MAX=.84,1.19

def eligible_boxes(path):
    im=Image.open(path).convert("RGB"); w,h=im.size; px=im.load(); seen=bytearray(w*h); boxes=[]
    for y in range(h):
      for x in range(w):
        st=y*w+x; p=px[x,y]
        if seen[st] or any(abs(p[k]-COLOR[k])>TOL for k in range(3)): continue
        stack=[(x,y)]; seen[st]=1; xs=[]; ys=[]
        while stack:
          cx,cy=stack.pop(); xs.append(cx); ys.append(cy)
          for nx,ny in ((cx-1,cy),(cx+1,cy),(cx,cy-1),(cx,cy+1)):
            if 0<=nx<w and 0<=ny<h:
              ni=ny*w+nx; q=px[nx,ny]
              if not seen[ni] and all(abs(q[k]-COLOR[k])<=TOL for k in range(3)):
                seen[ni]=1; stack.append((nx,ny))
        x0,x1,y0,y1=min(xs),max(xs)+1,min(ys),max(ys)+1; bw,bh=x1-x0,y1-y0; area=len(xs)
        if AREA_MIN<=area<=AREA_MAX and AR_MIN<=bw/bh<=AR_MAX and area/(bw*bh)>=FILL_MIN: boxes.append([x0,y0,x1,y1])
    return sorted(boxes)

def iou(a,b):
    ix=max(0,min(a[2],b[2])-max(a[0],b[0])); iy=max(0,min(a[3],b[3])-max(a[1],b[1])); inter=ix*iy
    union=(a[2]-a[0])*(a[3]-a[1])+(b[2]-b[0])*(b[3]-b[1])-inter
    return inter/union if union else 0.0

def audit(roots, manifests, predictions):
    errors=[]; expected=[]; by_id={}
    for root,manifest in zip(roots,manifests):
      for item in manifest["rows"]:
        expected.append(item); by_id[item["id"]]=(root,item)
    ids=[x["id"] for x in expected]; rows=predictions.get("rows",[]); got=[x.get("id") for x in rows]
    if len(ids)!=len(set(ids)) or len(got)!=len(set(got)) or got!=ids: errors.append("identity_or_denominator_mismatch")
    pred={r.get("id"):r for r in rows if isinstance(r,dict)}; positives=[]; controls=[]; ious={}
    for item in expected:
      rid=item["id"]; root,_=by_id[rid]
      if "file" in item: path=root/item["file"]
      elif (root/"panels").is_dir(): path=root/"panels"/f"{rid}.png"
      else: path=root/f"{rid}.png"
      if not path.is_file(): errors.append(f"input_missing:{rid}"); continue
      if hashlib.sha256(path.read_bytes()).hexdigest()!=item["sha256"]: errors.append(f"input_hash_mismatch:{rid}")
      found=eligible_boxes(path); row=pred.get(rid)
      if row is None: errors.append(f"prediction_missing:{rid}"); continue
      status=row.get("status"); reported=row.get("box_xyxy") if status=="PROPOSAL" else None
      kind=item["kind"]
      if kind.startswith("positive"):
        truth=item.get("expected_box_xyxy"); score=iou(truth,reported) if isinstance(reported,list) else 0.0; ious[rid]=score
        if len(found)!=1 or status!="PROPOSAL" or score<.95: errors.append(f"positive_localization_or_structure:{rid}")
        else: positives.append(rid)
      elif kind=="ambiguous-multiple-squares":
        if len(found)<2 or status!="ABSTAIN" or reported is not None: errors.append(f"ambiguous_not_abstained_or_structure:{rid}")
        elif row.get("candidate_count")!=len(found): errors.append(f"ambiguous_candidate_count_mismatch:{rid}")
        else: controls.append(rid)
      else:
        if len(found)!=0 or status!="ABSTAIN" or reported is not None: errors.append(f"absent_or_nonsquare_not_abstained:{rid}")
        elif row.get("candidate_count")!=0: errors.append(f"control_candidate_count_mismatch:{rid}")
        else: controls.append(rid)
    retained=pred.get("case-01-retained-arena",{}); point=retained.get("source_point_xy"); box=retained.get("box_xyxy")
    retained_item=next((x for x in expected if x["id"]=="case-01-retained-arena"),{})
    width=retained_item.get("width",720); height=retained_item.get("height",520)
    if point!=[920,640] or point[0]<0 or point[1]<0 or point[0]<width and point[1]<height or not isinstance(box,list): errors.append("retained_out_of_bounds_source_not_preserved")
    return {"outcome":"PASS_SCOPED_HELDOUT" if not errors else "FAIL_OR_HOLD","rows":len(rows),"positives":positives,"controls_abstained":controls,"ious":ious,"errors":errors}

def main():
    if len(sys.argv)!=5: raise SystemExit("usage: audit.py v1-dir v2-dir predictions.json report.json")
    roots=[Path(sys.argv[1]),Path(sys.argv[2])]; manifests=[json.loads((r/"manifest.json").read_text(encoding="utf-8")) for r in roots]
    preds=json.loads(Path(sys.argv[3]).read_text(encoding="utf-8")); result=audit(roots,manifests,preds)
    Path(sys.argv[4]).write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8"); print(json.dumps(result,indent=2))
    raise SystemExit(0 if not result["errors"] else 1)
if __name__=="__main__": main()
