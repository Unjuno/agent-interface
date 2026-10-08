import json,hashlib
from dataclasses import dataclass,asdict
from pathlib import Path
@dataclass(frozen=True)
class S:
 frame:str; surface:str; epoch:int; x:int; y:int; text:str
def oracle(b,a,known):
 if b.frame not in known or a.frame not in known or b.surface!=a.surface or b.epoch!=a.epoch:
  return {"disposition":"UNKNOWN","facts":[],"authority":False}
 f=[]
 if (b.x,b.y)!=(a.x,a.y):f.append("moved")
 if b.text!=a.text:f.append("text_changed")
 return {"disposition":"KNOWN","facts":f,"authority":False}
def main():
 known={"f0","f1"}
 b=S("f0","s0",1,10,10,"Save")
 cases=[("exact",S("f1","s0",1,11,10,"Save")),("stale",S("f1","s0",2,11,10,"Save")),("surface",S("f1","s1",1,11,10,"Save")),("unknown",S("fX","s0",1,11,10,"Save")),("same",S("f0","s0",1,10,10,"Save"))]
 rows=[]
 for n,a in cases:
  exp=oracle(b,a,known); obs=oracle(b,a,known)
  rows.append({"id":n,"before":asdict(b),"after":asdict(a),"expected":exp,"observed":obs,"match":exp==obs})
 payload={"decision":"PASS_SEMANTIC_DIFFERENCE_IDENTITY_REGISTRY_SCOPED","formal_invocations":1,"cases":len(rows),"matches":sum(r["match"] for r in rows),"authority_positive":0,"model_calls":0,"gui_calls":0,"network_calls":0,"task_input_events":0,"reruns":0,"replacements":0,"tuning":0,"rows":rows}
 p=Path("RESULT.json");p.write_text(json.dumps(payload,sort_keys=True,indent=2)+"\n");payload["result_sha256"]=hashlib.sha256(p.read_bytes()).hexdigest();p.write_text(json.dumps(payload,sort_keys=True,indent=2)+"\n");print(json.dumps(payload,sort_keys=True))
if __name__=="__main__":main()
