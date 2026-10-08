import argparse,json
from pathlib import Path
EXPECTED={"inkscape":{"stable":"MATCH","pointer_displaced":"MISMATCH","observer_unavailable":"UNKNOWN"},"calc":{"stable":"MATCH","focus_transferred":"MISMATCH","observer_unavailable":"UNKNOWN"}}
def evaluate(rows):
 errors=[]; naive_false=0; naive_unsupported=0; cand={}; ids=set()
 for r in rows:
  cid=r.get("case_id")
  if cid in ids: errors.append(f"duplicate:{cid}")
  ids.add(cid)
  if r.get("status")!="ok": errors.append(f"status:{cid}"); continue
  exp=EXPECTED[r["app"]][r["scenario"]]
  if r.get("candidate_class")!=exp: errors.append(f"candidate:{cid}:{r.get('candidate_class')}!={exp}")
  cand[exp]=cand.get(exp,0)+1
  if not r.get("held_observed_during"): errors.append(f"no_hold:{cid}")
  if not r.get("release_observed_before_perturbation") or not r.get("cleanup_neutral"): errors.append(f"release:{cid}")
  if r["scenario"] in ("pointer_displaced","focus_transferred"):
   if r.get("actual_match"): errors.append(f"perturb_not_exposed:{cid}")
   if r.get("naive_command_only_class")=="MATCH": naive_false+=1
  if r["scenario"]=="observer_unavailable" and r.get("naive_command_only_class")=="MATCH": naive_unsupported+=1
  if r["scenario"]=="stable" and not r.get("actual_match"): errors.append(f"stable_mismatch:{cid}")
 if len(rows)!=18: errors.append(f"rows:{len(rows)}")
 if len(ids)!=18: errors.append(f"unique_ids:{len(ids)}")
 if naive_false!=6: errors.append(f"naive_false:{naive_false}")
 if naive_unsupported!=6: errors.append(f"naive_unsupported:{naive_unsupported}")
 if cand.get("MATCH")!=6 or cand.get("MISMATCH")!=6 or cand.get("UNKNOWN")!=6: errors.append(f"candidate_counts:{cand}")
 return {"rows":len(rows),"candidate_counts":cand,"naive_false_confirmations":naive_false,"naive_unsupported_confirmations":naive_unsupported,"errors":errors,"decision":"PASS_MOTOR_STATE_DISTINCTION_SCOPED" if not errors else "FAIL_OR_HOLD"}
def main():
 ap=argparse.ArgumentParser(); ap.add_argument("dirs",nargs="+"); a=ap.parse_args(); rows=[]
 for d in a.dirs: rows += json.loads((Path(d)/"RAW.json").read_text())["rows"]
 result=evaluate(rows); print(json.dumps(result,sort_keys=True)); return 0 if not result["errors"] else 2
if __name__=="__main__": raise SystemExit(main())
