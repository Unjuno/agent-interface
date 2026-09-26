from __future__ import annotations
import json,pathlib,sys
BASES=("anchor","gate","unrelated"); DERIVED=("A","B","C","D")
SUPPORTS={"A":(("anchor",),("B",)),"B":(("A",),),"C":(("B","gate"),),"D":(("unrelated",),)}
DEPENDENTS={"anchor":{"A"},"gate":{"C"},"unrelated":{"D"},"A":{"B"},"B":{"A","C"},"C":set(),"D":set()}
def a3(vals):
 v=list(vals)
 if any(x=="FALSE" for x in v): return "FALSE"
 if v and all(x=="TRUE" for x in v): return "TRUE"
 return "UNKNOWN"
def o3(vals):
 v=list(vals)
 if any(x=="TRUE" for x in v): return "TRUE"
 if v and all(x=="FALSE" for x in v): return "FALSE"
 return "UNKNOWN"
def solve(base):
 cur={d:"UNKNOWN" for d in DERIVED}
 for _ in range(16):
  nxt={}
  for d in DERIVED:
   groups=[]
   for s in SUPPORTS[d]: groups.append(a3(base[x] if x in base else cur[x] for x in s))
   nxt[d]=o3(groups)
  if nxt==cur:return cur
  cur=nxt
 return cur
def region(changed):
 q=list(changed); seen=set()
 while q:
  x=q.pop(0)
  for y in DEPENDENTS.get(x,()):
   if y not in seen:seen.add(y);q.append(y)
 return seen
def macro(v): return a3([v["C"],v["D"]])
def audit(data):
 errs=[]; stale=0; stale_list=[]; cr=0; gr=0
 rows=data.get("rows",[])
 if len(rows)!=12: errs.append("row_count")
 for i,r in enumerate(rows):
  if r.get("step")!=i:errs.append("order")
  base=r.get("base",{}); oracle=solve(base)
  if r.get("oracle")!=oracle:errs.append("oracle")
  if r.get("candidate")!=oracle:errs.append("candidate")
  rr=region(r.get("changed",[])); cr+=len(rr); gr+=4
  if set(r.get("affected",[]))!=rr:errs.append("affected")
  if r.get("candidate_macro")!=macro(oracle) or r.get("oracle_macro")!=macro(oracle):errs.append("macro")
  if r.get("authority")!="none":errs.append("authority")
  for d in DERIVED:
   if r.get("candidate",{}).get(d)=="TRUE" and oracle[d]!="TRUE":errs.append("unsupported_candidate_true")
   if r.get("naive",{}).get(d)=="TRUE" and oracle[d]!="TRUE":
    stale+=1; stale_list.append([r.get("name"),d,oracle[d]])
 if data.get("candidate_recomputes")!=cr:errs.append("candidate_recomputes")
 if data.get("global_recomputes")!=gr:errs.append("global_recomputes")
 if not cr<gr:errs.append("no_recompute_gain")
 for nm in ["ANCHOR_FALSE","ANCHOR_UNKNOWN","ANCHOR_FALSE_AGAIN"]:
  rr=next((x for x in rows if x.get("name")==nm),None)
  if not rr or any(rr["candidate"][d]=="TRUE" for d in ("A","B","C")):errs.append("anchor_retraction_"+nm)
 for nm in ["UNRELATED_FALSE","UNRELATED_RESTORE","UNRELATED_UNKNOWN","UNRELATED_RESTORE_AGAIN"]:
  rr=next((x for x in rows if x.get("name")==nm),None)
  if rr and any(d in rr.get("affected",[]) for d in ("A","B","C")):errs.append("unrelated_scope")
 if data.get("naive_stale_true")!=stale_list:errs.append("naive_stale_summary")
 if stale<2:errs.append("naive_discriminator")
 return {"errors":sorted(set(errs)),"rows":len(rows),"naive_stale_true_rows":stale,"candidate_recomputes":cr,"global_recomputes":gr,"pass":not errs}
def main():
 p=pathlib.Path(sys.argv[1]); d=json.loads(p.read_text()); out=audit(d); print(json.dumps(out,sort_keys=True)); sys.exit(0 if out["pass"] else 1)
if __name__=="__main__":main()
