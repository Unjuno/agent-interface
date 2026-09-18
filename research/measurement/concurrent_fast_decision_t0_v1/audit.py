from __future__ import annotations
import argparse,json,math,random
from pathlib import Path
from oracle import expected_disposition
from candidate import select_disposition,ALLOWED
from runner import SEED,N,FRONTIER_RETURN_NS,DEADLINE_DELTA_NS,SAMPLE_PERIOD_NS,STATES,OFFSETS_NS,first_sample_at_or_after

def pct(values,q):
    xs=sorted(values); k=(len(xs)-1)*q; lo=math.floor(k); hi=math.ceil(k)
    return xs[lo] if lo==hi else xs[lo]*(hi-k)+xs[hi]*(k-lo)

def make_cases():
    rng=random.Random(SEED); base=[]; per=N//len(STATES); cid=0
    for state in STATES:
        for _ in range(per): base.append((cid,state,rng.choice(OFFSETS_NS))); cid+=1
    rng.shuffle(base); return base

def main():
    ap=argparse.ArgumentParser();ap.add_argument("result");ap.add_argument("--out",required=True);a=ap.parse_args()
    got=json.loads(Path(a.result).read_text()); errors=[]
    if got.get("formal_invocations")!=1 or got.get("reruns")!=0 or got.get("n")!=N: errors.append("invocation_or_count")
    s=got.get("summary",{})
    front_miss=0; det_miss=0; det_correct=0; hard_false=0; env=0; num=0; den=0
    # Auditor intentionally recomputes semantic/timing structure but does not reproduce measured CPU nanoseconds.
    for _,state,change in make_cases():
        exp=expected_disposition(state); out=select_disposition(state)
        if out not in ALLOWED: env+=1
        if out==exp: det_correct+=1
        if state=="HARD_INVALIDATION" and out=="ADVANCE": hard_false+=1
        deadline=change+DEADLINE_DELTA_NS
        front_miss += int(FRONTIER_RETURN_NS>deadline)
        sample=first_sample_at_or_after(change)
        # Measured compute is nonnegative; lower-bound semantic miss uses sample time only.
        det_miss += int(sample>deadline)
        num += max(0,FRONTIER_RETURN_NS-sample)
        den += max(0,FRONTIER_RETURN_NS-change)
    if s.get("frontier_deadline_misses")!=front_miss: errors.append("frontier_miss_recompute")
    if s.get("deterministic_deadline_misses",0)<det_miss: errors.append("deterministic_miss_underflow")
    if s.get("deterministic_correct_disposition_rate")!=1.0 or det_correct!=N: errors.append("correctness")
    if s.get("false_advance_hard")!=0 or hard_false!=0: errors.append("hard_false_advance")
    if s.get("envelope_violations")!=0 or env!=0: errors.append("envelope")
    expected_front_rate=front_miss/N
    if abs(s.get("frontier_deadline_miss_rate",-1)-expected_front_rate)>1e-12: errors.append("frontier_rate")
    expected_coverage=num/den
    # measured compute can only reduce coverage from sample-only upper bound
    if not (0.5 < s.get("correct_local_disposition_frontier_open_coverage",0) <= expected_coverage+1e-12): errors.append("coverage")
    if s.get("whole_local_cycle_ns",{}).get("p99",10**30)>12_000_000: errors.append("cycle_p99")
    if s.get("deadline_miss_improvement_pp",0)<50: errors.append("improvement")
    if got.get("decision")!="PASS_T0_DETERMINISTIC_CONCURRENCY_SHADOW_SCOPED": errors.append("decision")
    # Corruption controls: unknown state and hard->ADVANCE mutation must not pass candidate/oracle contract.
    corruption={}
    try: select_disposition("UNKNOWN_STATE"); corruption["unknown_state_rejected"]=False
    except ValueError: corruption["unknown_state_rejected"]=True
    corruption["hard_advance_rejected"]=(expected_disposition("HARD_INVALIDATION")!="ADVANCE")
    if not all(corruption.values()): errors.append("corruption")
    out={"pass":not errors,"errors":errors,"decision":got.get("decision"),"corruption_controls":corruption,
         "recomputed":{"frontier_misses":front_miss,"sample_only_deterministic_misses":det_miss,"sample_only_coverage_upper":expected_coverage}}
    Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps(out,sort_keys=True))
if __name__=="__main__":main()
