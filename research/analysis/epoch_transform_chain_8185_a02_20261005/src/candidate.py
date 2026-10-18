"""Public-input affine chain candidate and non-refusing scalar baseline."""
import itertools,json,sys

def mul(l,r):
    a,b,c,d,x,y=l; A,B,C,D,X,Y=r
    return [a*A+b*C,a*B+b*D,c*A+d*C,c*B+d*D,a*X+b*Y+x,c*X+d*Y+y]
def point(p,t):
    a,b,c,d,x,y=t; return [a*p[0]+b*p[1]+x,c*p[0]+d*p[1]+y]
def bounds_points(points): return [[min(p[k] for p in points),max(p[k] for p in points)] for k in (0,1)]
def box_corners(b,delta=(0,0)):
    x1,y1,x2,y2=b; dx,dy=delta
    return [[x1+dx,y1+dy],[x2+dx,y1+dy],[x2+dx,y2+dy],[x1+dx,y2+dy]]
def rect(ps): return [min(p[0] for p in ps),min(p[1] for p in ps),max(p[0] for p in ps),max(p[1] for p in ps)]
def inside_poly(p,poly):
    signs=[]
    for a,b in zip(poly,poly[1:]+poly[:1]):
        cross=(b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])
        if cross: signs.append(1 if cross>0 else -1)
    bounds=rect(poly)
    return not (1 in signs and -1 in signs) and bounds[0]<=p[0]<=bounds[2] and bounds[1]<=p[1]<=bounds[3]
def paths(edges,start,goal,unit,context):
    found=[]
    def walk(node,used,path):
        if node==goal: found.append(path); return
        for i,e in enumerate(edges):
            if i in used or e["unit"]!=unit or e["context"]!=context: continue
            if (e["source"]["frame"],e["source"]["epoch"])==node:
                dst=(e["target"]["frame"],e["target"]["epoch"])
                walk(dst,used|{i},path+[e])
    walk((start["frame"],start["epoch"]),set(),[]); return found
def chain_matrix(path,assignment):
    total=[1,0,0,1,0,0]
    for e in path: total=mul(assignment[e["id"]],total)
    return total
def allowed_maps(bounds): return [list(v) for v in itertools.product(*(range(lo,hi+1) for lo,hi in bounds))]
def decision(worlds):
    return "ADMIT" if worlds and all(inside_poly(w["point"],w["target"]) and not any(inside_poly(w["point"],b) for b in w["forbidden"]) for w in worlds) else "UNKNOWN"
def hulls(worlds):
    pts=[w["point"] for w in worlds]; targets=[p for w in worlds for p in w["target"]]
    return {"point_bounds":bounds_points(pts),"target_bounds":rect(targets)}
def baseline_eval(c,calibration):
    state=calibration["initial_state"]; bm=calibration["calibrations"][state]; worlds=[]
    for te,ae in itertools.product(c["target_error_options"],c["action_error_options"]):
        target=[point(p,bm) for p in box_corners(c["target"]["box"],te)]
        action=point([c["action"]["point"][0]+ae[0],c["action"]["point"][1]+ae[1]],bm)
        forbidden=[[point(p,bm) for p in box_corners(f["box"])] for f in c["forbidden"]]
        worlds.append({"point":action,"target":target,"forbidden":forbidden})
    return {"decision":decision(worlds),"state":state,**hulls(worlds)}

def evaluate(c,calibration):
    unknown={"case_id":c["case_id"],"decision":"UNKNOWN","reason":None,"point_bounds":None,"target_bounds":None,"baseline":baseline_eval(c,calibration)}
    if c.get("layout_model","affine")!="affine": unknown["reason"]="non_affine"; return unknown
    if c["target"]["identity"]!=c["action"]["target_identity"]: unknown["reason"]="identity_mismatch"; return unknown
    if c["observation_epoch"]!=c["target"]["at"]["epoch"] or c["admission_epoch"]!=c["input"]["epoch"] or not c.get("binding_current",True): unknown["reason"]="stale_binding"; return unknown
    if c["input"]["context"]!=c["required_context"] or c["input"]["epoch"]!=c["admission_epoch"]: unknown["reason"]="input_context_or_epoch_mismatch"; return unknown
    goal=(c["input"]["frame"],c["input"]["epoch"]); req_unit=c["required_unit"]; req_ctx=c["required_context"]
    tp=paths(c["edges"],c["target"]["at"],goal,req_unit,req_ctx)
    ap=paths(c["edges"],c["action"]["at"],goal,req_unit,req_ctx)
    fp=[paths(c["edges"],f["at"],goal,req_unit,req_ctx) for f in c["forbidden"]]
    if len(tp)!=1 or len(ap)!=1 or any(len(x)!=1 for x in fp): unknown["reason"]="missing_or_ambiguous_path"; return unknown
    opts={e["id"]:allowed_maps(e["bounds"]) for e in c["edges"]}
    ids=sorted(opts); assignments=(dict(zip(ids,vs)) for vs in itertools.product(*(opts[k] for k in ids))) if ids else iter([{}])
    worlds=[]
    for assn in assignments:
        tm,am=chain_matrix(tp[0],assn),chain_matrix(ap[0],assn)
        for te,ae in itertools.product(c["target_error_options"],c["action_error_options"]):
            tbox=[point(p,tm) for p in box_corners(c["target"]["box"],te)]
            apoint=point([c["action"]["point"][0]+ae[0],c["action"]["point"][1]+ae[1]],am)
            forb=[]
            for fi,f in enumerate(c["forbidden"]): forb.append([point(p,chain_matrix(fp[fi][0],assn)) for p in box_corners(f["box"])])
            worlds.append({"point":apoint,"target":tbox,"forbidden":forb})
    result={"case_id":c["case_id"],"decision":decision(worlds),"reason":None,**hulls(worlds)}
    # A deliberately simple, frame-untyped comparator: current calibration is applied
    # to every input coordinate; chain length never causes an automatic refusal.
    state=calibration["initial_state"]; bm=calibration["calibrations"][state]
    bw=[]
    for te,ae in itertools.product(c["target_error_options"],c["action_error_options"]):
        tbox=[point(p,bm) for p in box_corners(c["target"]["box"],te)]
        bp=point([c["action"]["point"][0]+ae[0],c["action"]["point"][1]+ae[1]],bm)
        bs=[[point(p,bm) for p in box_corners(f["box"])] for f in c["forbidden"]]
        bw.append({"point":bp,"target":tbox,"forbidden":bs})
    bh=hulls(bw); result["baseline"]={"decision":decision(bw),"state":state,**bh}
    return result
def run(public):
    schedule=public["baseline_schedule"]; state=schedule["initial_state"]; rows=[]
    for c in public["cases"]:
        event=c.get("calibration_event")
        if event: state=event["refresh_to"]
        row=evaluate(c,{**schedule,"initial_state":state}); row["baseline"]["state_used"]=state
        rows.append(row)
    return {"schema":"epoch-transform-a02-candidate-v1","rows":rows}
def main():
    public=json.load(open(sys.argv[1])); out=run(public); open(sys.argv[2],"w").write(json.dumps(out,sort_keys=True,indent=2)+"\n")
if __name__=="__main__": main()
