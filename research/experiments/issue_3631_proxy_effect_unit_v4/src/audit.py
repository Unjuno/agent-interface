"""Independent file-level auditor; intentionally imports neither runner nor proxy."""
import copy
import hashlib
import json
from pathlib import Path

OUT=Path("/evidence")
SRC=Path("/src")
AUDIT_OUT=Path("/audit")
ARMS=("ordinary_screenshot","proxy_image","structured_proxy","hybrid")
CASES=("positive","no_effect","stale_version","target_replaced","unavailable","ambiguous","macro_failure")
DECISIONS={"positive":"COMPLETED","no_effect":"YIELD_NO_APPLICATION_EFFECT",
 "stale_version":"REFUSE_STALE_BINDING","target_replaced":"REFUSE_STALE_BINDING",
 "unavailable":"YIELD_TARGET_UNAVAILABLE","ambiguous":"YIELD_TARGET_AMBIGUOUS",
 "macro_failure":"YIELD_MACRO_FAILURE"}

def digest(data): return hashlib.sha256(data).hexdigest()
def center(r): return [r["x"]+r["width"]//2,r["y"]+r["height"]//2]
def ppm(data):
    parts=data.split(b"\n",3)
    if len(parts)!=4 or parts[0]!=b"P6" or parts[2]!=b"255": raise ValueError("bad PPM")
    w,h=map(int,parts[1].split()); rgb=parts[3]
    if len(rgb)!=w*h*3: raise ValueError("bad PPM byte length")
    return w,h,rgb
def bbox(w,h,rgb):
    xs=[];ys=[]
    for y in range(h):
        for x in range(w):
            i=(y*w+x)*3;r,g,b=rgb[i:i+3]
            if r<70 and 80<=g<=145 and 130<=b<=205 and b>r+70: xs.append(x);ys.append(y)
    if not xs: raise ValueError("no blue target pixels")
    return {"x":min(xs),"y":min(ys),"width":max(xs)-min(xs)+1,"height":max(ys)-min(ys)+1}
def read_rel(path):
    p=Path(path)
    if p.is_absolute() or ".." in p.parts: raise ValueError("non-relative evidence path")
    return (OUT/p).read_bytes()

def validate(raw):
    errors=[]; rows=raw.get("rows")
    if not isinstance(rows,list) or len(rows)!=28:return ["expected exactly 28 rows"]
    expected={(a,c) for a in ARMS for c in CASES}
    observed={(r.get("arm"),r.get("case")) for r in rows}
    if observed!=expected or len(observed)!=len(rows):errors.append("matrix denominator/identity mismatch")
    if raw.get("issue")!=3631 or raw.get("allocation_id")!="issue3631-proxy-effect-unit-formal-04":errors.append("allocation identity mismatch")
    if raw.get("canonical_output_path")!="evidence/formal-04":errors.append("canonical evidence path mismatch")
    if raw.get("image_id")!="sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27" or raw.get("platform")!="linux/arm64":errors.append("runtime image/platform mismatch")
    if raw.get("formal_invocations")!=1 or raw.get("retries")!=0:errors.append("formal one-shot count mismatch")
    for row in rows:
        label=f'{row.get("arm")}/{row.get("case")}'; case=row.get("case")
        if row.get("error") is not None:errors.append(f"{label}: runner error");continue
        if row.get("decision")!=DECISIONS.get(case):errors.append(f"{label}: decision mismatch")
        if row.get("release_verified") is not True or not row.get("release_observation",{}).get("verified"):errors.append(f"{label}: release observer missing/pressed")
        if not row.get("socket_disappeared"):errors.append(f"{label}: Xvfb socket remained")
        if row.get("reply",{}).get("decision")!=row.get("decision"):errors.append(f"{label}: reply mismatch")
        if row.get("reply",{}).get("emissions")!=row.get("emissions"):errors.append(f"{label}: reply emission mismatch")
        processes=row.get("processes",[]); exits=row.get("process_exit_codes",{})
        if len(exits)!=len(processes) or any(v not in (0,-15,-9) for v in exits.values()):errors.append(f"{label}: unreaped or unaccounted process")
        ev=row.get("fixture_events",[])
        event_path=OUT/"rows"/row.get("row_id","")/"fixture-events.jsonl"
        if not event_path.is_file() or digest(event_path.read_bytes())!=row.get("fixture_events_sha256"):errors.append(f"{label}: event bytes/hash mismatch")
        app_procs=sorted(p.get("pid") for p in processes if p.get("role") in {"fixture","fixture_replacement","duplicate_fixture"})
        ready=sorted(e.get("pid") for e in ev if e.get("kind")=="ready")
        if app_procs!=ready:errors.append(f"{label}: fixture process/event owner mismatch")
        ack=sum(e.get("kind")=="click_ack" for e in ev); effects=sum(e.get("kind")=="effect" for e in ev)
        if ack!=row.get("emissions") or bool(ack)!=bool(row.get("input_ack")):errors.append(f"{label}: input emission/ack mismatch")
        if effects!=(1 if case=="positive" else 0):errors.append(f"{label}: task effect count mismatch")
        initial=row.get("initial_state",{}); current=row.get("current_state",{}); after=row.get("after_state",{})
        token={k:initial.get(k) for k in ("xid","pid","start_ticks","counter","version","title","geometry","rgb_sha256")}
        request=row.get("request",{})
        if request.get("source_token")!=token:errors.append(f"{label}: source token not bound to observed state")
        if request.get("source_frame_sha256")!=initial.get("rgb_sha256"):errors.append(f"{label}: source frame binding mismatch")
        if request.get("representation_arm")!=row.get("arm"):errors.append(f"{label}: arm binding mismatch")
        if initial.get("status")!="ok":errors.append(f"{label}: initial target absent")
        else:
            xres=initial.get("xres",{}); proc=initial.get("process",{}); ready_owner=initial.get("ready_event",{})
            if xres.get("pid")!=initial.get("pid") or proc.get("pid")!=initial.get("pid") or ready_owner.get("pid")!=initial.get("pid"):errors.append(f"{label}: XID-to-process owner mismatch")
            if proc.get("start_ticks")!=initial.get("start_ticks") or not proc.get("stable_read"):errors.append(f"{label}: process incarnation unstable")
            for state_name,state in (("initial",initial),("current",current),("after",after)):
                if state.get("status")!="ok":continue
                try:
                    frame=read_rel(state["frame_path"]); rgb=read_rel(state["rgb_path"])
                    if digest(frame)!=state["frame_sha256"] or len(frame)!=state["frame_bytes"]:errors.append(f"{label}: {state_name} XImage hash/length mismatch")
                    if digest(rgb)!=state["rgb_sha256"] or len(rgb)!=state["rgb_bytes"] or len(rgb)!=state["width"]*state["height"]*3:errors.append(f"{label}: {state_name} RGB hash/length mismatch")
                except Exception as exc:errors.append(f"{label}: {state_name} image evidence missing: {exc}")
        presentation=row.get("presentation",{}); arm=row.get("arm")
        try:
            if arm=="ordinary_screenshot":
                data=read_rel(presentation["input_path"]); w=initial["width"];h=initial["height"];rgb=data
                input_hash=digest(data); coord=center(bbox(w,h,rgb))
            elif arm=="proxy_image":
                data=read_rel(presentation["input_path"]);w,h,rgb=ppm(data);input_hash=digest(data);coord=center(bbox(w,h,rgb))
            elif arm=="structured_proxy":
                data=read_rel(presentation["input_path"]); spec=json.loads(data);input_hash=digest(data);coord=center(spec["control"])
                if spec!={"target":initial["xid"],"pid":initial["pid"],"start_ticks":initial["start_ticks"],"counter":initial["counter"],"version":initial["version"],"operation":"increment","control":initial["ready_event"]["button_rect"]}:errors.append(f"{label}: structured state not bound to fixture")
            elif arm=="hybrid":
                ipath,spath=presentation["input_paths"]; image=read_rel(ipath);struct=read_rel(spath);w,h,rgb=ppm(image);image_coord=center(bbox(w,h,rgb));spec=json.loads(struct);coord=center(spec["control"])
                combined={"proxy_image_sha256":digest(image),"structured_sha256":digest(struct)}
                input_hash=digest(json.dumps(combined,sort_keys=True,separators=(",",":")).encode())
                if image_coord!=coord or presentation.get("image_coordinate")!=image_coord or presentation.get("structured_coordinate")!=coord:errors.append(f"{label}: hybrid derivations disagree")
            else:raise ValueError("unknown representation")
            if input_hash!=presentation.get("input_sha256") or input_hash!=request.get("representation_sha256"):errors.append(f"{label}: representation input hash mismatch")
            if coord!=presentation.get("coordinate") or coord!=request.get("derived_coordinate"):errors.append(f"{label}: derived coordinate mismatch")
            if request.get("derived_from_sha256")!=input_hash:errors.append(f"{label}: derived input binding mismatch")
        except Exception as exc:errors.append(f"{label}: representation audit failed: {exc}")
        if case=="positive":
            if (initial.get("counter"),after.get("counter"),after.get("version"))!=(0,1,initial.get("version",0)+1):errors.append(f"{label}: exact positive effect mismatch")
            if initial.get("rgb_sha256")==after.get("rgb_sha256"):errors.append(f"{label}: positive frame unchanged")
        elif case=="no_effect":
            if ack!=1 or after.get("counter")!=0:errors.append(f"{label}: acknowledgement-only control invalid")
        else:
            if ack or row.get("emissions") or effects:errors.append(f"{label}: negative case emitted or affected task")
        if case=="stale_version" and current.get("version")==initial.get("version"):errors.append(f"{label}: stale mutation missing")
        if case=="target_replaced" and (current.get("pid"),current.get("start_ticks"))==(initial.get("pid"),initial.get("start_ticks")):errors.append(f"{label}: replacement incarnation missing")
        if case=="unavailable" and current.get("status")!="unavailable":errors.append(f"{label}: unavailable setup missing")
        if case=="ambiguous":
            setup=row.get("ambiguous_setup",{});ids=[t.get("xid") for t in setup.get("targets",[])]
            if setup.get("status")!="ambiguous" or setup.get("count")!=2 or len(set(ids))!=2 or len(set(setup.get("ready_pids",[])))!=2:errors.append(f"{label}: synchronized two-target gate missing")
            if current.get("status")!="ambiguous" or after.get("status")!="ambiguous":errors.append(f"{label}: ambiguity not retained at dispatch/after")
    return errors

def challenge(raw):
    checks=[]
    mutations=[
      ("missing-row",lambda x:x["rows"].pop()),
      ("xres-owner-forgery",lambda x:next(r for r in x["rows"] if r["case"]=="positive").update(initial_state={**next(r for r in x["rows"] if r["case"]=="positive")["initial_state"],"xres":{"pid":999999}})),
      ("derived-coordinate-forgery",lambda x:next(r for r in x["rows"] if r["arm"]=="proxy_image" and r["case"]=="positive")["presentation"].update(coordinate=[1,1])),
      ("wrong-output-path",lambda x:x.update(canonical_output_path="evidence/alias")),
      ("stale-admission",lambda x:next(r for r in x["rows"] if r["case"]=="stale_version").update(emissions=1)),
      ("ambiguity-removed",lambda x:next(r for r in x["rows"] if r["case"]=="ambiguous").update(ambiguous_setup={})),
      ("release-pressed",lambda x:next(r for r in x["rows"] if r["case"]=="positive").update(release_verified=False)),
    ]
    for name,mutate in mutations:
        candidate=copy.deepcopy(raw);mutate(candidate);checks.append({"name":name,"detected":bool(validate(candidate))})
    return checks

def main():
    raw_bytes=(OUT/"raw.json").read_bytes();raw=json.loads(raw_bytes);errors=validate(raw)
    frozen=json.loads(Path("/freeze.json").read_text());manifest_bytes=Path("/source_manifest.json").read_bytes();manifest=json.loads(manifest_bytes)
    prereg=Path("/preregistration.md").read_bytes()
    claimed=raw.get("result_sha256");payload=dict(raw);payload.pop("result_sha256",None)
    if digest(json.dumps(payload,sort_keys=True,separators=(",",":")).encode())!=claimed:errors.append("raw self-hash mismatch")
    if digest(Path("/freeze.json").read_bytes())!=raw.get("freeze_sha256"):errors.append("freeze hash mismatch")
    if digest(manifest_bytes)!=raw.get("source_manifest_sha256"):errors.append("manifest hash mismatch")
    if digest(prereg)!=raw.get("preregistration_sha256"):errors.append("preregistration hash mismatch")
    if frozen.get("source_commit")!=raw.get("source_commit") or frozen.get("image_id")!=raw.get("image_id"):errors.append("freeze/runtime identity mismatch")
    if frozen.get("preregistration_sha256")!=digest(prereg) or frozen.get("source_manifest_sha256")!=digest(manifest_bytes):errors.append("freeze preregistration/manifest binding mismatch")
    if digest(Path("/formal_launch.sh").read_bytes())!=frozen.get("formal_launch_sha256"):errors.append("launcher freeze hash mismatch")
    for name,want in manifest.get("files",{}).items():
        if not (SRC/name).is_file() or digest((SRC/name).read_bytes())!=want:errors.append(f"frozen source mismatch: {name}")
    controls=challenge(raw)
    if not all(c["detected"] for c in controls):errors.append("independent corruption challenge escaped")
    result={"decision":"PASS_INDEPENDENT_AUDIT" if not errors else "HOLD_OR_FAIL_INDEPENDENT_AUDIT","rows":len(raw.get("rows",[])),"raw_sha256":digest(raw_bytes),"errors":errors,"corruption_controls":controls}
    (AUDIT_OUT/"audit.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n");print(json.dumps(result,sort_keys=True))
    if errors:raise SystemExit(1)

if __name__=="__main__":main()
