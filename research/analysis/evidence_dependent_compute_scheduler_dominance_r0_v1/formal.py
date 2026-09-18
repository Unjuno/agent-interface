from fractions import Fraction as F
import json, pathlib

T = (F(0), F(1,2), F(1), F(3,2), F(2))
C = (F(0), F(1,4), F(1,2), F(1), F(3,2), F(2))
D = (F(0), F(1,2), F(1), F(3,2), F(2), F(5,2), F(3), F(4))
NO_RESULT_PENALTY = F(10)
WAIT_DELAY = F(1,2)
INVALIDATE_AT = F(1,4)
WITNESS = {"t": F(0), "c": F(1), "d": F(2), "current": True}

def s(x):
    return str(x.numerator) if x.denominator == 1 else f"{x.numerator}/{x.denominator}"

def candidate_feasible(current, t, c, d):
    return bool(current and t + c <= d)

def direct_feasible(current, t, c, d):
    if not current:
        return False
    completion = t + c
    return completion <= d

def run_world(invalidate_at=None):
    t=WITNESS["t"]; c=WITNESS["c"]; d=WITNESS["d"]
    if invalidate_at is not None and t < invalidate_at < t+c:
        wasted = invalidate_at - t
        return {"useful": False, "completion": None, "wasted": wasted,
                "cost": NO_RESULT_PENALTY + wasted}
    completion=t+c
    useful=completion<=d
    return {"useful": useful, "completion": completion if useful else None,
            "wasted": F(0), "cost": (completion-t if useful else NO_RESULT_PENALTY)}

def wait_world(invalidate_at=None):
    t=WITNESS["t"]; c=WITNESS["c"]; d=WITNESS["d"]
    start=t+WAIT_DELAY
    if invalidate_at is not None and invalidate_at <= start:
        return {"useful": False, "completion": None, "wasted": F(0),
                "cost": NO_RESULT_PENALTY}
    if start+c>d:
        return {"useful": False, "completion": None, "wasted": F(0),
                "cost": NO_RESULT_PENALTY}
    completion=start+c
    return {"useful": True, "completion": completion, "wasted": F(0),
            "cost": completion-t}

def encode_world(row):
    return {k:(s(v) if isinstance(v,F) else v) for k,v in row.items()}

rows=[]; mismatches=0; stale_accepted=0; tardy_accepted=0; tie_current=0; tie_feasible=0
reuse_decisions=0
for current in (True,False):
    for t in T:
        for c in C:
            for d in D:
                cand=candidate_feasible(current,t,c,d)
                direct=direct_feasible(current,t,c,d)
                mismatches += cand != direct
                stale_accepted += (not current and cand)
                tardy_accepted += (current and t+c>d and cand)
                if current and t+c==d:
                    tie_current += 1
                    tie_feasible += cand
                rows.append({"current":current,"t":s(t),"c":s(c),"d":s(d),
                             "candidate_feasible":cand,"direct_feasible":direct})

stable_run=run_world(); stable_wait=wait_world()
invalid_run=run_world(INVALIDATE_AT); invalid_wait=wait_world(INVALIDATE_AT)
paired={
    "metadata": {k:(s(v) if isinstance(v,F) else v) for k,v in WITNESS.items()},
    "wait_delay": s(WAIT_DELAY), "invalidate_at": s(INVALIDATE_AT),
    "stable": {"run":encode_world(stable_run),"wait":encode_world(stable_wait),
               "preference":"RUN" if stable_run["cost"]<stable_wait["cost"] else "WAIT"},
    "invalidate_soon": {"run":encode_world(invalid_run),"wait":encode_world(invalid_wait),
               "preference":"RUN" if invalid_run["cost"]<invalid_wait["cost"] else "WAIT"},
}
summary={
  "schema":"evidence_compute_scheduler_dominance_result_v1",
  "formal_invocations":1,"reruns":0,"replacements":0,"tuning":0,
  "rows":len(rows),"mismatches":mismatches,"stale_run_accepted":stale_accepted,
  "tardy_run_accepted":tardy_accepted,"exact_tie_current_rows":tie_current,
  "exact_tie_feasible_rows":tie_feasible,"reuse_decisions":reuse_decisions,
  "paired_futures":paired,
  "universal_hard_metadata_choice_rejected": paired["stable"]["preference"]=="RUN" and paired["invalidate_soon"]["preference"]=="WAIT",
}
summary["decision"] = "PASS_COMPUTE_SCHEDULER_HARD_DOMINANCE_SCOPED" if (
    mismatches==0 and stale_accepted==0 and tardy_accepted==0 and tie_current>0 and
    tie_feasible==tie_current and summary["universal_hard_metadata_choice_rejected"] and
    reuse_decisions==0) else "FAIL_PRIMARY"
out={"summary":summary,"rows":rows}
pathlib.Path(__file__).with_name("RESULT.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
print(json.dumps(summary,sort_keys=True))
