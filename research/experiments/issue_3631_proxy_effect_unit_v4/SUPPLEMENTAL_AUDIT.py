"""Post-formal independent cross-checks beyond the frozen primary audit."""
import hashlib
import json
from pathlib import Path

OUT=Path("/evidence")
def sha(b): return hashlib.sha256(b).hexdigest()
def loadrel(s):
    p=Path(s)
    if p.is_absolute() or ".." in p.parts: raise ValueError("unsafe evidence path")
    return (OUT/p).read_bytes()
def center(r): return [r["x"]+r["width"]//2,r["y"]+r["height"]//2]
def ppm(b):
    a=b.split(b"\n",3)
    if len(a)!=4 or a[0]!=b"P6" or a[2]!=b"255": raise ValueError("bad PPM")
    w,h=map(int,a[1].split());rgb=a[3]
    if len(rgb)!=w*h*3: raise ValueError("bad PPM length")
    return w,h,rgb
def blue_center(w,h,rgb):
    xs=[];ys=[]
    for y in range(h):
        for x in range(w):
            i=(y*w+x)*3;r,g,b=rgb[i:i+3]
            if r<70 and 80<=g<=145 and 130<=b<=205 and b>r+70:xs.append(x);ys.append(y)
    if not xs:raise ValueError("no blue target")
    return [(min(xs)+max(xs)+1)//2,(min(ys)+max(ys)+1)//2]

raw=json.loads((OUT/"raw.json").read_text());errors=[];checked=0
for row in raw["rows"]:
    checked+=1;label=f'{row["arm"]}/{row["case"]}';arm=row["arm"];case=row["case"]
    initial=row["initial_state"];current=row["current_state"];req=row["request"];pres=row["presentation"]
    token=req["source_token"]
    for k in ("xid","pid","start_ticks","counter","version","title","geometry","rgb_sha256"):
        if token.get(k)!=initial.get(k):errors.append(f"{label}: request source token mismatch {k}")
    if case in ("positive","no_effect","macro_failure"):
        for k in ("xid","pid","start_ticks","counter","version","title","geometry","rgb_sha256"):
            if current.get(k)!=token.get(k):errors.append(f"{label}: current action binding mismatch {k}")
    if case=="stale_version" and current.get("version")==token.get("version"):errors.append(f"{label}: version was not stale")
    if case=="target_replaced" and (current.get("pid"),current.get("start_ticks"))==(token.get("pid"),token.get("start_ticks")):errors.append(f"{label}: process incarnation was not replaced")
    rect=initial["ready_event"]["button_rect"]
    expected_struct={"target":initial["xid"],"pid":initial["pid"],"start_ticks":initial["start_ticks"],"counter":initial["counter"],"version":initial["version"],"operation":"increment","control":rect}
    try:
        if arm=="ordinary_screenshot":
            b=loadrel(pres["input_path"])
            if pres["input_path"]!=initial["rgb_path"] or sha(b)!=initial["rgb_sha256"]:errors.append(f"{label}: screenshot not bound to actual assigned frame")
            if len(b)!=initial["width"]*initial["height"]*3:errors.append(f"{label}: screenshot dimensions mismatch")
            xy=blue_center(initial["width"],initial["height"],b); ih=sha(b)
        elif arm=="proxy_image":
            b=loadrel(pres["input_path"]);w,h,rgb=ppm(b);xy=blue_center(w,h,rgb);ih=sha(b)
            if (w,h)!=(initial["width"],initial["height"]):errors.append(f"{label}: proxy geometry mismatch")
            if xy!=center(rect):errors.append(f"{label}: proxy image target not bound to structured control")
        elif arm=="structured_proxy":
            b=loadrel(pres["input_path"]);spec=json.loads(b);xy=center(spec["control"]);ih=sha(b)
            if spec!=expected_struct:errors.append(f"{label}: structured representation does not bind target/process/state")
        else:
            ib,sb=(loadrel(p) for p in pres["input_paths"]);w,h,rgb=ppm(ib);ixy=blue_center(w,h,rgb);spec=json.loads(sb);sxy=center(spec["control"]);xy=sxy
            combo={"proxy_image_sha256":sha(ib),"structured_sha256":sha(sb)}
            ih=sha(json.dumps(combo,sort_keys=True,separators=(",",":")).encode())
            if spec!=expected_struct:errors.append(f"{label}: hybrid structured state not target-bound")
            if ixy!=sxy or ixy!=center(rect):errors.append(f"{label}: hybrid inputs do not independently agree")
            if (w,h)!=(initial["width"],initial["height"]):errors.append(f"{label}: hybrid image geometry mismatch")
        if ih!=pres["input_sha256"] or ih!=req["representation_sha256"] or ih!=req["derived_from_sha256"]:errors.append(f"{label}: recomputed representation hash mismatch")
        if xy!=pres["coordinate"] or xy!=req["derived_coordinate"]:errors.append(f"{label}: recomputed action coordinate mismatch")
        if pres.get("input_bytes")!= (len(b) if arm!="hybrid" else len(ib)+len(sb)):errors.append(f"{label}: representation byte count mismatch")
    except Exception as exc:errors.append(f"{label}: supplemental representation check failed: {exc}")

result={"decision":"PASS_SUPPLEMENTAL_CROSS_BINDING_AUDIT" if not errors else "HOLD_SUPPLEMENTAL_CROSS_BINDING_AUDIT","rows_checked":checked,"raw_sha256":sha((OUT/"raw.json").read_bytes()),"errors":errors}
(Path("/audit")/"supplemental_audit.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
print(json.dumps(result,sort_keys=True))
if errors:raise SystemExit(1)
