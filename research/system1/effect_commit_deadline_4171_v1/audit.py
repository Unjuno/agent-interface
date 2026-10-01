#!/usr/bin/env python3
import argparse, json, pathlib
POLICIES=("PRE_DISPATCH_ONLY","POSTHOC_EFFECT_CHECK","APP_COMMIT_DEADLINE")
SCHEDULES=("EARLY_SHORT","NEAR_SHORT","EARLY_LONG","NEAR_LONG")
LONG={"EARLY_LONG","NEAR_LONG"}

def audit(root,reps):
    rows=json.loads((pathlib.Path(root)/"ROWS.json").read_text()); errors=[]
    expected=reps*len(POLICIES)*len(SCHEDULES)
    if len(rows)!=expected: errors.append(f"row_count:{len(rows)}!={expected}")
    ids=set()
    for r in rows:
      cid=r["case_id"]
      if cid in ids: errors.append("duplicate:"+cid)
      ids.add(cid)
      if type(r["rep"]) is not int: errors.append("rep_type:"+cid)
      if r["authority"] is not False: errors.append("authority:"+cid)
      if r["app_exit"]!=0: errors.append("app_exit:"+cid)
      if not r["dispatch_valid"]: errors.append("dispatch_invalid:"+cid)
      if r["proposal_ready_elapsed_ms"]>120 or r["predispatch_elapsed_ms"]>120: errors.append("pre_dispatch_late:"+cid)
      if r["predispatch_elapsed_ms"]>400: errors.append("freshness:"+cid)
      rec=r["receipt"]
      if not isinstance(rec,dict): errors.append("receipt_missing:"+cid); continue
      long=r["schedule"] in LONG
      if r["policy"] in ("PRE_DISPATCH_ONLY","POSTHOC_EFFECT_CHECK"):
        if not rec.get("effect_committed"): errors.append("baseline_noeffect:"+cid)
        if long and rec.get("within_deadline") is not False: errors.append("baseline_long_not_late:"+cid)
        if not long and rec.get("within_deadline") is not True: errors.append("baseline_short_not_ontime:"+cid)
        if r["policy"]=="POSTHOC_EFFECT_CHECK":
          want="LATE" if long else "ON_TIME"
          if r.get("posthoc")!=want: errors.append("posthoc:"+cid)
      else:
        if long:
          if rec.get("effect_committed") or rec.get("effect_ns") is not None or rec.get("type")!="REFUSED_DEADLINE": errors.append("candidate_late_effect:"+cid)
        else:
          if not rec.get("effect_committed") or rec.get("within_deadline") is not True: errors.append("candidate_short_refuse:"+cid)
    decision="PASS_EFFECT_COMMIT_DEADLINE_SCOPED" if not errors else "FAIL_OR_HOLD"
    return {"decision":decision,"rows":len(rows),"errors":errors}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("root"); ap.add_argument("--reps",type=int,required=True); ap.add_argument("--out"); a=ap.parse_args()
    result=audit(a.root,a.reps); s=json.dumps(result,indent=2,sort_keys=True)+"\n"
    if a.out: pathlib.Path(a.out).write_text(s)
    print(s,end=""); raise SystemExit(0 if not result["errors"] else 1)
if __name__=='__main__': main()
