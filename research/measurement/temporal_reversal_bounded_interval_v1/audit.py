from __future__ import annotations
import argparse, hashlib, json
from collections import defaultdict
from common import FORMAL_AGES_MS, IDENT_CEILING, POSITION_JITTER_BOUND, DISP_ERROR_BOUND, UNKNOWN, position_exact_u, jitter_u


def audit(path: str, formal: bool=True):
    with open(path,"r",encoding="utf-8") as f: p=json.load(f)
    errors=[]
    rows=p.get("rows",[])
    expected=2400 if formal else 48
    if len(rows)!=expected or p.get("row_count")!=expected: errors.append("row_count")
    if formal and p.get("formal_invocation")!=1: errors.append("invocation")
    if p.get("reruns")!=0: errors.append("reruns")
    seen=set(); agg=defaultdict(lambda:[0,0,0,0])
    for r in rows:
        key=(r.get("trajectory_id"),r.get("estimator"))
        if key in seen: errors.append("duplicate")
        seen.add(key)
        age=r["age_ms"]; post=r["post_dir"]; ts=r["sample_times_us"]
        if r.get("position_jitter_bound_u") != POSITION_JITTER_BOUND: errors.append("error_bound")
        if r.get("displacement_error_bound_u") != DISP_ERROR_BOUND: errors.append("disp_bound")
        exact=[position_exact_u(t,age,post) for t in ts]
        if exact != r["exact_positions_u"]: errors.append("exact_position")
        # Independently recompute deterministic perturbations and observed values.
        jj=[jitter_u(r["trajectory_id"],t) for t in ts]
        if jj != r["jitter_u"]: errors.append("jitter")
        obs=[x+j for x,j in zip(exact,jj)]
        if obs != r["observed_positions_u"]: errors.append("observed")
        if obs[0]-obs[1] != r["d_new_u"] or obs[1]-obs[2] != r["d_prev_u"]: errors.append("displacement")
        if r["oracle"] != post: errors.append("oracle")
        pred=r["prediction"]
        if bool(pred==post)!=bool(r["correct"]): errors.append("correct_flag")
        if bool(pred==UNKNOWN)!=bool(r["unknown"]): errors.append("unknown_flag")
        if bool(pred not in (UNKNOWN,post))!=bool(r["wrong_direction"]): errors.append("wrong_flag")
        a=agg[(r["estimator"],age)]; a[0]+=1; a[1]+=int(r["correct"]); a[2]+=int(r["unknown"]); a[3]+=int(r["wrong_direction"])
    metrics={}
    for (est,age),(n,c,u,w) in agg.items():
        metrics.setdefault(est,{})[age]={"n":n,"accuracy":c/n,"unknown_rate":u/n,"wrong_direction_rate":w/n}
    decision=None
    if formal and not errors:
        b=metrics.get("STRICT_EXACT",{}); c=metrics.get("BOUNDED_INTERVAL",{})
        safety=False
        for age in FORMAL_AGES_MS:
            if age not in b or age not in c: errors.append("missing_cell"); continue
            if c[age]["accuracy"] + 1e-12 < b[age]["accuracy"]: errors.append(f"candidate_below_baseline_{age}")
            if c[age]["wrong_direction_rate"] != 0: safety=True
            if c[age]["accuracy"] > IDENT_CEILING[age] + 1e-12: safety=True
        if safety:
            decision="FAIL_BOUNDED_INTERVAL_SAFETY"
        else:
            recovery_ok=(c[100]["accuracy"]>=0.90 and c[150]["accuracy"]>=0.95 and c[200]["accuracy"]>=0.95)
            for age in (50,75,100,150,200):
                if c[age]["accuracy"] + 1e-12 < 0.90*IDENT_CEILING[age]: recovery_ok=False
            improve=max(c[a]["accuracy"]-b[a]["accuracy"] for a in (100,150,200))
            if improve < 0.80: recovery_ok=False
            decision="PASS_BOUNDED_INTERVAL_JITTER_RECOVERY_SCOPED" if recovery_ok else "HOLD_BOUNDED_INTERVAL_INSUFFICIENT"
    if errors:
        decision="FAIL_INTEGRITY"
    return {"pass": decision=="PASS_BOUNDED_INTERVAL_JITTER_RECOVERY_SCOPED", "decision":decision, "errors":sorted(set(errors)), "metrics":metrics, "row_count":len(rows)}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("path"); ap.add_argument("--construction",action="store_true"); ap.add_argument("--out")
    a=ap.parse_args(); r=audit(a.path,not a.construction)
    s=json.dumps(r,separators=(",",":"),sort_keys=True)
    if a.out:
        open(a.out,"w",encoding="utf-8").write(s)
    print(s)
if __name__=="__main__": main()
