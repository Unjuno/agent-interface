#!/usr/bin/env python3
"""Finite paired stage-graph diagnostic; no external I/O."""
import json,sys
from pathlib import Path

def rn(x): return round(float(x),12)

def run_arm(case, arm):
    gains=case["gains"]; n=len(gains)
    if len(case["common_disturbances"])!=n or len(case["injected_pulses"])!=n:
        raise ValueError("stage_vector_length")
    checkpoint_list=case.get(arm+"_checkpoints",[])
    if len(checkpoint_list)!=len(set(checkpoint_list)): raise ValueError("duplicate_checkpoint")
    checkpoints=set(checkpoint_list)
    if any(i<0 or i>=n for i in checkpoints): raise ValueError("checkpoint_index")
    nominal=float(case["initial_nominal"])
    perturbed=nominal+float(case["initial_delta"])
    rows=[]; first_branch=None; first_unsafe=None
    threshold=case["branch_threshold"]
    for i,(gain,common,pulse) in enumerate(zip(gains,case["common_disturbances"],case["injected_pulses"])):
        nominal=float(gain)*nominal+float(common)
        perturbed=float(gain)*perturbed+float(common)+float(pulse)
        delta=perturbed-nominal
        if threshold is not None and (nominal>=threshold)!=(perturbed>=threshold) and first_branch is None:
            first_branch=i
        safe=abs(nominal)<=case["forbidden_abs_max"] and abs(perturbed)<=case["forbidden_abs_max"]
        if not safe and first_unsafe is None: first_unsafe=i
        pre_checkpoint_delta=delta
        checkpoint=i in checkpoints
        if checkpoint: perturbed=nominal
        rows.append({"stage":i,"nominal":rn(nominal),"perturbed_before_checkpoint":rn(perturbed if not checkpoint else nominal+pre_checkpoint_delta),
                     "delta_before_checkpoint":rn(pre_checkpoint_delta),"checkpoint":checkpoint,
                     "delta_after_checkpoint":rn(perturbed-nominal),"safe_prefix":safe,
                     "branch_diverged":first_branch is not None})
    total_injected=abs(float(case["initial_delta"]))+sum(abs(float(x)) for x in case["injected_pulses"])
    comparable=first_branch is None
    final_delta=perturbed-nominal
    metric=None if total_injected==0 or not comparable else abs(final_delta)/total_injected
    ratio=None if metric is None else rn(metric)
    if first_branch is not None: cls="INCOMPARABLE_BRANCHES"
    elif total_injected==0: cls="NOT_COMPUTABLE_ZERO_INJECTION"
    elif case["initial_delta"]==0 and any(case["injected_pulses"]): cls="LATE_INJECTION_NO_UPSTREAM_GAIN" if all(r["delta_before_checkpoint"]==0 for r in rows[:-1]) else "LATE_INJECTION"
    elif metric>1: cls="AMPLIFYING"
    elif metric<1: cls="ATTENUATING"
    else: cls="NEUTRAL"
    first_nonzero=next((r["stage"] for r in rows if r["delta_before_checkpoint"]!=0),None)
    return {"stages":rows,"final_delta":rn(final_delta),"ratio":ratio,"class":cls,"first_nonzero_stage":first_nonzero,
            "first_divergence_stage":first_branch,"first_unsafe_stage":first_unsafe,
            "safety_pass":first_unsafe is None,
            "task_effect_pass":final_delta==0 and first_branch is None and first_unsafe is None}


def evaluate(data):
    result={}
    for case in data["cases"]:
        result[case["id"]]={arm:run_arm(case,arm) for arm in "ABC"}
    return {"case_count":len(result),"cases":result,"disposition":"PASS_METHOD_SCOPED"}


def main():
    data=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    print(json.dumps({"schema":"6053.candidate.v1","summary":evaluate(data)},sort_keys=True))


if __name__=="__main__": main()
