#!/usr/bin/env python3
import argparse, json, pathlib
SCHEDULES={"EARLY_SHORT":(20,20),"NEAR_SHORT":(90,10),"NEAR_LONG":(90,60),"EARLY_LONG":(20,140)}
POLICIES=("PROPOSAL_READY_DEADLINE","PRE_DISPATCH_DEADLINE")
LATE={"NEAR_LONG","EARLY_LONG"}

def audit(root, expected_reps):
    root=pathlib.Path(root); rows=json.loads((root/"ROWS.json").read_text()); errors=[]
    expected=expected_reps*len(SCHEDULES)*len(POLICIES)
    if len(rows)!=expected: errors.append(f"row_count:{len(rows)}!={expected}")
    ids=set()
    for r in rows:
        if r["case_id"] in ids: errors.append("duplicate:"+r["case_id"])
        ids.add(r["case_id"])
        if type(r["rep"]) is not int: errors.append("rep_type:"+r["case_id"])
        if r["authority"] is not False: errors.append("authority:"+r["case_id"])
        if r["app_exit"]!=0: errors.append("exit:"+r["case_id"])
        if r["proposal_ready_elapsed_ms"]>120: errors.append("proposal_late:"+r["case_id"])
        if r["proposal_ready_elapsed_ms"]>400 or r["predispatch_elapsed_ms"]>400: errors.append("freshness:"+r["case_id"])
        late=r["schedule"] in LATE
        if r["policy"]=="PROPOSAL_READY_DEADLINE":
            if not r["admitted"]: errors.append("baseline_refused:"+r["case_id"])
            if r["app_effect"] is None: errors.append("baseline_noeffect:"+r["case_id"])
            elif bool(r["app_effect"]["within_deadline"]) == late: errors.append("baseline_deadline_effect:"+r["case_id"])
        else:
            if late:
                if r["admitted"] or r["app_effect"] is not None: errors.append("candidate_late_admit:"+r["case_id"])
            else:
                if not r["admitted"] or r["app_effect"] is None: errors.append("candidate_on_time_refuse:"+r["case_id"])
                elif not r["app_effect"]["within_deadline"]: errors.append("candidate_on_time_effect_late:"+r["case_id"])
    return {"decision":"PASS_DISPATCH_DEADLINE_VALIDITY_SCOPED" if not errors else "FAIL_OR_HOLD","rows":len(rows),"errors":errors}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("root"); ap.add_argument("--reps",type=int,required=True); ap.add_argument("--out"); a=ap.parse_args()
    result=audit(a.root,a.reps)
    text=json.dumps(result,indent=2,sort_keys=True)+"\n"
    if a.out: pathlib.Path(a.out).write_text(text)
    print(text,end="")
    raise SystemExit(0 if not result["errors"] else 1)
if __name__=='__main__': main()
