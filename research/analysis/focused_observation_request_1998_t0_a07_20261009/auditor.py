#!/usr/bin/env python3
"""Independent raw-only audit; oracle is separately written from candidate."""
import copy,hashlib,json,pathlib,sys
PKG=pathlib.Path(__file__).resolve().parent
def canon(x): return json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()
def sha(b): return hashlib.sha256(b).hexdigest()
def oracle(frame,q):
 if (q.get("frame_id"),q.get("epoch"),q.get("identity"))!=(frame["frame_id"],frame["epoch"],frame["identity"]): return ("REFUSE",None)
 if q.get("mode")=="FULL_FRAME": return ("FULL_FRAME",{"mode":"FULL_FRAME","frame_id":frame["frame_id"],"epoch":frame["epoch"],"identity":frame["identity"],"pixels":frame["pixels"]})
 if q.get("mode")!="DECLARED_FOCUS" or q.get("reason")!="uncertain": return ("REFUSE",None)
 if frame.get("focus_token") is None or q.get("focus_token")!=frame.get("focus_token"): return ("REFUSE",None)
 if q.get("candidate_region_ids")!=[q.get("region_id")]: return ("REFUSE",None)
 r=frame["regions"].get(q.get("region_id"))
 if r is None: return ("REFUSE",None)
 b=q.get("bounds_override",r["bounds"])
 if not isinstance(b,list) or len(b)!=4 or any(type(v)is not int for v in b): return ("REFUSE",None)
 x0,y0,x1,y1=b; h=len(frame["pixels"]); w=len(frame["pixels"][0])
 if not(0<=x0<x1<=w and 0<=y0<y1<=h) or b!=r["bounds"]: return ("REFUSE",None)
 pixels=[row[x0:x1] for row in frame["pixels"][y0:y1]]
 f={"mode":"FULL_FRAME","frame_id":frame["frame_id"],"epoch":frame["epoch"],"identity":frame["identity"],"pixels":frame["pixels"]}
 e={"mode":"DECLARED_FOCUS","frame_id":frame["frame_id"],"epoch":frame["epoch"],"identity":frame["identity"],"region_id":q["region_id"],"bounds":b,"pixels":pixels}
 if len(canon(e))>=len(canon(f)): return ("FULL_FRAME_FALLBACK",f)
 return ("DECLARED_FOCUS",e)
def check(raw,design,freeze_sha,inputs):
 errors=[]; rows=raw.get("rows",[]); frames={f["frame_id"]:f for f in design["frames"]}; expected={f["frame_id"]+"/"+q["case"]:(f,q) for f in design["frames"] for t in design["requests"] for q in [{**t,"frame_id":f["frame_id"]}]}
 ids=[r.get("case_id") for r in rows]
 if raw.get("schema")!="a07-candidate-v1" or raw.get("case_count")!=len(expected) or len(rows)!=len(expected): errors.append("coverage")
 if len(set(ids))!=len(ids) or set(ids)!=set(expected): errors.append("identity")
 if raw.get("design_sha256")!=freeze_sha: errors.append("design-freeze")
 focus_results={}; full_results={}
 for row in rows:
  pair=expected.get(row.get("case_id"))
  if pair is None: continue
  frame,q=pair; kind,want=oracle(frame,q); got=row.get("result",{})
  if row.get("frame_id")!=frame["frame_id"] or row.get("request")!=q or row.get("frame_sha256")!=sha(canon(frame)): errors.append("source-binding:"+row["case_id"])
  if got.get("decision")!=kind: errors.append("decision:"+row["case_id"])
  if got.get("action_authorized") is not False: errors.append("authority:"+row["case_id"])
  if want is None:
   if "evidence" in got: errors.append("refusal-evidence:"+row["case_id"])
  elif got.get("evidence")!=want: errors.append("evidence-bytes:"+row["case_id"])
  if kind=="DECLARED_FOCUS": focus_results[frame["frame_id"]]=got.get("evidence",{}).get("pixels")
  if kind=="FULL_FRAME": full_results[frame["frame_id"]]=got.get("evidence",{}).get("pixels")
  if kind=="DECLARED_FOCUS":
   f={"mode":"FULL_FRAME","frame_id":frame["frame_id"],"epoch":frame["epoch"],"identity":frame["identity"],"pixels":frame["pixels"]}
   if len(canon(got.get("evidence")))>=len(canon(f)): errors.append("non-saving-focus:"+row["case_id"])
 if full_results!={f["frame_id"]:f["pixels"] for f in design["frames"]}: errors.append("full-frame-exactness")
 if focus_results.get("frame-7-base")!=focus_results.get("frame-7-distractor-change"): errors.append("distractor-invariance")
 return errors
def main():
 design=json.loads((PKG/"design.json").read_text()); raw=json.load(sys.stdin); freeze=json.loads((PKG/"FREEZE.json").read_text()); errors=check(raw,design,freeze["design_sha256"],freeze["inputs"])
 for rel,h in freeze["inputs"].items():
  try:
   if sha((PKG.parents[2]/rel).read_bytes())!=h: errors.append("frozen-input:"+rel)
  except OSError: errors.append("frozen-input-missing:"+rel)
 for rel,h in freeze["code_sources"].items():
  if sha((PKG/rel).read_bytes())!=h: errors.append("frozen-code:"+rel)
 if sha((PKG/"design.json").read_bytes())!=freeze["design_sha256"]: errors.append("frozen-design")
 controls=[]
 muts=[("drop-row",lambda x:x["rows"].pop()),("duplicate-id",lambda x:x["rows"].__setitem__(1,copy.deepcopy(x["rows"][0]))),("corrupt-focused-pixels",lambda x:x["rows"][1]["result"]["evidence"]["pixels"][0].__setitem__(0,"X")),("grant-action",lambda x:x["rows"][0]["result"].__setitem__("action_authorized",True)),("wrong-frame-hash",lambda x:x["rows"][0].__setitem__("frame_sha256","0"*64)),("accept-stale",lambda x:x["rows"][2]["result"].update({"decision":"DECLARED_FOCUS","evidence":{"mode":"DECLARED_FOCUS"}}))]
 for name,mut in muts:
  altered=copy.deepcopy(raw); mut(altered); caught=bool(check(altered,design,freeze["design_sha256"],freeze["inputs"])); controls.append({"name":name,"rejected":caught})
 if not all(c["rejected"] for c in controls): errors.append("mutation-controls")
 decisions={}
 for r in raw.get("rows",[]):
  d=r.get("result",{}).get("decision"); decisions[d]=decisions.get(d,0)+1
 result={"schema":"a07-audit-v1","errors":errors,"case_count":len(raw.get("rows",[])),"decision_counts":decisions,"mutation_controls":controls,"disposition":"PASS_METHOD_SCOPED" if not errors else "STOP_AUDIT"}
 print(json.dumps(result,sort_keys=True,separators=(",",":"))); return 0 if not errors else 1
if __name__=="__main__": raise SystemExit(main())
