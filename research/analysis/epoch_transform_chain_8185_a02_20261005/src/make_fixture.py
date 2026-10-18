"""Create frozen public metadata and a separate exact-world oracle sidecar."""
import itertools, json, sys
from pathlib import Path

I=[1,0,0,1,0,0]
def m(a=1,b=0,c=0,d=1,tx=0,ty=0): return [a,b,c,d,tx,ty]
def edge(eid,src,se,dst,de,maps,unit="px",context="dpi-v2"):
    bounds=[[min(x[i] for x in maps),max(x[i] for x in maps)] for i in range(6)]
    return {"id":eid,"source":{"frame":src,"epoch":se},"target":{"frame":dst,"epoch":de},"unit":unit,"context":context,"bounds":bounds,"_oracle_maps":maps}
def frame(name,epoch): return {"frame":name,"epoch":epoch}
def make(cid,kind,edges,target_frame,target_box,action_frame,action_point,baseline_state="scale2",**kw):
    return {"case_id":cid,"kind":kind,"edges":edges,"target":{"identity":"target-A","at":frame(*target_frame),"box":target_box},"action":{"target_identity":"target-A","at":frame(*action_frame),"point":action_point},"forbidden":[{"at":frame(*target_frame),"box":[90,90,92,92]}],"required_unit":"px","required_context":"dpi-v2","input":{"frame":"backend","epoch":target_frame[1] if kind=="direct" else max([e['target']['epoch'] for e in edges],default=target_frame[1]),"context":"dpi-v2"},"observation_epoch":target_frame[1],"admission_epoch":target_frame[1] if kind=="direct" else max([e['target']['epoch'] for e in edges],default=target_frame[1]),"target_error_options":[[0,0]],"action_error_options":[[0,0]],**kw}

def main():
    out=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]/"results/FORMAL_A02"
    (out/"public").mkdir(parents=True,exist_ok=True); (out/"oracle").mkdir(parents=True,exist_ok=True)
    baseline={"scale1":I,"translate5":m(tx=5),"scale2":m(a=2,d=2)}
    cases=[]
    cases.append(make("DIRECT_STABLE","direct",[edge("d0","capture",7,"backend",7,[I])],("capture",7),[8,8,12,12],("capture",7),[10,10],"scale1"))
    cases.append(make("DIRECT_TRANSLATION_REFRESH","direct",[edge("d1","capture",7,"backend",7,[m(tx=5)])],("capture",7),[8,8,12,12],("capture",7),[10,10],"translate5",calibration_event={"refresh_to":"translate5"}))
    cases.append(make("DIRECT_UNIFORM_SCALE_REFRESH","direct",[edge("d2","capture",7,"backend",7,[m(a=2,d=2)])],("capture",7),[4,4,6,6],("capture",7),[5,5],"scale2",calibration_event={"refresh_to":"scale2"}))
    mixed=[edge("crop","capture",7,"presentation",7,[m(tx=10)]),edge("client","presentation",7,"client",7,[I]),edge("dpi","client",7,"monitor",7,[m(a=2,d=1)]),edge("origin","monitor",7,"backend",7,[m(tx=100,ty=20)])]
    cases.append(make("COMPOSE_MIXED_DPI_VALID_UPDATE","composed_valid",mixed,("capture",7),[4,4,6,6],("presentation",7),[14,5],"scale2"))
    epoch=[edge("e78","capture",7,"client",8,[m(tx=1)]),edge("e89","client",8,"backend",9,[m(a=2,d=2)])]
    cases.append(make("COMPOSE_EPOCH_7_8_9","composed_valid",epoch,("capture",7),[10,10,10,10],("client",8),[11,10],"scale2"))
    sh=m(b=2); shinv=m(b=-2)
    cases.append(make("INVERSE_SHEAR_PAIR_IDENTITY","composed_control",[edge("shear-a","capture",7,"camera",7,[sh]),edge("shear-b","camera",7,"backend",7,[shinv])],("capture",7),[4,4,6,6],("capture",7),[5,5],"scale2"))
    ncm=[edge("n1","capture",7,"f1",7,[m(b=1)]),edge("n2","f1",7,"f2",7,[m(tx=3)]),edge("n3","f2",7,"backend",7,[m(c=1)])]
    cases.append(make("COMPOSE_NONCOMMUTING_ORDER","composed_valid",ncm,("capture",7),[1,1,1,1],("f1",7),[2,1],"scale2"))
    common=[edge("shared","capture",7,"backend",7,[m(tx=-1),m(tx=1)])]
    cases.append(make("COMMON_MODE_UNCERTAINTY_CONTROL","uncertainty_control",common,("capture",7),[0,0,4,4],("capture",7),[2,2],"scale2"))
    independent=[edge("target-path","target-frame",7,"backend",7,[m(tx=-1),m(tx=1)]),edge("action-path","action-frame",7,"backend",7,[m(tx=-1),m(tx=1)])]
    cases.append(make("INDEPENDENT_ERROR_CONTROL","uncertainty_control",independent,("target-frame",7),[0,0,10,10],("action-frame",7),[5,5],"scale2",target_error_options=[[0,0]],action_error_options=[[0,0]]))
    # Fail-closed path, provenance, and model controls.
    invalids=[
      ("INVALID_STALE_EDGE",[edge("stale","capture",6,"backend",7,[I])],("capture",7),("capture",7),"stale_edge"),
      ("INVALID_MISSING_EDGE",[],("capture",7),("capture",7),"missing_path"),
      ("INVALID_REVERSED_EDGE",[edge("reverse","backend",7,"capture",7,[I])],("capture",7),("capture",7),"missing_path"),
      ("INVALID_DUPLICATE_PATH",[edge("dup-a","capture",7,"backend",7,[I]),edge("dup-b","capture",7,"backend",7,[I])],("capture",7),("capture",7),"ambiguous_path"),
      ("INVALID_UNIT",[edge("bad-unit","capture",7,"backend",7,[I],unit="dp")],("capture",7),("capture",7),"unit_mismatch"),
      ("INVALID_DPI_CONTEXT",[edge("bad-context","capture",7,"backend",7,[I],context="dpi-v1")],("capture",7),("capture",7),"context_mismatch"),
    ]
    for cid,es,tf,af,why in invalids:
        cases.append(make(cid,"invalid",es,tf,[0,0,4,4],af,[2,2],"scale2",expected_invalid=why))
    c=make("INVALID_IDENTITY_SWAP","invalid",[edge("id","capture",7,"backend",7,[I])],("capture",7),[0,0,4,4],("capture",7),[2,2],"scale2",expected_invalid="identity_mismatch")
    c["action"]["target_identity"]="neighbor-B"; cases.append(c)
    cases.append(make("INVALID_NONAFFINE_REFLOW","invalid",[edge("aff","capture",7,"backend",7,[I])],("capture",7),[0,0,4,4],("capture",7),[2,2],"scale2",layout_model="non_affine",expected_invalid="non_affine"))
    c=make("INVALID_STALE_OBSERVATION_BINDING","invalid",[edge("fresh","capture",7,"backend",9,[I])],("capture",7),[0,0,4,4],("capture",7),[2,2],"scale2",expected_invalid="stale_binding")
    c["observation_epoch"]=7; c["admission_epoch"]=9; c["binding_current"]=False; cases.append(c)
    crossing=[edge("target-id","target-frame",7,"backend",7,[I]),edge("action-uncertain","action-frame",7,"backend",7,[m(tx=-1),m(tx=1)])]
    cases.append(make("INVALID_TARGET_BOUNDARY_UNCERTAINTY","invalid",crossing,("target-frame",7),[10,10,10,12],("action-frame",7),[10,11],"scale2",expected_invalid="boundary_uncertainty"))
    c=make("INVALID_FORBIDDEN_REGION_OVERLAP","invalid",[edge("forbidden-id","capture",7,"backend",7,[I])],("capture",7),[0,0,10,10],("capture",7),[5,5],"scale2",expected_invalid="forbidden_overlap")
    c["forbidden"]=[{"at":frame("capture",7),"box":[5,5,5,5]}]; cases.append(c)

    schedule={"initial_state":"scale1","calibrations":baseline}
    public={"schema":"epoch-transform-a02-public-v1","issue":8201,"required_input_context":"dpi-v2","required_unit":"px","baseline_schedule":schedule}
    hidden={"schema":"epoch-transform-a02-hidden-oracle-v1","worlds":{}}
    for c in cases:
        ids=[e["id"] for e in c["edges"]]; opts=[e["_oracle_maps"] for e in c["edges"]]
        assignments=[dict(zip(ids,vs)) for vs in itertools.product(*opts)] if opts else [{}]
        hidden["worlds"][c["case_id"]]={"stratum":c["kind"],"edge_assignments":assignments,"target_boxes":[c["target"]["box"]],"target_identity":"target-A","action_points":[c["action"]["point"]],"forbidden_boxes":[f["box"] for f in c["forbidden"]],"target_errors":c["target_error_options"],"action_errors":c["action_error_options"],"expected_invalid":c.get("expected_invalid"),"exact_world_count":len(assignments)}
        for e in c["edges"]: e.pop("_oracle_maps")
    public["cases"]=[{k:v for k,v in c.items() if k not in ("kind","expected_invalid")} for c in cases]
    (out/"public/corpus.json").write_text(json.dumps(public,sort_keys=True,indent=2)+"\n")
    (out/"oracle/exact_worlds.json").write_text(json.dumps(hidden,sort_keys=True,indent=2)+"\n")
    print(json.dumps({"cases":len(cases),"hidden_worlds":sum(x['exact_world_count'] for x in hidden['worlds'].values()),"output":str(out)},sort_keys=True))
if __name__=="__main__": main()
