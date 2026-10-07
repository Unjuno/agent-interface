#!/usr/bin/env python3
"""Independent finite oracle for lifecycle/cue recall and authority boundary."""
import argparse, copy, hashlib, json
from pathlib import Path
HERE=Path(__file__).resolve().parent

def oracle(f):
    item=f["intent"]; out=[]
    for state in f["lifecycle"]:
        for label,cue in f["cue_definitions"].items():
            same=cue.get("known") is True and cue.get("object_id")==item.get("object_id") and cue.get("state_id")==item.get("state_id")
            for method in f["policies"]:
                show=cue.get("known") is True if method=="PLAIN_TEXT" else state=="PENDING" and same
                if method=="RESUMPTION_PACKET": show=show and item.get("authority_generation") is not None and item.get("effect_receipt") is not None
                out.append({"lifecycle":state,"cue":label,"policy":method,"recalled":bool(show),
                            "decision":"INSPECT_AND_REVALIDATE" if show else "DO_NOT_RESUME","input_authorized":False})
    return out

def audit(raw,f):
    errors=[]
    if raw.get("fixture_sha256")!=hashlib.sha256((HERE/"fixture.json").read_bytes()).hexdigest(): errors.append("fixture digest mismatch")
    if raw.get("candidate_sha256")!=hashlib.sha256((HERE/"candidate.py").read_bytes()).hexdigest(): errors.append("candidate digest mismatch")
    expected=oracle(f)
    if raw.get("rows")!=expected: errors.append("rows differ from independent oracle")
    if any(r.get("input_authorized") is not False for r in raw.get("rows",[])): errors.append("retrieval conveyed input authority")
    return errors

def corruptions(raw):
    cases={}
    edits=[("ignore_terminal_lifecycle",lambda r:r["lifecycle"]=="CANCELLED" and r["cue"]=="EXACT_OBJECT_STATE" and r["policy"]=="TYPED_LIFECYCLE",{"recalled":True}),
           ("ignore_object_identity",lambda r:r["lifecycle"]=="PENDING" and r["cue"]=="SAME_LABEL_WRONG_OBJECT" and r["policy"]=="TYPED_LIFECYCLE",{"recalled":True}),
           ("grant_input_authority",lambda r:r["lifecycle"]=="PENDING" and r["cue"]=="EXACT_OBJECT_STATE" and r["policy"]=="RESUMPTION_PACKET",{"input_authorized":True}),
           ("revive_unknown_effect",lambda r:r["lifecycle"]=="UNKNOWN_EFFECT" and r["cue"]=="EXACT_OBJECT_STATE" and r["policy"]=="TYPED_LIFECYCLE",{"recalled":True})]
    for name,pred,change in edits:
        value=copy.deepcopy(raw); row=next(r for r in value["rows"] if pred(r)); row.update(change); cases[name]=value
    return cases

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--raw",required=True,type=Path); ap.add_argument("--out",required=True,type=Path); a=ap.parse_args()
    f=json.loads((HERE/"fixture.json").read_text(encoding="utf-8")); raw=json.loads(a.raw.read_text(encoding="utf-8")); errors=audit(raw,f); controls={}
    for name,changed in corruptions(raw).items():
        found=audit(changed,f); controls[name]={"rejected":bool(found),"errors":len(found)}
        if not found: errors.append("mutation accepted: "+name)
    result={"status":"PASS_METHOD_SCOPED" if not errors else "FAIL_METHOD","rows_reconstructed":len(oracle(f)),
            "safe_terminal_revivals":sum(r["recalled"] for r in oracle(f) if r["policy"]!="PLAIN_TEXT" and r["lifecycle"]!="PENDING"),
            "mutations":controls,"errors":errors,"scope":"finite synthetic cue/lifecycle policy; no live safety or model claim"}
    a.out.parent.mkdir(parents=True,exist_ok=True); a.out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,sort_keys=True)); raise SystemExit(0 if not errors else 1)
if __name__=="__main__": main()
