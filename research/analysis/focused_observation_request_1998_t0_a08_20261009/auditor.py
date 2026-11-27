#!/usr/bin/env python3
"""Independent raw-only exhaustive oracle and mutation audit for A08."""
import copy,hashlib,itertools,json,pathlib,sys
PKG=pathlib.Path(__file__).resolve().parent; ROOT=PKG.parents[2]
def canonical(v): return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()
def digest(b): return hashlib.sha256(b).hexdigest()
def reconstruct_frame(epoch,identity,focus,distractor,design):
 width=design["dimensions"]["width"]; height=design["dimensions"]["height"]; pixels=[[0 for _ in range(width)] for _ in range(height)]
 for dy in range(2):
  for dx in range(2):
   pixels[2+dy][2+dx]=(11,12,13,14)[dy*2+dx]
   pixels[2+dy][5+dx]=(21,22,23,24)[dy*2+dx]
 if distractor==1:
  pixels[0][0]=pixels[0][1]=pixels[1][0]=pixels[1][1]=99
 return {"frame_id":f"e{epoch}-{identity}-{'focused' if focus else 'unfocused'}-d{distractor}","epoch":epoch,"identity":identity,"focus_token":focus,"pixels":pixels,"regions":{k:{"bounds":b} for k,b in design["regions"].items()}}
def pixel_window(pixels,bounds):
 left,top,right,bottom=bounds
 return [line[left:right] for line in pixels[top:bottom]]
def request_permutations(frame,domains):
 for ep,ident,focus,reason,region,shape,bounds,frame_mode in itertools.product(domains["epochs"],domains["identities"],domains["focus_tokens"],domains["reasons"],domains["region_ids"],domains["candidate_shapes"],domains["bounds_modes"],domains["frame_id_modes"]):
  desc=frame["regions"].get(region); rect=desc["bounds"] if desc else [0,0,2,2]; x0,y0,x1,y1=rect
  candidates=[region] if shape=="unique" else (["target","other"] if shape=="ambiguous" else [])
  box=rect if bounds=="declared" else ([x0,y0,x0,y1] if bounds=="empty" else ([7,7,9,9] if bounds=="outside" else ([0,4,2,6] if region=="target" else [0,0,2,2])))
  yield {"frame_id":frame["frame_id"] if frame_mode=="current" else frame["frame_id"]+"-replaced","epoch":ep,"identity":ident,"focus_token":focus,"reason":reason,"region_id":region,"candidate_region_ids":candidates,"bounds":box,"bounds_mode":bounds,"candidate_shape":shape,"frame_id_mode":frame_mode}
def full_evidence(frame): return {"mode":"FULL_FRAME","frame_id":frame["frame_id"],"epoch":frame["epoch"],"identity":frame["identity"],"pixels":frame["pixels"]}
def expected_focused(frame,q):
 if q["frame_id"]!=frame["frame_id"] or q["epoch"]!=frame["epoch"] or q["identity"]!=frame["identity"]: return None
 if frame["focus_token"] is None or q["focus_token"]!=frame["focus_token"] or q["reason"]!="uncertain": return None
 if q["candidate_region_ids"]!=[q["region_id"]]: return None
 region=frame["regions"].get(q["region_id"])
 if region is None or q["bounds"]!=region["bounds"]: return None
 x0,y0,x1,y1=q["bounds"]; h=len(frame["pixels"]); w=len(frame["pixels"][0])
 if not(0<=x0<x1<=w and 0<=y0<y1<=h): return None
 return {"mode":"DECLARED_FOCUS","frame_id":frame["frame_id"],"epoch":frame["epoch"],"identity":frame["identity"],"region_id":q["region_id"],"bounds":q["bounds"],"pixels":pixel_window(frame["pixels"],q["bounds"])}
def expected_cases(design):
 cases=[]; domains=design["request_domains"]
 states=itertools.product(design["frame_domains"]["epochs"],design["frame_domains"]["identities"],design["frame_domains"]["focus_states"],design["frame_domains"]["distractor_states"])
 for ep,ident,focus,distractor in states:
  frame=reconstruct_frame(ep,ident,focus,distractor,design); full=full_evidence(frame); full_size=len(canonical(full)); frame_hash=digest(canonical(frame))
  fq={"mode":"FULL_FRAME","frame_id":frame["frame_id"],"epoch":ep,"identity":ident}
  cases.append((frame["frame_id"]+"/FULL_FRAME",frame,fq,frame_hash,full_size,"FULL_FRAME",full))
  for q in request_permutations(frame,domains):
   n=len(cases); expected=expected_focused(frame,q); decision="REFUSE"; evidence=None
   if expected is not None:
    if len(canonical(expected))<full_size: decision="DECLARED_FOCUS"; evidence=expected
    else: decision="FULL_FRAME_FALLBACK"; evidence=full
   cases.append((frame["frame_id"]+"/MATRIX/"+str(n),frame,q,frame_hash,full_size,decision,evidence))
 return cases
def validate(raw,design,freeze):
 errors=[]; expected=expected_cases(design); rows=raw.get("rows",[])
 if raw.get("schema")!="a08-candidate-v1" or raw.get("case_count")!=len(expected) or len(rows)!=len(expected): errors.append("coverage")
 if raw.get("design_sha256")!=freeze["design_sha256"]: errors.append("design-identity")
 ids=[r.get("case_id") for r in rows]
 if len(set(ids))!=len(ids): errors.append("duplicate-case-id")
 if ids!=[x[0] for x in expected]: errors.append("case-order-or-identity")
 decisions={}
 focus_pixels={}; full_pixels={}
 for i,(case,frame,q,frame_hash,full_size,decision,evidence) in enumerate(expected):
  if i>=len(rows): break
  row=rows[i]; got=row.get("result",{})
  if row.get("case_id")!=case or row.get("frame")!=frame["frame_id"] or row.get("request")!=q: errors.append("row-binding:"+str(i))
  if row.get("frame_sha256")!=frame_hash: errors.append("frame-hash:"+str(i))
  if row.get("full_payload_bytes")!=full_size: errors.append("full-payload-size:"+str(i))
  if got.get("decision")!=decision: errors.append("decision:"+str(i))
  if got.get("action_authorized") is not False: errors.append("action-authority:"+str(i))
  if evidence is None:
   if "evidence" in got: errors.append("refusal-contained-evidence:"+str(i))
  elif got.get("evidence")!=evidence: errors.append("evidence-pixels-or-metadata:"+str(i))
  if decision=="FULL_FRAME": full_pixels[frame["frame_id"]]=got.get("evidence",{}).get("pixels")
  if decision=="DECLARED_FOCUS":
   focus_pixels[(frame["epoch"],frame["identity"],q["region_id"],frame["focus_token"])]=got.get("evidence",{}).get("pixels")
   if len(canonical(got.get("evidence")))>=full_size: errors.append("focused-not-smaller:"+str(i))
  decisions[decision]=decisions.get(decision,0)+1
 if len(expected)==27664 and decisions!={"FULL_FRAME":16,"DECLARED_FOCUS":16,"REFUSE":27632}: errors.append("decision-census")
 if len(full_pixels)!=16: errors.append("full-frame-control-count")
 return errors
def mutation_cases(raw):
 def corrupt_crop(x):
  row=next(r for r in x["rows"] if r["result"].get("decision")=="DECLARED_FOCUS")
  row["result"]["evidence"]["pixels"][0][0]+=1
 def alter_full(x):
  row=next(r for r in x["rows"] if r["result"].get("decision")=="FULL_FRAME")
  row["result"]["evidence"]["pixels"][0][0]+=1
 def grant_action(x): x["rows"][0]["result"]["action_authorized"]=True
 def wrong_hash(x): x["rows"][0]["frame_sha256"]="0"*64
 def accept_stale(x):
  row=next(r for r in x["rows"] if r["result"].get("decision")=="REFUSE" and r["request"].get("epoch")!=next(c for c in x["rows"] if c["case_id"]==r["frame"]+"/FULL_FRAME")["request"]["epoch"])
  row["result"]={"decision":"DECLARED_FOCUS","evidence":{"mode":"DECLARED_FOCUS"},"action_authorized":False}
 return [("drop-row",lambda x:x["rows"].pop(),"coverage"),("corrupt-focused-pixels",corrupt_crop,"evidence-pixels-or-metadata:"),("corrupt-full-frame-pixels",alter_full,"evidence-pixels-or-metadata:"),("grant-action",grant_action,"action-authority:"),("wrong-frame-hash",wrong_hash,"frame-hash:"),("accept-stale",accept_stale,"decision:")]
def detects_new_error(before,after,prefix): return any(e not in before and e.startswith(prefix) for e in after)
def main():
 design=json.loads((PKG/"design.json").read_text()); freeze=json.loads((PKG/"FREEZE.json").read_text()); raw=json.load(sys.stdin); errors=validate(raw,design,freeze)
 for rel,h in freeze["inputs"].items():
  try:
   if digest((ROOT/rel).read_bytes())!=h: errors.append("frozen-input:"+rel)
  except OSError: errors.append("frozen-input-missing:"+rel)
 for rel,h in freeze["code_sources"].items():
  if digest((PKG/rel).read_bytes())!=h: errors.append("frozen-code:"+rel)
 if digest((PKG/"design.json").read_bytes())!=freeze["design_sha256"]: errors.append("frozen-design")
 controls=[]; baseline=set(errors)
 for name,mutate,prefix in mutation_cases(raw):
  changed=copy.deepcopy(raw); mutate(changed); changed_errors=validate(changed,design,freeze)
  rejected=detects_new_error(baseline,changed_errors,prefix); controls.append({"name":name,"rejected":rejected,"detector_prefix":prefix})
 if not all(c["rejected"] for c in controls): errors.append("mutation-controls")
 result={"schema":"a08-audit-v1","errors":errors,"case_count":len(raw.get("rows",[])),"mutation_controls":controls,"disposition":"PASS_METHOD_SCOPED" if not errors else "STOP_AUDIT"}
 print(json.dumps(result,sort_keys=True,separators=(",",":"))); return 0 if not errors else 1
if __name__=="__main__": raise SystemExit(main())
