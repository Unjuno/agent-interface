from __future__ import annotations
import argparse, hashlib, json, tarfile, tempfile
from pathlib import Path

EXPECTED_SHA={
 "855":"46f08082f3bd58ed67b9a8a16d3fe26c10774d6d7ead246202a10c40e724e9ae",
 "864":"5c7725f878028e620a4edf975fe890b0b2d8fda0071cd286a3c70163ca4d96d6",
}
EXPECTED_BYTES={"855":10012,"864":10652}

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ev(d,k):
 if k not in d:return ("UNKNOWN",None)
 if d[k] is None:return ("KNOWN_NULL",None)
 return ("KNOWN",d[k])
def classify(ctx,current):
 if ctx["client_id"] != current["client_id"]: return "MISMATCH"
 a,b=ev(ctx,"transient_for"),ev(current,"transient_for")
 if "UNKNOWN" in (a[0],b[0]): return "CORE_MATCH_REFINEMENT_UNKNOWN"
 return "EXACT_MATCH" if a[1]==b[1] else "MISMATCH"
def load(arc,cohort):
 if Path(arc).stat().st_size!=EXPECTED_BYTES[cohort] or sha(arc)!=EXPECTED_SHA[cohort]: raise RuntimeError("archive_identity")
 with tempfile.TemporaryDirectory() as td:
  with tarfile.open(arc,"r:xz") as tf: tf.extractall(td)
  ps=sorted((Path(td)/"cases").glob("*/case.json"))
  return [(json.loads(p.read_text()),sha(p)) for p in ps]
def verify(rows_path,focus,modal):
 rows=[json.loads(x) for x in Path(rows_path).read_text().splitlines() if x]
 expected={}
 for cohort,arc in [("855",focus),("864",modal)]:
  for d,csha in load(arc,cohort):
   for form,ctx in [("stale_source",d["source"]),("fresh_current",d["admission"])]:
    expected[(cohort,d["case_id"],form)] = (classify(ctx,d["admission"]),csha,d)
 errors=[]; fabricated=0; coerced=0
 if len(rows)!=32: errors.append("row_count")
 seen=set(); counts={}
 for r in rows:
  key=(r.get("cohort"),r.get("case_id"),r.get("receipt",{}).get("receipt_form"))
  if key in seen: errors.append("duplicate:"+repr(key))
  seen.add(key)
  if key not in expected: errors.append("unexpected:"+repr(key)); continue
  exp,csha,d=expected[key]
  if r.get("classification")!=exp: errors.append("class:"+repr(key))
  if r.get("case_sha256")!=csha: errors.append("case_sha:"+repr(key))
  if r.get("authority")!="none" or r.get("task_input_granted") is not False or r.get("action_admission_eligible") is not False: errors.append("authority:"+repr(key))
  counts[r.get("classification")]=counts.get(r.get("classification"),0)+1
  source = d["source"] if key[2]=="stale_source" else d["admission"]
  for label,obj,raw in [("receipt",r["receipt"]["identity"]["transient_for"],source),("current",r["current_identity"]["transient_for"],d["admission"])]:
   present="transient_for" in raw
   if not present and obj.get("state")!="UNKNOWN":
    coerced += 1
    if obj.get("state")=="KNOWN_NULL": fabricated += 1
   if present and raw["transient_for"] is None and obj.get("state")!="KNOWN_NULL": errors.append("lost_known_null:"+repr((key,label)))
   if present and raw["transient_for"] is not None and (obj.get("state")!="KNOWN" or obj.get("value")!=raw["transient_for"]): errors.append("lost_known_value:"+repr((key,label)))
 gates={
  "rows_32":len(rows)==32,
  "stale_mismatch_16":sum(1 for r in rows if r["receipt"]["receipt_form"]=="stale_source" and r["classification"]=="MISMATCH")==16,
  "fresh_864_exact_8":sum(1 for r in rows if r["cohort"]=="864" and r["receipt"]["receipt_form"]=="fresh_current" and r["classification"]=="EXACT_MATCH")==8,
  "fresh_855_unknown_8":sum(1 for r in rows if r["cohort"]=="855" and r["receipt"]["receipt_form"]=="fresh_current" and r["classification"]=="CORE_MATCH_REFINEMENT_UNKNOWN")==8,
  "fabricated_null_zero":fabricated==0,
  "unknown_coercion_zero":coerced==0,
  "authority_none_32":sum(r.get("authority")=="none" for r in rows)==32,
  "task_input_false_32":sum(r.get("task_input_granted") is False for r in rows)==32,
  "action_admission_false_32":sum(r.get("action_admission_eligible") is False for r in rows)==32,
 }
 if not all(gates.values()): errors.append("gates")
 return {"errors":errors,"gates":gates,"classification_counts":counts,"fabricated_null_count":fabricated,"unknown_to_null_or_value_coercions":coerced,"rows_sha256":sha(rows_path),"audit_pass":not errors}
def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--rows",required=True); ap.add_argument("--focus-archive",required=True); ap.add_argument("--modal-archive",required=True); ap.add_argument("--out",required=True); a=ap.parse_args()
 out=verify(a.rows,a.focus_archive,a.modal_archive); Path(a.out).write_text(json.dumps(out,sort_keys=True,indent=2)+"\n"); print(json.dumps(out,sort_keys=True))
if __name__=="__main__":main()
