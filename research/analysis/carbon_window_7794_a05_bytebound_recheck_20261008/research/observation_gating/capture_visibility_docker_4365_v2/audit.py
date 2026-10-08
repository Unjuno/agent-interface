from __future__ import annotations
import argparse,hashlib,json,struct
from pathlib import Path

IMAGE_ID="sha256:acf83a1dfafd43c44d81e2f28f85fc844fa43dc73f36b689a862dd924f9235d0"
CONDITIONS=("CLEAR","SIBLING_HALF","SIBLING_FULL","CHILD_HALF","CHILD_FULL","RESTORED")
PARENT=(43,57,120,80); PARENT_PIXEL=0x204060; CHILD_PIXEL=0xE0A040; SIBLING_PIXEL=0x20C0E0

def loadj(p): return json.loads(p.read_text(encoding="utf-8"))
def loadjl(p): return [json.loads(s) for s in p.read_text(encoding="utf-8").splitlines() if s]
def err(errors,name): errors.append(name)
def pixels(raw,w,h,layout):
    bpp=int(layout["bits_per_pixel"]); pad=int(layout["scanline_pad"]); order=int(layout["byte_order"])
    if bpp not in (16,24,32) or pad not in (8,16,32): raise ValueError("unsupported XImage format")
    pxbytes=(bpp+7)//8; stride=((w*bpp+pad-1)//pad)*(pad//8)
    if len(raw)!=stride*h: raise ValueError("raw image length does not match XImage stride")
    endian="little" if order==0 else "big"
    out=[]
    for y in range(h):
        line=[]
        for x in range(w):
            i=y*stride+x*pxbytes
            line.append(int.from_bytes(raw[i:i+pxbytes],endian))
        out.append(line)
    return out
def check_raw(root,cap,expected_pixel,errors,label,mask):
    art=cap.get("artifact")
    if cap.get("status")!="CAPTURED" or not isinstance(art,dict): err(errors,label+":missing_artifact");return None
    rel=Path(art.get("path",""))
    if rel.is_absolute() or ".." in rel.parts: err(errors,label+":unsafe_path");return None
    p=root/rel
    if not p.is_file(): err(errors,label+":missing_raw");return None
    raw=p.read_bytes()
    if len(raw)!=art.get("bytes") or hashlib.sha256(raw).hexdigest()!=art.get("sha256") or cap.get("sha256")!=art.get("sha256"):
        err(errors,label+":raw_digest")
    if cap.get("bytes")!=len(raw): err(errors,label+":capture_length")
    w,h=int(cap["width"]),int(cap["height"])
    try: pix=pixels(raw,w,h,art)
    except Exception as exc: err(errors,label+":pixel_decode:"+type(exc).__name__);return None
    if expected_pixel is not None and any((v&mask)!=(expected_pixel&mask) for row in pix for v in row): err(errors,label+":pixel_value_mismatch")
    return pix
def audit(root,source,manifest_path):
    errors=[]; manifest=loadj(manifest_path)
    for name,want in manifest.items():
        got=hashlib.sha256((source/name).read_bytes()).hexdigest()
        if got!=want: err(errors,"source_sha:"+name)
    result=loadj(root/"result.json"); rows=loadjl(root/"cases.jsonl"); environment=loadj(root/"environment.json")
    if result.get("image_id")!=IMAGE_ID: err(errors,"image_id")
    if environment.get("image_id")!=IMAGE_ID or environment.get("network_expected")!="none" or environment.get("gpu_used") is not False or len(environment.get("xvfb_binary_sha256",""))!=64:
        err(errors,"environment_provenance")
    if len(rows)!=12 or result.get("sessions_total")!=12: err(errors,"case_count")
    keys={(r.get("condition"),r.get("replicate")) for r in rows}
    expected={(c,r) for c in CONDITIONS for r in (1,2)}
    if keys!=expected: err(errors,"condition_replicates")
    clear_count=unknown_count=0; attempts=0; raw_errors=0; pixel_checks=0
    xfail=[]
    for r in rows:
        idx=r.get("case_index"); cond=r.get("condition"); rep=r.get("replicate")
        if r.get("status")!="COMPLETE": err(errors,f"case_status:{idx}")
        if r.get("map_state")!=2: err(errors,f"map_state:{idx}")
        ev=r.get("visibility_events",[])
        if not ev or r.get("visibility") not in (0,1,2) or r.get("visibility")!=ev[-1]:
            err(errors,f"visibility_receipt:{idx}")
        if r.get("coverage_complete") is not True: err(errors,f"coverage:{idx}")
        if not r.get("x_socket_absent_after_cleanup") or not r.get("xauthority_removed_after_cleanup"):
            err(errors,f"cleanup:{idx}")
        if r.get("server_alive_before_cleanup") is not True or not isinstance(r.get("xvfb_exit_code"),int):
            err(errors,f"server_receipt:{idx}")
        if len(r.get("captures",[]))!=2: err(errors,f"capture_attempt_count:{idx}");continue
        cap_by={c.get("frame"):c for c in r["captures"]}
        if set(cap_by)!={"screen_physical_px","window_client"}: err(errors,f"capture_frames:{idx}");continue
        attempts+=2
        rootcap=cap_by["screen_physical_px"]
        # A top-level sibling overlays root pixels. A direct child overlays only the root image, not the parent drawable.
        rootpix=check_raw(root,rootcap,None,errors,f"root:{idx}",0)
        if rootcap.get("status")=="CAPTURED" and rootpix is not None:
            art=rootcap["artifact"]; masks=art["masks"]; fullmask=int(masks[0])|int(masks[1])|int(masks[2])
            gx,gy,gw,gh=PARENT
            sib=(cond=="SIBLING_HALF","SIBLING_FULL")
            child=(cond=="CHILD_HALF","CHILD_FULL")
            for yy in range(gh):
                for xx in range(gw):
                    exp=PARENT_PIXEL
                    if cond=="SIBLING_HALF" and xx>=60: exp=SIBLING_PIXEL
                    if cond=="SIBLING_FULL": exp=SIBLING_PIXEL
                    if cond=="CHILD_HALF" and xx>=60: exp=CHILD_PIXEL
                    if cond=="CHILD_FULL": exp=CHILD_PIXEL
                    if (rootpix[yy][xx]&fullmask)!=(exp&fullmask):
                        err(errors,f"root_composition:{idx}:{xx}:{yy}");break
                else: continue
                break
            else: pixel_checks+=1
        win=r.get("parent_geometry",PARENT)
        child_rows=r.get("children",[])
        mapped=[c for c in child_rows if c.get("map_state")==2]
        covered=cond in ("SIBLING_HALF","SIBLING_FULL","CHILD_HALF","CHILD_FULL")
        overlap=False
        for c in mapped:
            a,b,w,h=c.get("rect",[0,0,0,0])
            if a<120 and 0<a+w and b<80 and 0<b+h: overlap=True
        if cond in ("CHILD_HALF","CHILD_FULL") and not overlap: err(errors,f"child_geometry_missing:{idx}")
        if cond in ("CLEAR","SIBLING_HALF","SIBLING_FULL","RESTORED") and overlap: err(errors,f"unexpected_child_overlap:{idx}")
        expected_status="CLEAR_PARENT_REGION_SCOPED" if cond in ("CLEAR","RESTORED") else "UNKNOWN"
        got=r.get("assessment",{}).get("status")
        if got!=expected_status: err(errors,f"assessment:{idx}")
        if got=="CLEAR_PARENT_REGION_SCOPED": clear_count+=1
        if got=="UNKNOWN": unknown_count+=1
        if r.get("assessment",{}).get("input_authority") is not False or r.get("assessment",{}).get("task_success") is not None:
            err(errors,f"authority:{idx}")
        wincap=cap_by["window_client"]
        if wincap.get("status")=="ERROR":
            raw_errors+=1
            if cond!="SIBLING_FULL" or wincap.get("frame")!="window_client" or wincap.get("error_type")!="TypeError": err(errors,f"unexpected_capture_error:{idx}")
            else: xfail.append(idx)
        else:
            # Parent-window drawable pixels are defined on clear/restored and child-covered cases.
            # Under sibling occlusion, only the part not covered by the sibling has defined support.
            expected_parent=cond in ("CLEAR","CHILD_HALF","CHILD_FULL","RESTORED")
            pix=check_raw(root,wincap,None,errors,f"window:{idx}",0)
            if pix is not None:
                masks=wincap["artifact"]["masks"]
                maskall=int(masks[0])|int(masks[1])|int(masks[2])
                if expected_parent:
                    mismatch=any((v&maskall)!=(PARENT_PIXEL&maskall) for line in pix for v in line)
                elif cond=="SIBLING_HALF":
                    mismatch=any((pix[yy][xx]&maskall)!=(PARENT_PIXEL&maskall) for yy in range(80) for xx in range(60))
                else:
                    mismatch=False
                if mismatch: err(errors,f"window_pixel_mismatch:{idx}")
                else: pixel_checks+=1
    if clear_count!=4: err(errors,"assessor_clear_count")
    if unknown_count!=8: err(errors,"assessor_unknown_count")
    if attempts!=24: err(errors,"capture_attempts")
    if result.get("producer_gate_candidate") is not True: err(errors,"producer_gate_candidate")
    complete=sum(r.get("status")=="COMPLETE" for r in rows)
    total_errors=sum(c.get("status")=="ERROR" for r in rows for c in r.get("captures",[]))
    if result.get("sessions_complete")!=complete or result.get("capture_attempts")!=attempts or result.get("capture_errors")!=total_errors:
        err(errors,"result_summary_binding")
    report={"schema":"capture-visibility-docker-4835-audit-v1","status":"PASS_RAW_AUDIT" if not errors else "FAIL_RAW_AUDIT",
            "errors":errors,"source_files_checked":len(manifest),"sessions_checked":len(rows),
            "capture_attempts_checked":attempts,"capture_errors":raw_errors,"permitted_sibling_full_typeerrors":xfail,
            "pixel_images_checked":pixel_checks,"assessor_clear":clear_count,"assessor_unknown":unknown_count,
            "allocation_scientific_disposition":"PENDING_SCOPE_GATES" if not errors else "STOP_AUDIT"}
    return report
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--root",type=Path,required=True);p.add_argument("--source",type=Path,required=True)
    p.add_argument("--manifest",type=Path,required=True);p.add_argument("--out",type=Path,required=True);a=p.parse_args()
    result=audit(a.root,a.source,a.manifest);a.out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,sort_keys=True,indent=2))
