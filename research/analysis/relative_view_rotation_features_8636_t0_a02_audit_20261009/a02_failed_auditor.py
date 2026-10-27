"""Independent raw-only replay/scorer for Issue #8636 T0 A02. No candidate import."""
from __future__ import annotations
import argparse, copy, hashlib, json, math, statistics
import random
from pathlib import Path

ROOT=Path(__file__).resolve().parent
COLORS=((255,0,0),(0,255,0),(0,0,255)); CX=CY=47.5; F=48.0; GAIN=.72; LIMIT=.08; TOL=.015
WORLD=((-0.45,-0.25,1.0),(0.45,-0.20,1.0),(0.05,0.50,1.0))


def ppm(path):
    data=Path(path).read_bytes(); h,p=data.split(b"\n255\n",1); ps=h.split()
    w,hg=int(ps[1]),int(ps[2])
    if ps[0]!=b"P6" or len(p)!=w*hg*3: raise ValueError("invalid PPM")
    return w,hg,p,data


def camera(yaw,pitch):
    cy,sy=math.cos(yaw),math.sin(yaw); cp,sp=math.cos(pitch),math.sin(pitch)
    return ((cy,sy*sp,sy*cp),(0.0,cp,-sp),(-sy,cy*sp,cy*cp))


def scenario(seed,condition):
    code={"pure_yaw":0,"combined_rotation":1,"focal_shift":2,"feature_loss":3}[condition]
    rng=random.Random(seed*37+code); yaw=rng.uniform(-.28,.28); pitch=0.0; focal=48.0; fault=None
    if condition=="combined_rotation": pitch=rng.uniform(-.24,.24)
    elif condition=="focal_shift": pitch=rng.uniform(-.20,.20); focal=43.0 if seed%2 else 53.0
    elif condition=="feature_loss":
        pitch=rng.uniform(-.18,.18)
        fault=("hide_second","swap_ids","move_third","near_singular","low_texture","camera_translation","stale_frame","viewport_resize","range_variation")[seed%9]
    return yaw,pitch,focal,fault


def expected_renderer(yaw,pitch,focal,fault,width,height):
    cy,sy=math.cos(yaw),math.sin(yaw); cp,sp=math.cos(pitch),math.sin(pitch)
    q=((cy,sy*sp,sy*cp),(0.0,cp,-sp),(-sy,cy*sp,cy*cp))
    translation=(.35,0.0,0.0) if fault=="camera_translation" else (0.0,0.0,0.0)
    radial=(2.0,.7,1.4) if fault=="range_variation" else (1.0,1.0,1.0)
    points=[]
    for idx,p in enumerate(WORLD):
        moved=tuple(radial[idx]*p[k]-translation[k] for k in range(3))
        b=tuple(sum(q[k][i]*moved[k] for k in range(3)) for i in range(3))
        if b[2]<=.1: raise ValueError("landmark behind camera")
        points.append(((width-1)/2+focal*b[0]/b[2],(height-1)/2-focal*b[1]/b[2]))
    if fault=="move_third": points[2]=(points[2][0]+18.0,points[2][1]-14.0)
    if fault=="near_singular": points[1]=(points[0][0]+.5,points[0][1]+.5)
    image=bytearray([16,16,16]*(width*height)); size=1 if fault=="low_texture" else 3; half=size//2
    for idx,(x,y) in enumerate(points):
        if fault=="hide_second" and idx==1: continue
        color=COLORS[1-idx] if fault=="swap_ids" and idx<2 else COLORS[idx]
        ix,iy=round(x),round(y)
        for yy in range(iy-half,iy+half+1):
            for xx in range(ix-half,ix+half+1):
                if 0<=xx<width and 0<=yy<height:
                    off=(yy*width+xx)*3; image[off:off+3]=bytes(color)
    header=f"P6\n{width} {height}\n255\n".encode()
    return header+bytes(image),points


def centers(w,h,p):
    out=[]
    for c in COLORS:
        xy=[]
        for y in range(h):
            for x in range(w):
                off=(y*w+x)*3
                if tuple(p[off:off+3])==c: xy.append((x,y))
        if len(xy)!=9: raise ValueError("missing or ambiguous landmark")
        out.append((sum(x for x,_ in xy)/9.0,sum(y for _,y in xy)/9.0))
    return out


def vsub(a,b): return tuple(x-y for x,y in zip(a,b))
def vscale(a,k): return tuple(x*k for x in a)
def vdot(a,b): return sum(x*y for x,y in zip(a,b))
def vnorm(a): return math.sqrt(vdot(a,a))
def vcross(a,b): return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def vunit(a):
    n=vnorm(a)
    if n<1e-9: raise ValueError("degenerate frame")
    return vscale(a,1/n)


def rays(points):
    result=[]
    for x,y in points:
        u=(x-CX)/F; v=-(y-CY)/F; z=1.0/math.sqrt(u*u+v*v+1.0)
        result.append((u*z,v*z,z))
    return result


def matmul(x,y):
    return tuple(tuple(sum(x[i][k]*y[k][j] for k in range(3)) for j in range(3)) for i in range(3))
def mtrans(x): return tuple(tuple(x[j][i] for j in range(3)) for i in range(3))
def mcols(c): return tuple(tuple(c[j][i] for j in range(3)) for i in range(3))


def basis(points):
    b=rays(points); e1=vunit(b[0]); w=vsub(b[1],vscale(e1,vdot(b[1],e1)))
    if vnorm(w)<.08: raise ValueError("near singular")
    e2=vunit(w); e3=vunit(vcross(e1,e2))
    return (e1,e2,e3),b


def sph_geometry(now,ref):
    bn,un=basis(now); br,ur=basis(ref)
    pairs=((0,1),(0,2),(1,2))
    ds=[math.acos(max(-1,min(1,vdot(un[i],un[j])))) for i,j in pairs]
    rs=[math.acos(max(-1,min(1,vdot(ur[i],ur[j])))) for i,j in pairs]
    if max(abs(a-b) for a,b in zip(ds,rs))>.09: raise ValueError("shape changed")
    rr=matmul(mcols(bn),mtrans(mcols(br)))
    yaw=math.atan2(-rr[0][2],rr[0][0]); pitch=math.atan2(rr[1][2],rr[2][2])
    theta=math.acos(max(-1.0,min(1.0,(rr[0][0]+rr[1][1]+rr[2][2]-1.0)/2.0)))
    if theta<1e-10: rv=(0.,0.,0.)
    else:
        denom=2*math.sin(theta)
        rv=tuple(theta*x/denom for x in (rr[2][1]-rr[1][2],rr[0][2]-rr[2][0],rr[1][0]-rr[0][1]))
    return yaw,pitch,tuple(ds)+rv


def raw_feature_vector(now,ref):
    c=[((x-CX)/F,-(y-CY)/F) for x,y in now]; r=[((x-CX)/F,-(y-CY)/F) for x,y in ref]
    return tuple(v for i in range(3) for v in (c[i][0]-r[i][0],c[i][1]-r[i][1]))


def raw_error(now,ref):
    c=[((x-CX)/F,-(y-CY)/F) for x,y in now]; r=[((x-CX)/F,-(y-CY)/F) for x,y in ref]
    eps=1e-5
    def proj(ya,pi):
        cy,sy=math.cos(ya),math.sin(ya); cp,sp=math.cos(pi),math.sin(pi)
        q=((cy,sy*sp,sy*cp),(0.,cp,-sp),(-sy,cy*sp,cy*cp)); vals=[]
        for x,y in r:
            z=(x,y,1.); cam=tuple(sum(q[k][i]*z[k] for k in range(3)) for i in range(3))
            if cam[2]<=.1: raise ValueError("behind camera")
            vals.extend((cam[0]/cam[2],cam[1]/cam[2]))
        return vals
    z=proj(0,0); py=proj(eps,0); pp=proj(0,eps)
    a=[(py[i]-z[i])/eps for i in range(6)]; b=[(pp[i]-z[i])/eps for i in range(6)]
    d=[c[i//2][i%2]-r[i//2][i%2] for i in range(6)]
    aa=sum(x*x for x in a); ab=sum(x*y for x,y in zip(a,b)); bb=sum(x*x for x in b)
    ad=sum(x*y for x,y in zip(a,d)); bd=sum(x*y for x,y in zip(b,d)); det=aa*bb-ab*ab
    if det<1e-10: raise ValueError("ill-conditioned raw mapping")
    return ( (ad*bb-bd*ab)/det, (bd*aa-ad*ab)/det )


def check_generation(meta):
    if meta["target_generation"]!=meta["viewport_generation"]: raise ValueError("stale target generation")


def expected_image_action(arm,pts,ref,meta):
    if meta["width"]!=96 or meta["height"]!=96: raise ValueError("viewport")
    check_generation(meta)
    _,un=basis(pts); _,ur=basis(ref); pairs=((0,1),(0,2),(1,2))
    da=[math.acos(max(-1,min(1,vdot(un[i],un[j])))) for i,j in pairs]
    dr=[math.acos(max(-1,min(1,vdot(ur[i],ur[j])))) for i,j in pairs]
    if max(abs(a-b) for a,b in zip(da,dr))>.09: raise ValueError("shape changed")
    y,p=raw_error(pts,ref) if arm=="raw_pixels" else sph_geometry(pts,ref)[:2]
    if max(abs(y),abs(p))<=TOL: return None
    return (max(-LIMIT,min(LIMIT,-GAIN*y)),max(-LIMIT,min(LIMIT,-GAIN*p)))


def expected_oracle_action(yaw,pitch,step):
    if step>=12 or max(abs(yaw),abs(pitch))<=TOL: return None
    return (max(-LIMIT,min(LIMIT,-GAIN*yaw)),max(-LIMIT,min(LIMIT,-GAIN*pitch)))


def expected_fault_yield(fault):
    return fault in {"hide_second","swap_ids","move_third","near_singular","low_texture","camera_translation","stale_frame","viewport_resize"}


def expected_stress_yield(condition,arm,points,reference,meta):
    """Reconstruct a focal-calibration abstention without treating it as a primary fault."""
    if condition != "focal_shift" or arm == "viewstate_oracle" or points is None:
        return False,None
    try:
        expected_image_action(arm,points,reference,meta)
    except ValueError as exc:
        return True,str(exc)
    return False,None


def close_action(a,b):
    if a is None or b is None: return a is b
    return len(a)==len(b) and all(abs(x-y)<1e-10 for x,y in zip(a,b))


def check_order(rows):
    last={}
    for row in rows:
        trial=row["trial"]; step=row["step"]
        if step!=last.get(trial,-1)+1: raise ValueError("event order/count")
        last[trial]=step


def check_release(rows):
    grouped={}
    for row in rows: grouped.setdefault(row["trial"],[]).append(row)
    for trial,items in grouped.items():
        releases=[i for i,x in enumerate(items) if x.get("event_type")=="RELEASE"]
        if len(releases)!=1 or releases[0]!=len(items)-1: raise ValueError("missing or nonterminal release event")
        rel=items[-1]
        if rel.get("status")!="RELEASE" or rel.get("release_verified") is not True or rel.get("action")!=[0.0,0.0]:
            raise ValueError("invalid neutral release receipt")
        if items[-2].get("status")=="ACTION": raise ValueError("release before terminal control decision")


def audit_source(freeze,root):
    for name,expected in freeze["source_sha256"].items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=expected: return False
    return True


def audit(out):
    freeze=json.loads((ROOT/"FREEZE.json").read_text())
    if not audit_source(freeze,ROOT): raise ValueError("frozen source digest mismatch")
    events=[json.loads(s) for s in (out/"events.jsonl").read_text().splitlines()]
    truths=[json.loads(s) for s in (out/"scorer_truth.jsonl").read_text().splitlines()]
    check_order(events)
    check_release(events)
    result_by={}; truth_by={t["trial"]:t for t in truths}
    for r in events:
        if r.get("event_type")=="RELEASE":
            if r["trial"] not in truth_by: raise ValueError("release without trial")
            result_by.setdefault(r["trial"],[]).append(r)
            continue
        if r.get("event_type")!="OBSERVATION": raise ValueError("unknown event type")
        w,h,p,raw=ppm(out/r["frame"])
        if hashlib.sha256(raw).hexdigest()!=r["frame_sha256"]: raise ValueError("frame digest")
        iw,ih,ip,rawref=ppm(out/"frames/reference.ppm")
        if hashlib.sha256(rawref).hexdigest()!=r["reference_sha256"]: raise ValueError("reference digest")
        ref=centers(iw,ih,ip)
        truth=truth_by[r["trial"]]
        ey,ep,ef,base_fault=scenario(r["seed"],r["condition"])
        active_fault=base_fault if r["step"]==0 else None
        if truth["fault"]!=base_fault or r["fault"]!=active_fault: raise ValueError("fault schedule mismatch")
        ew,eh=(112,112) if active_fault=="viewport_resize" else (96,96)
        generation=r["seed"]+(1 if active_fault=="stale_frame" else 0)
        if (w,h)!=(ew,eh) or r["width"]!=w or r["height"]!=h: raise ValueError("viewport frame dimensions")
        if truth["focal"]!=ef: raise ValueError("focal schedule mismatch")
        frame_y=ey+sum(x["action"][0] for x in events if x.get("event_type")=="OBSERVATION" and x["trial"]==r["trial"] and x["step"]<r["step"] and x["action"] is not None)
        frame_p=ep+sum(x["action"][1] for x in events if x.get("event_type")=="OBSERVATION" and x["trial"]==r["trial"] and x["step"]<r["step"] and x["action"] is not None)
        expected_frame,expected_pts=expected_renderer(frame_y,frame_p,ef,active_fault,w,h)
        if raw!=expected_frame: raise ValueError("independent renderer mismatch")
        if r["target_generation"]!=r["seed"] or r["viewport_generation"]!=generation: raise ValueError("generation schedule mismatch")
        try: actual=centers(w,h,p)
        except ValueError:
            if r["status"]!="YIELD": raise
            actual=None
        if actual is None:
            if r["points"] is not None or r["feature_vector"] is not None: raise ValueError("missing image values not represented as UNKNOWN")
        else:
            if r["points"] is None or len(actual)!=len(r["points"]) or any(abs(a-b)>1e-12 for q,z in zip(actual,r["points"]) for a,b in zip(q,z)):
                raise ValueError("forged feature sample")
            if truth_by[r["trial"]]["arm"]=="raw_pixels": expected_features=raw_feature_vector(actual,ref)
            elif truth_by[r["trial"]]["arm"]=="spherical_features":
                try: expected_features=sph_geometry(actual,ref)[2]
                except ValueError: expected_features=None
            else: expected_features=None
            if expected_features is None and r["feature_vector"] is not None: raise ValueError("invalid feature published")
            if expected_features is not None and (r["feature_vector"] is None or any(abs(x-y)>1e-10 for x,y in zip(expected_features,r["feature_vector"]))):
                raise ValueError("feature vector mismatch")
        expected_fault=expected_fault_yield(active_fault)
        if truth["arm"]=="viewstate_oracle": expected_fault=False
        stress_yield,stress_reason=expected_stress_yield(r["condition"],truth["arm"],actual,ref,{"width":w,"height":h,"target_generation":r["target_generation"],"viewport_generation":r["viewport_generation"]})
        if r["status"]=="YIELD":
            if truth["arm"]=="viewstate_oracle" or not (expected_fault or stress_yield): raise ValueError("unexpected yield on valid fixture")
            if stress_yield and r.get("yield_reason")!=stress_reason: raise ValueError("focal stress yield reason mismatch")
            expected=None
        elif truth["arm"]!="viewstate_oracle":
            if expected_fault or stress_yield: raise ValueError("invalid or out-of-calibration fixture did not abstain")
            expected=expected_image_action(truth["arm"],actual,ref,{"width":w,"height":h,"target_generation":r["target_generation"],"viewport_generation":r["viewport_generation"]})
        else:
            expected=expected_oracle_action(frame_y,frame_p,r["step"])
        if active_fault=="range_variation" and r["step"]==0:
            normal,_=expected_renderer(frame_y,frame_p,ef,None,w,h)
            if raw!=normal: raise ValueError("radial range null control changed image")
        if r["step"]>=12: expected=None
        expected_status="YIELD" if (expected_fault or stress_yield) else ("STEP_LIMIT" if r["step"]>=12 else "STOP" if expected is None else "ACTION")
        if r["status"]!=expected_status: raise ValueError("status does not match independent decision")
        if r["status"]=="YIELD":
            if r["action"] is not None: raise ValueError("yield emitted action")
        elif r["status"]=="ACTION":
            if not close_action(r["action"],expected): raise ValueError("action replay mismatch")
            if any(abs(x)>LIMIT+1e-12 for x in r["action"]): raise ValueError("action outside envelope")
        elif r["status"] in ("STOP","STEP_LIMIT"):
            if expected is not None or r["action"] is not None: raise ValueError("invalid terminal action")
        else: raise ValueError("unknown event status")
        result_by.setdefault(r["trial"],[]).append(r)
    if len(truths)!=120*3 or len(result_by)!=len(truths): raise ValueError("fixture cardinality")
    for t in truths:
        rows=result_by[t["trial"]]
        if rows[-1]["event_type"]!="RELEASE" or not t["release_verified"]: raise ValueError("missing terminal release")
        acts=[r["action"] for r in rows if r["event_type"]=="OBSERVATION" and r["action"] is not None]
        if acts!=t["actions"] or len(acts)!=t["corrections"]: raise ValueError("action custody")
        y=t["initial_yaw"]+sum(a[0] for a in acts); p=t["initial_pitch"]+sum(a[1] for a in acts)
        if abs(y-t["final_yaw"])>1e-12 or abs(p-t["final_pitch"])>1e-12: raise ValueError("state transition")
        expected_success=(not t["target_loss"] and abs(y)<=.025 and abs(p)<=.025)
        if t["success"]!=expected_success: raise ValueError("terminal oracle mismatch")
        if t["target_loss"] != any(r["status"]=="YIELD" for r in rows if r["event_type"]=="OBSERVATION"): raise ValueError("loss disposition")
    # In-memory mutation controls; source/result artifacts remain unchanged.
    mutations={}
    changed=copy.deepcopy(freeze); first=next(iter(changed["source_sha256"])); changed["source_sha256"][first]="0"*64
    mutations["source_digest_rejected"]=not audit_source(changed,ROOT)
    ordercopy=copy.deepcopy(events); idx=next(i for i in range(len(ordercopy)-1) if ordercopy[i]["trial"]==ordercopy[i+1]["trial"])
    ordercopy[idx],ordercopy[idx+1]=ordercopy[idx+1],ordercopy[idx]
    try: check_order(ordercopy); mutations["event_order_rejected"]=False
    except ValueError: mutations["event_order_rejected"]=True
    stale=copy.deepcopy(events[0]); stale["viewport_generation"]+=1
    try: check_generation(stale); mutations["stale_generation_rejected"]=False
    except ValueError: mutations["stale_generation_rejected"]=True
    release_mutant=copy.deepcopy(events)
    trial=release_mutant[0]["trial"]
    release_mutant=[row for row in release_mutant if not (row["trial"]==trial and row.get("event_type")=="RELEASE")]
    try: check_release(release_mutant); mutations["missing_release_rejected"]=False
    except ValueError: mutations["missing_release_rejected"]=True
    forged=copy.deepcopy(events[0]); forged["points"][0][0]+=3.0
    w,h,pix,raw=ppm(out/forged["frame"]); measured=centers(w,h,pix)
    mutations["forged_feature_rejected"]=any(abs(a-b)>1e-12 for q,z in zip(measured,forged["points"]) for a,b in zip(q,z))
    if not all(mutations.values()): raise ValueError("mutation control missed")
    paired={}
    for t in truths:
        key=(t["condition"],t["seed"]); slot=paired.setdefault(key,{})
        if t["arm"] in slot: raise ValueError("duplicate arm identity")
        slot[t["arm"]]=t
    expected_keys={(condition,seed) for condition in ("pure_yaw","combined_rotation","focal_shift","feature_loss") for seed in range(30030,30060)}
    grid_complete=set(paired)==expected_keys and all(set(x)=={"raw_pixels","spherical_features","viewstate_oracle"} for x in paired.values())
    primary=[x for (cond,_),x in paired.items() if cond in ("pure_yaw","combined_rotation")]
    raw_corr=[x["raw_pixels"]["corrections"] for x in primary]; sph_corr=[x["spherical_features"]["corrections"] for x in primary]
    reduction=1-statistics.median(sph_corr)/statistics.median(raw_corr) if statistics.median(raw_corr) else 0.0
    raw_success=sum(x["raw_pixels"]["success"] for x in primary); sph_success=sum(x["spherical_features"]["success"] for x in primary)
    raw_loss=sum(x["raw_pixels"]["target_loss"] for x in primary); sph_loss=sum(x["spherical_features"]["target_loss"] for x in primary)
    invalid=[t for t in truths if t["condition"]=="feature_loss" and t["fault"]!="range_variation" and t["arm"]!="viewstate_oracle"]
    invalid_count=sum(t["target_loss"] and t["corrections"]==0 for t in invalid)
    invalid_abstain=len(invalid)==54 and invalid_count==54
    control_counts={fault:sum(t["condition"]=="feature_loss" and t["fault"]==fault for t in truths) for fault in ("hide_second","swap_ids","move_third","near_singular","low_texture","camera_translation","stale_frame","viewport_resize","range_variation")}
    method_pass=(grid_complete and len(primary)==60 and all(mutations.values()) and invalid_abstain and all(t["release_verified"] for t in truths))
    h_supported=method_pass and sph_success>=raw_success and sph_loss<=raw_loss and reduction>=.20
    summary={"allocation":freeze["allocation"],"disposition":"H_SUPPORTED_SCOPED" if h_supported else "H_FAIL_SCOPED" if method_pass else "HOLD_UNCERTAIN","method_gate":"PASS_METHOD_SCOPED" if method_pass else "HOLD_UNCERTAIN","paired_seed_conditions":len(paired),"complete_pair_grid":grid_complete,"arm_trials":len(truths),"primary_pairs":len(primary),"primary_median_corrections":{"raw_pixels":statistics.median(raw_corr),"spherical_features":statistics.median(sph_corr)},"primary_correction_reduction_fraction":reduction,"primary_successes":{"raw_pixels":raw_success,"spherical_features":sph_success},"primary_target_loss":{"raw_pixels":raw_loss,"spherical_features":sph_loss},"feature_loss_abstentions_image_arms":invalid_count,"feature_loss_expected_abstention_trials":len(invalid),"fault_control_trial_counts":control_counts,"focal_shift":{"raw_success":sum(t["success"] for t in truths if t["condition"]=="focal_shift" and t["arm"]=="raw_pixels"),"spherical_success":sum(t["success"] for t in truths if t["condition"]=="focal_shift" and t["arm"]=="spherical_features"),"raw_yield_trials":sum(t["condition"]=="focal_shift" and t["arm"]=="raw_pixels" and t["target_loss"] for t in truths),"spherical_yield_trials":sum(t["condition"]=="focal_shift" and t["arm"]=="spherical_features" and t["target_loss"] for t in truths),"interpretation":"out-of-calibration stress only; not part of primary H gate"},"mutation_controls":mutations,"errors":0}
    return summary


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--output",default=str(ROOT/"results/a02-outcome")); ap.add_argument("--result",default=str(ROOT/"results/a02-outcome/audit.json")); a=ap.parse_args()
    summary=audit(Path(a.output)); Path(a.result).write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n"); print(json.dumps(summary,sort_keys=True))
if __name__=="__main__": main()
