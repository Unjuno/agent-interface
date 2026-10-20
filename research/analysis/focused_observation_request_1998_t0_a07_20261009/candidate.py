#!/usr/bin/env python3
"""Deterministic candidate for the frozen finite focused-observation fixture."""
import hashlib, json, pathlib, platform, sys
PKG=pathlib.Path(__file__).resolve().parent
ROOT=PKG.parents[2]
def canonical(x): return json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()
def sha(b): return hashlib.sha256(b).hexdigest()
def crop(pixels,bounds):
 x0,y0,x1,y1=bounds
 return [row[x0:x1] for row in pixels[y0:y1]]
def evaluate(frame,request):
 if request.get("frame_id")!=frame["frame_id"] or request.get("epoch")!=frame["epoch"] or request.get("identity")!=frame["identity"]:
  return {"decision":"REFUSE","reason":"stale_or_replaced","action_authorized":False}
 if request.get("mode")=="FULL_FRAME":
  evidence={"mode":"FULL_FRAME","frame_id":frame["frame_id"],"epoch":frame["epoch"],"identity":frame["identity"],"pixels":frame["pixels"]}
  return {"decision":"FULL_FRAME","evidence":evidence,"action_authorized":False}
 if request.get("mode")!="DECLARED_FOCUS" or request.get("reason")!="uncertain":
  return {"decision":"REFUSE","reason":"mode_or_reason","action_authorized":False}
 if request.get("focus_token")!=frame.get("focus_token") or frame.get("focus_token") is None:
  return {"decision":"REFUSE","reason":"focus_lost","action_authorized":False}
 candidates=request.get("candidate_region_ids")
 if not isinstance(candidates,list) or len(candidates)!=1 or candidates[0]!=request.get("region_id"):
  return {"decision":"REFUSE","reason":"ambiguous_region","action_authorized":False}
 region=frame["regions"].get(request.get("region_id"))
 if region is None:
  return {"decision":"REFUSE","reason":"unknown_region","action_authorized":False}
 bounds=request.get("bounds_override",region["bounds"])
 if (not isinstance(bounds,list) or len(bounds)!=4 or any(type(v) is not int for v in bounds)):
  return {"decision":"REFUSE","reason":"malformed_bounds","action_authorized":False}
 x0,y0,x1,y1=bounds; height=len(frame["pixels"]); width=len(frame["pixels"][0])
 if not (0<=x0<x1<=width and 0<=y0<y1<=height) or bounds!=region["bounds"]:
  return {"decision":"REFUSE","reason":"invalid_bounds","action_authorized":False}
 evidence={"mode":"DECLARED_FOCUS","frame_id":frame["frame_id"],"epoch":frame["epoch"],"identity":frame["identity"],"region_id":request["region_id"],"bounds":bounds,"pixels":crop(frame["pixels"],bounds)}
 full={"mode":"FULL_FRAME","frame_id":frame["frame_id"],"epoch":frame["epoch"],"identity":frame["identity"],"pixels":frame["pixels"]}
 if len(canonical(evidence))>=len(canonical(full)):
  return {"decision":"FULL_FRAME_FALLBACK","evidence":full,"action_authorized":False}
 return {"decision":"DECLARED_FOCUS","evidence":evidence,"action_authorized":False}
def main():
 freeze=json.loads((PKG/"FREEZE.json").read_text())
 if (pathlib.Path(sys.executable).resolve().as_posix()!=freeze["python_executable"] or sys.version!=freeze["python_version"] or platform.platform()!=freeze["platform"] or platform.machine()!=freeze["machine"] or platform.release()!=freeze["kernel_release"]): raise SystemExit("frozen host/Python identity mismatch")
 for rel,h in freeze["inputs"].items():
  if sha((ROOT/rel).read_bytes())!=h: raise SystemExit("frozen input mismatch: "+rel)
 for rel,h in freeze["code_sources"].items():
  if sha((PKG/rel).read_bytes())!=h: raise SystemExit("frozen code mismatch: "+rel)
 design=json.loads((PKG/"design.json").read_text()); rows=[]
 for original in design["frames"]:
  frame=original
  for template in design["requests"]:
   req=dict(template); req["frame_id"]=frame["frame_id"]
   result=evaluate(frame,req)
   rows.append({"case_id":frame["frame_id"]+"/"+req["case"],"frame_id":frame["frame_id"],"request":req,"frame_sha256":sha(canonical(frame)),"result":result})
 out={"schema":"a07-candidate-v1","design_sha256":sha((PKG/"design.json").read_bytes()),"case_count":len(rows),"rows":rows}
 sys.stdout.write(canonical(out).decode()+"\n")
if __name__=="__main__": main()
