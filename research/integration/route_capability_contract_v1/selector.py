#!/usr/bin/env python3
import hashlib,json
from pathlib import Path
KNOWN={"scale","center"}; BAND=(0.45,0.55)
def blob(b): return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def catalog(root):
 sraw=(root/"evidence/scale-audit.json").read_bytes(); craw=(root/"evidence/center-summary.json").read_bytes()
 if blob(sraw)!="389fe8cd93603c0415480fc398664a903dede0f4" or blob(craw)!="28bc4a8c07958db58efe98eb73881cbced46c481": raise ValueError("evidence_identity")
 s=json.loads(sraw); c=json.loads(craw); cw=c["route_stats"]["ctrl_wheel"]; n=c["route_stats"]["native_fixed80"]; one=s["route_ratios"]["one_contact_negative"]
 return {"ctrl_wheel":{"dims":["scale","center"] if cw["scale_matches"]==cw["n"]==cw["full_contract_matches"] else [],"any":cw["scale_matches"]>0},"native_fixed80":{"dims":["scale"] if n["scale_matches"]==n["n"] else [],"any":n["scale_matches"]>0},"one_contact_negative":{"dims":["scale"] if all(BAND[0]<=x<=BAND[1] for x in one) else [],"any":False}}
def choose(req,cat,policy):
 dims=req.get("required_dimensions"); routes=req.get("allowed_routes")
 if not isinstance(dims,list) or not dims or any(d not in KNOWN for d in dims) or not isinstance(routes,list) or not routes: return {"status":"INVALID_REQUEST","route":None}
 for r in routes:
  cap=cat.get(r)
  if cap and ((policy=="flat" and cap["any"]) or (policy=="dim" and set(dims)<=set(cap["dims"]))): return {"status":"SELECTED","route":r}
 if all(r not in cat for r in routes): return {"status":"UNSUPPORTED_PROVENANCE","route":None}
 return {"status":"UNSUPPORTED","route":None}
if __name__=="__main__":
 toy={"a":{"dims":["scale"],"any":True},"b":{"dims":["scale","center"],"any":True}}; q={"required_dimensions":["scale","center"],"allowed_routes":["a","b"]}; assert choose(q,toy,"flat")["route"]=="a" and choose(q,toy,"dim")["route"]=="b"; print("SELFTEST_PASS")
