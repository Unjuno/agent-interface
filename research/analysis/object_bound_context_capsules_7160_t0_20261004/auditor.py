#!/usr/bin/env python3
"""Independent oracle for identity-bound capsule retrieval."""
import argparse,copy,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent

def oracle(f):
    cap=f["capsule"];rows=[]
    for case in f["cases"]:
        for policy in f["policies"]:
            if policy=="SIMILARITY_ONLY": found=case.get("label")==cap["label"]
            elif policy=="IDENTITY_BOUND":
                found=(case.get("object_id") is not None and case.get("object_id")==cap.get("object_id")
                       and case.get("generation")==cap.get("generation"))
            else:found=False
            stale=sorted(name for name in f["mutable_fields"] if found and name in case)
            rows.append({"case":case["id"],"policy":policy,"retrieved":bool(found),
                         "capsule_id":cap["id"] if found else None,"stale_fields":stale,"input_authorized":False})
    return rows

def audit(raw,f):
    errors=[]
    if raw.get("fixture_sha256")!=hashlib.sha256((HERE/"fixture.json").read_bytes()).hexdigest():errors.append("fixture digest mismatch")
    if raw.get("candidate_sha256")!=hashlib.sha256((HERE/"candidate.py").read_bytes()).hexdigest():errors.append("candidate digest mismatch")
    if raw.get("rows")!=oracle(f):errors.append("retrieval rows differ from independent oracle")
    for row in raw.get("rows",[]):
        if row.get("input_authorized") is not False:errors.append("capsule granted input authority")
        if row.get("policy")=="IDENTITY_BOUND" and row.get("case") in ("lookalike_different_object","duplicate_label","recycled_id_new_generation","identity_unavailable") and row.get("retrieved"):errors.append("wrong/recycled/unknown identity accepted")
        if row.get("policy")=="IDENTITY_BOUND" and row.get("retrieved") and row.get("case")=="same_object_moved" and "location" not in row.get("stale_fields",[]):errors.append("moved-object location was not invalidated")
    return errors

def mutations(raw):
    cases={}
    for name,select,change in [
      ("ignore_generation",lambda r:r["case"]=="recycled_id_new_generation" and r["policy"]=="IDENTITY_BOUND",{"retrieved":True,"capsule_id":"capsule-17"}),
      ("accept_lookalike",lambda r:r["case"]=="lookalike_different_object" and r["policy"]=="IDENTITY_BOUND",{"retrieved":True,"capsule_id":"capsule-17"}),
      ("trust_unknown_identity",lambda r:r["case"]=="identity_unavailable" and r["policy"]=="IDENTITY_BOUND",{"retrieved":True,"capsule_id":"capsule-17"}),
      ("grant_input_authority",lambda r:r["policy"]=="IDENTITY_BOUND" and r["retrieved"],{"input_authorized":True})]:
        v=copy.deepcopy(raw);next(r for r in v["rows"] if select(r)).update(change);cases[name]=v
    return cases

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--raw",required=True,type=Path);ap.add_argument("--out",required=True,type=Path);a=ap.parse_args()
    f=json.loads((HERE/"fixture.json").read_text(encoding="utf-8"));raw=json.loads(a.raw.read_text(encoding="utf-8"));errors=audit(raw,f);controls={}
    for name,v in mutations(raw).items():
        e=audit(v,f);controls[name]={"rejected":bool(e),"errors":len(e)}
        if not e:errors.append("mutation accepted: "+name)
    safe=[r for r in oracle(f) if r["policy"]=="IDENTITY_BOUND"]
    result={"status":"PASS_METHOD_SCOPED" if not errors else "FAIL_METHOD","rows_reconstructed":len(oracle(f)),
      "wrong_recycled_unknown_retrievals":sum(r["retrieved"] for r in safe if r["case"] in ("lookalike_different_object","duplicate_label","recycled_id_new_generation","identity_unavailable")),
      "same_object_retrieved":sum(r["retrieved"] for r in safe if r["case"].startswith("same_object")),
      "mutations":controls,"errors":errors,"scope":"finite identity fixture only; no visual re-identification or live safety claim"}
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8");print(json.dumps(result,sort_keys=True));raise SystemExit(0 if not errors else 1)
if __name__=="__main__":main()
