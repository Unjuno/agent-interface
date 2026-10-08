#!/usr/bin/env python3
"""Generate and evaluate the frozen exhaustive A08 request matrix."""
import hashlib,itertools,json,pathlib,platform,sys
PKG=pathlib.Path(__file__).resolve().parent; ROOT=PKG.parents[2]
def canon(v): return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()
def sha(b): return hashlib.sha256(b).hexdigest()
def make_frame(e,i,focus,distractor,design):
 h=design["dimensions"]["height"]; w=design["dimensions"]["width"]; px=[[0]*w for _ in range(h)]
 for y,row in enumerate(((11,12),(13,14))):
  for x,v in enumerate(row): px[2+y][2+x]=v
 for y,row in enumerate(((21,22),(23,24))):
  for x,v in enumerate(row): px[2+y][5+x]=v
 if distractor:
  for y in range(2):
   for x in range(2): px[y][x]=99
 fid=f"e{e}-{i}-{'focused' if focus else 'unfocused'}-d{distractor}"
 return {"frame_id":fid,"epoch":e,"identity":i,"focus_token":focus,"pixels":px,"regions":{k:{"bounds":v} for k,v in design["regions"].items()}}
def make_request(frame,qe,qi,qt,reason,rid,shape,bmode,fidmode):
 cs={"unique":[rid],"ambiguous":["target","other"],"empty":[]}[shape]
 region=frame["regions"].get(rid); declared=region["bounds"] if region else [0,0,2,2]
 x0,y0,x1,y1=declared
 bounds={"declared":declared,"empty":[x0,y0,x0,y1],"outside":[7,7,9,9],"wrong":[0,4,2,6] if rid=="target" else [0,0,2,2]}[bmode]
 return {"frame_id":frame["frame_id"] if fidmode=="current" else frame["frame_id"]+"-replaced","epoch":qe,"identity":qi,"focus_token":qt,"reason":reason,"region_id":rid,"candidate_region_ids":cs,"bounds":bounds,"bounds_mode":bmode,"candidate_shape":shape,"frame_id_mode":fidmode}
def full_evidence(frame): return {"mode":"FULL_FRAME","frame_id":frame["frame_id"],"epoch":frame["epoch"],"identity":frame["identity"],"pixels":frame["pixels"]}
def crop(px,b): x0,y0,x1,y1=b; return [row[x0:x1] for row in px[y0:y1]]
def evaluate(frame,q):
 if q["frame_id"]!=frame["frame_id"] or q["epoch"]!=frame["epoch"] or q["identity"]!=frame["identity"]: return {"decision":"REFUSE","reason":"stale_or_replaced","action_authorized":False}
 if q["focus_token"] is None or frame["focus_token"] is None or q["focus_token"]!=frame["focus_token"]: return {"decision":"REFUSE","reason":"focus_mismatch","action_authorized":False}
 if q["reason"]!="uncertain": return {"decision":"REFUSE","reason":"reason_mismatch","action_authorized":False}
 if q["candidate_region_ids"]!=[q["region_id"]]: return {"decision":"REFUSE","reason":"candidate_set_not_unique","action_authorized":False}
 region=frame["regions"].get(q["region_id"])
 if region is None: return {"decision":"REFUSE","reason":"unknown_region","action_authorized":False}
 b=q["bounds"]; x0,y0,x1,y1=b; h=len(frame["pixels"]); w=len(frame["pixels"][0])
 if not(0<=x0<x1<=w and 0<=y0<y1<=h) or b!=region["bounds"]: return {"decision":"REFUSE","reason":"bounds_mismatch","action_authorized":False}
 evidence={"mode":"DECLARED_FOCUS","frame_id":frame["frame_id"],"epoch":frame["epoch"],"identity":frame["identity"],"region_id":q["region_id"],"bounds":b,"pixels":crop(frame["pixels"],b)}
 full=full_evidence(frame)
 if len(canon(evidence))>=len(canon(full)): return {"decision":"FULL_FRAME_FALLBACK","evidence":full,"action_authorized":False}
 return {"decision":"DECLARED_FOCUS","evidence":evidence,"action_authorized":False}
def frame_rows(d):
 for e,i,f,p in itertools.product(d["frame_domains"]["epochs"],d["frame_domains"]["identities"],d["frame_domains"]["focus_states"],d["frame_domains"]["distractor_states"]): yield make_frame(e,i,f,p,d)
def request_rows(frame,d):
 domains=d["request_domains"]
 for values in itertools.product(domains["epochs"],domains["identities"],domains["focus_tokens"],domains["reasons"],domains["region_ids"],domains["candidate_shapes"],domains["bounds_modes"],domains["frame_id_modes"]): yield make_request(frame,*values)
def main():
 freeze=json.loads((PKG/"FREEZE.json").read_text())
 if (pathlib.Path(sys.executable).resolve().as_posix()!=freeze["python_executable"] or sys.version!=freeze["python_version"] or platform.platform()!=freeze["platform"] or platform.machine()!=freeze["machine"] or platform.release()!=freeze["kernel_release"]): raise SystemExit("frozen host/Python identity mismatch")
 for rel,h in freeze["inputs"].items():
  if sha((ROOT/rel).read_bytes())!=h: raise SystemExit("frozen input mismatch: "+rel)
 for rel,h in freeze["code_sources"].items():
  if sha((PKG/rel).read_bytes())!=h: raise SystemExit("frozen code mismatch: "+rel)
 d=json.loads((PKG/"design.json").read_text()); rows=[]
 for frame in frame_rows(d):
  raw=canon(frame); full=full_evidence(frame); full_size=len(canon(full)); fullq={"mode":"FULL_FRAME","frame_id":frame["frame_id"],"epoch":frame["epoch"],"identity":frame["identity"]}
  rows.append({"case_id":frame["frame_id"]+"/FULL_FRAME","frame":frame["frame_id"],"request":fullq,"frame_sha256":sha(raw),"full_payload_bytes":full_size,"result":{"decision":"FULL_FRAME","evidence":full,"action_authorized":False}})
  for q in request_rows(frame,d):
   rows.append({"case_id":frame["frame_id"]+"/MATRIX/"+str(len(rows)),"frame":frame["frame_id"],"request":q,"frame_sha256":sha(raw),"full_payload_bytes":full_size,"result":evaluate(frame,q)})
 out={"schema":"a08-candidate-v1","design_sha256":sha((PKG/"design.json").read_bytes()),"case_count":len(rows),"rows":rows}
 sys.stdout.write(canon(out).decode()+"\n")
if __name__=="__main__": main()
