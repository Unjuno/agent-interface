from __future__ import annotations
import argparse,json,statistics
from pathlib import Path
PREDICATES=("TARGET_CORRECT","FORM_COMPLETE","MODAL_BLOCKING","RECOVERY_NEEDED","INTENT_SUBMIT","ENVELOPE_VALID")
MAP={"TARGET_CORRECT":("target_pos","target_neg"),"FORM_COMPLETE":("form_pos","form_neg"),"MODAL_BLOCKING":("modal_pos","modal_neg"),"RECOVERY_NEEDED":("recovery_pos","recovery_neg"),"INTENT_SUBMIT":("intent_pos","intent_neg"),"ENVELOPE_VALID":("envelope_pos","envelope_neg")}
def truth(f,p):
 a,b=MAP[p]; pair=(f[a],f[b]); return "TRUE" if pair==(1,0) else ("FALSE" if pair==(0,1) else "UNKNOWN")
def graph(p):
 if any(p[k]=="UNKNOWN" for k in PREDICATES):return "YIELD_UNKNOWN"
 if p["ENVELOPE_VALID"]=="FALSE":return "YIELD_OUT_OF_ENVELOPE"
 if p["MODAL_BLOCKING"]=="TRUE":return "YIELD_MODAL"
 if p["TARGET_CORRECT"]=="FALSE":return "YIELD_TARGET"
 if p["FORM_COMPLETE"]=="FALSE":return "CONTINUE_FILL"
 if p["RECOVERY_NEEDED"]=="TRUE":return "RECOVER"
 if p["INTENT_SUBMIT"]!="TRUE":return "YIELD_INTENT"
 return "SUBMIT_READY"
def main(path):
 r=json.loads(Path(path).read_text());err=[]
 if r.get("support_rows")!=32:err.append("support_count")
 if r.get("eval_rows")!=256:err.append("eval_count")
 if len(r.get("records",[]))!=256:err.append("record_count")
 if r.get("formal_invocations")!=1 or any(r.get(k)!=0 for k in ("reruns","replacements","tuning")):err.append("formal_discipline")
 tc=unk=unkok=fe=ge=0
 for row in r.get("records",[]):
  f=row["features"]; labels={p:truth(f,p) for p in PREDICATES}; t=labels["TARGET_CORRECT"]
  got=row["specialist"];tc+=got==t
  if t=="UNKNOWN":unk+=1;unkok+=got=="UNKNOWN";fe+=got in {"TRUE","FALSE"}
  p2=dict(labels);p2["TARGET_CORRECT"]=got; ge+=graph(p2)==graph(labels)
  if row["truth"]!=t or row["graph_general"]!=graph(labels) or row["graph_specialist"]!=graph(p2):err.append(f"row:{row['i']}")
 if (tc,unkok,fe,ge)!=(256,unk,0,256):err.append("semantic_gate")
 art=r.get("artifact","").encode()
 if len(art)>1024:err.append("artifact_size")
 gt=r.get("general_batch_ns",[]);st=r.get("specialist_ns",[])
 if len(gt)!=9 or len(st)!=9 or any(x<=0 for x in gt+st):err.append("timing_shape")
 ratio=statistics.median(st)/statistics.median(gt) if not err else None
 if err:dec="STOP_INTEGRITY"
 elif ratio<=0.5:dec="PASS_TINY_PREDICATE_SPECIALIST_SCOPED"
 else:dec="HOLD_GENERAL_BACKEND_ALREADY_CHEAP"
 print(json.dumps({"decision":dec,"errors":err,"checks":{"target_correct":tc,"unknown":unk,"unknown_correct":unkok,"false_exec":fe,"graph_equal":ge,"timing_ratio":ratio}},sort_keys=True))
 return 0 if not err else 2
if __name__=="__main__":
 ap=argparse.ArgumentParser();ap.add_argument("raw");a=ap.parse_args();raise SystemExit(main(a.raw))
