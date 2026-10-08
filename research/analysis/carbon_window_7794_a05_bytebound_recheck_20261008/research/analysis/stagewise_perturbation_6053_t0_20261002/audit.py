#!/usr/bin/env python3
"""Independent exact-rational stage replay; does not import candidate.py."""
import json,sys
from fractions import Fraction as Q
from pathlib import Path


def q(v): return Q(str(v))
def rn(v): return round(float(v),12)


def replay(c,arm):
    g=c["gains"]; n=len(g)
    if len(c["common_disturbances"])!=n or len(c["injected_pulses"])!=n: raise ValueError("misaligned-stage-data")
    marks=c.get(arm+"_checkpoints",[])
    if len(set(marks))!=len(marks) or any(j not in range(n) for j in marks): raise ValueError("invalid-checkpoint")
    x=q(c["initial_nominal"]); y=x+q(c["initial_delta"]); boundary=None; breach=None; rows=[]
    for j in range(n):
        x=q(g[j])*x+q(c["common_disturbances"][j])
        y=q(g[j])*y+q(c["common_disturbances"][j])+q(c["injected_pulses"][j])
        gap=y-x; threshold=c["branch_threshold"]
        if threshold is not None and (x>=q(threshold))!=(y>=q(threshold)) and boundary is None: boundary=j
        safe=abs(x)<=q(c["forbidden_abs_max"]) and abs(y)<=q(c["forbidden_abs_max"])
        if not safe and breach is None: breach=j
        before=y
        reset=j in marks
        if reset: y=x
        rows.append({"stage":j,"nominal":rn(x),"perturbed_before_checkpoint":rn(before),
                     "delta_before_checkpoint":rn(gap),"checkpoint":reset,
                     "delta_after_checkpoint":rn(y-x),"safe_prefix":safe,
                     "branch_diverged":boundary is not None})
    injected=abs(q(c["initial_delta"]))+sum((abs(q(t)) for t in c["injected_pulses"]),Q(0))
    final=y-x
    if boundary is not None: cls="INCOMPARABLE_BRANCHES"
    elif injected==0: cls="NOT_COMPUTABLE_ZERO_INJECTION"
    elif q(c["initial_delta"])==0 and any(q(t)!=0 for t in c["injected_pulses"]): cls="LATE_INJECTION_NO_UPSTREAM_GAIN" if all(q(r["delta_before_checkpoint"])==0 for r in rows[:-1]) else "LATE_INJECTION"
    elif abs(final)/injected>1: cls="AMPLIFYING"
    elif abs(final)/injected<1: cls="ATTENUATING"
    else: cls="NEUTRAL"
    first_nonzero=next((r["stage"] for r in rows if q(r["delta_before_checkpoint"])!=0),None)
    return {"stages":rows,"final_delta":rn(final),"ratio":None if injected==0 or boundary is not None else rn(abs(final)/injected),
            "first_nonzero_stage":first_nonzero,
            "class":cls,"first_divergence_stage":boundary,"first_unsafe_stage":breach,"safety_pass":breach is None,
            "task_effect_pass":final==0 and boundary is None and breach is None}


def main():
    data=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    output={c["id"]:{arm:replay(c,arm) for arm in "ABC"} for c in data["cases"]}
    print(json.dumps({"schema":"6053.independent-audit.v1","summary":{"case_count":len(output),"cases":output,"disposition":"PASS_METHOD_SCOPED"}},sort_keys=True))


if __name__=="__main__": main()
