"""Independent raw-only replay audit; intentionally does not import candidate.py or ppm.py."""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).parent
SPEC = json.loads((ROOT / "fixtures.json").read_text())
FREEZE = json.loads((ROOT / "FREEZE.json").read_text())

def digest(b): return hashlib.sha256(b).hexdigest()

def parse(raw):
    parts = raw.split(b"\n", 3)
    if len(parts) != 4 or parts[0] != b"P6" or parts[2] != b"255": raise ValueError("bad ppm")
    w, h = map(int, parts[1].split()); px = parts[3]
    if len(px) != w*h*3: raise ValueError("bad pixel count")
    return w, h, px

def reconstruct(raw, r):
    w, h, px = parse(raw); x0,y0,x1,y1 = r
    if not (0 <= x0 < x1 <= w and 0 <= y0 < y1 <= h): raise ValueError("crop out of bounds")
    body=b"".join(px[(y*w+x0)*3:(y*w+x1)*3] for y in range(y0,y1))
    return f"P6\n{x1-x0} {y1-y0}\n255\n".encode()+body

def contained(outer, inner):
    x0,y0,x1,y1=outer; a,b,c,d=inner
    return x0<=a and y0<=b and x1>=c and y1>=d

def audit(outdir):
    if FREEZE.get("status") != "AUTHORIZED" or not FREEZE.get("resource_assignment_record"):
        return {"schema":"visual-presentation-t0-audit-v1","passed":False,"rows":0,
                "errors":["missing exact #5085 assignment"],"decision":"STOP_UNASSIGNED"}
    frozen_errors=[]
    for rel, expected_hash in FREEZE["source_sha256"].items():
        try: actual_hash=digest((ROOT/rel).read_bytes())
        except Exception: frozen_errors.append("missing frozen source: "+rel); continue
        if actual_hash!=expected_hash: frozen_errors.append("frozen source hash mismatch: "+rel)
    if frozen_errors:
        return {"schema":"visual-presentation-t0-audit-v1","passed":False,"rows":0,
                "errors":frozen_errors,"decision":"FAIL_FROZEN_SOURCE"}
    out=Path(outdir); doc=json.loads((out/"candidate.json").read_text())
    expected={(c,a) for c in SPEC["conditions"] for a in SPEC["arms"]}
    expected|={(c,"CROP_ONLY_NEGATIVE:"+n["name"]) for c in SPEC["conditions"] for n in SPEC["negative_crops"]}
    seen=set(); errors=[]
    for row in doc.get("rows",[]):
        key=(row.get("condition"), row.get("arm") if row.get("arm")!="CROP_ONLY_NEGATIVE" else "CROP_ONLY_NEGATIVE:"+row.get("negative",""))
        if key in seen: errors.append("duplicate row")
        seen.add(key)
        cond,arm=key
        src=(ROOT/"sources"/(str(cond)+".ppm")).read_bytes()
        sw,sh,_=parse(src); shash=digest(src)
        if row.get("source_sha256")!=shash or row.get("source_dimensions")!=[sw,sh]: errors.append("source identity mismatch")
        if arm.startswith("CROP_ONLY_NEGATIVE:"):
            neg=next((n for n in SPEC["negative_crops"] if n["name"]==arm.split(":",1)[1]),None)
            hides_required=bool(neg) and not all(contained(neg["rectangle"],SPEC["required_regions"][k]) for k in ("task_target","safety_cue"))
            if not neg or row.get("rectangle")!=neg["rectangle"] or not hides_required or row.get("accepted") is not False or row.get("reason")!="required_region_hidden" or row.get("views")!=[]: errors.append("negative refusal mismatch")
            continue
        views=row.get("views",[])
        spec_views={"FULL":[("full",None)],"FULL+CONTEXT_CROP":[("full",None),("context",SPEC["context_crop"])],
                    "CROP_ONLY":[("crop",SPEC["context_crop"])],"SHAM_CROP":[("full",None),("sham",SPEC["sham_crop"])]}[arm]
        if len(views)!=len(spec_views): errors.append("view count mismatch"); continue
        for v,(label,rect) in zip(views,spec_views):
            expected_raw=src if rect is None else reconstruct(src,rect)
            try: actual=(out/v["file"]).read_bytes()
            except Exception: errors.append("missing view bytes"); continue
            ew,eh,_=parse(expected_raw)
            if v.get("label")!=label or actual!=expected_raw or v.get("sha256")!=digest(expected_raw) or [v.get("width"),v.get("height")]!=[ew,eh]: errors.append("view provenance mismatch")
        should_accept=arm!="CROP_ONLY" or all(contained(SPEC["context_crop"],SPEC["required_regions"][k]) for k in ("task_target","safety_cue"))
        if row.get("accepted") is not should_accept or row.get("reason")!=("accepted" if should_accept else "required_region_hidden"): errors.append("acceptance/visibility mismatch")
    if seen!=expected: errors.append("missing or unexpected rows")
    return {"schema":"visual-presentation-t0-audit-v1","passed":not errors,"rows":len(seen),"errors":errors,
            "decision":"PASS_METHOD_SCOPED" if not errors else "FAIL"}

if __name__=="__main__":
    result=audit(sys.argv[1]); print(json.dumps(result,sort_keys=True)); raise SystemExit(0 if result["passed"] else 1)
