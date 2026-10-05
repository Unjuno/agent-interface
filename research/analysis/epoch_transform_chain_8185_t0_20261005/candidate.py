#!/usr/bin/env python3
"""Candidate: typed, epoch-bound affine transform composition with interval bounds."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def refuse(reason): return {"decision":"UNKNOWN_REFUSE","reason":reason,"mapped":None}
def mul(A,B):
    return [[sum(A[i][k]*B[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
def apply(A,p):
    x,y=p; return (A[0][0]*x+A[0][1]*y+A[0][2], A[1][0]*x+A[1][1]*y+A[1][2])
def chain(record):
    source=record["source_frame"]; epoch=record["observation_epoch"]; units=record["source_units"]
    edges=record["edges"]
    if not edges: return None,"missing_edge"
    seen=set(); cur=source; total=[[1,0,0],[0,1,0],[0,0,1]]; radius=[0.0,0.0]; correlated={}
    for e in edges:
        key=e.get("edge_id")
        if key in seen:return None,"duplicate_edge"
        seen.add(key)
        if e.get("source")!=cur:return None,"edge_order_or_frame_mismatch"
        if e.get("source_units")!=units:return None,"unit_mismatch"
        if e.get("epoch")!=epoch:return None,"stale_or_mixed_epoch"
        if e.get("kind")!="affine":return None,"unsupported_non_affine"
        M=e.get("matrix")
        if not isinstance(M,list) or len(M)!=2 or any(len(row)!=3 for row in M):return None,"malformed_matrix"
        H=[M[0],M[1],[0,0,1]]
        # L-infinity interval propagation; edge residual is in target-frame pixels.
        radius=[sum(abs(H[i][j])*radius[j] for j in range(2))+float(e.get("residual",0)) for i in range(2)]
        correlated={k:[sum(H[i][j]*v[j] for j in range(2)) for i in range(2)] for k,v in correlated.items()}
        if e.get("correlation_id"):
            k=e["correlation_id"]; v=e.get("correlated_error",[0.0,0.0]); old=correlated.get(k,[0.0,0.0]); correlated[k]=[old[i]+v[i] for i in range(2)]
        total=mul(H,total); cur=e.get("target"); units=e.get("target_units")
    if cur!=record["input_frame"] or units!=record["input_units"]:return None,"chain_endpoint_mismatch"
    return (total,radius,correlated),None

def inside_region(box,center,radius):
    x,y=center;rx,ry=radius
    return x-rx>=box[0] and y-ry>=box[1] and x+rx<=box[2] and y+ry<=box[3]
def intersects(box,center,radius):
    x,y=center;rx,ry=radius
    return not (x+rx<box[0] or x-rx>box[2] or y+ry<box[1] or y-ry>box[3])
def decide(record):
    if record.get("target_id")!=record.get("target_box_target_id"):return refuse("target_identity_binding_mismatch")
    c,err=chain(record)
    if err:return refuse(err)
    M,radius,correlated=c; mapped=apply(M,record["point"])
    region_corr=record.get("target_correlated_uncertainty",{})
    keys=set(correlated)|set(region_corr)
    relative=list(mapped)
    for k in keys:
        pv=correlated.get(k); rv=region_corr.get(k)
        if pv is not None and rv is not None:
            # Same declared latent shift acts on point and target region, so it cancels.
            continue
        v=pv if pv is not None else rv
        radius=[radius[i]+abs(v[i]) for i in range(2)]
    if not inside_region(record["target_box"],relative,radius):return refuse("uncertainty_not_wholly_inside_target")
    if any(intersects(b,relative,radius) for b in record.get("forbidden_boxes",[])):return refuse("uncertainty_intersects_forbidden")
    return {"decision":"ADMIT","reason":"typed_current_chain_inside_target","mapped":[relative[0],relative[1]],"radius":radius,"target_id":record["target_id"]}
def main():
    data=json.loads((ROOT/"candidate_input.json").read_text())
    out={"schema":"issue8185.candidate.output.v1","allocation":data["allocation"],"decisions":[{"case_id":r["case_id"],**decide(r)} for r in data["cases"]]}
    (ROOT/"candidate_output.json").write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
if __name__=="__main__":main()
