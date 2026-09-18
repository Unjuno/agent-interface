from __future__ import annotations
import argparse, json, math, random, time
from pathlib import Path
from candidate import select_disposition, ALLOWED
from oracle import expected_disposition

TASK="CONCURRENT-FAST-DECISION-T0-SHADOW-20260918-001"
SEED=137820260918001
N=120_000
FRONTIER_RETURN_NS=40_000_000
DEADLINE_DELTA_NS=12_000_000
SAMPLE_PERIOD_NS=5_000_000
STATES=("CLEAR_PROGRESS","UNCERTAIN_TRANSIENT","HARD_INVALIDATION")
OFFSETS_NS=tuple(int(x*1_000_000) for x in (2.5,7.5,12.5,17.5,22.5,27.5,32.5))
ARMS=("FRONTIER_BOUNDARY_ONLY","DETERMINISTIC_FAST_LANE")

def pct(values, q):
    xs=sorted(values)
    if not xs: return None
    k=(len(xs)-1)*q
    lo=math.floor(k); hi=math.ceil(k)
    if lo==hi: return xs[lo]
    return xs[lo]*(hi-k)+xs[hi]*(k-lo)

def first_sample_at_or_after(t_ns:int)->int:
    return ((t_ns + SAMPLE_PERIOD_NS - 1)//SAMPLE_PERIOD_NS)*SAMPLE_PERIOD_NS

def make_cases():
    rng=random.Random(SEED)
    base=[]
    per_state=N//len(STATES)
    cid=0
    for state in STATES:
        for _ in range(per_state):
            offset=rng.choice(OFFSETS_NS)
            base.append((cid,state,offset)); cid+=1
    rng.shuffle(base)
    return base

def run(out_path:Path, construction=False):
    if out_path.exists(): raise SystemExit("result exists")
    if construction:
        cases=[
          (0,"CLEAR_PROGRESS",2_500_000),
          (1,"UNCERTAIN_TRANSIENT",17_500_000),
          (2,"HARD_INVALIDATION",27_500_000),
          (3,"HARD_INVALIDATION",32_500_000),
        ]
    else:
        cases=make_cases()
    rows=[]
    compute_ns=[]; cycles_ns=[]
    misses={a:0 for a in ARMS}; correct={a:0 for a in ARMS}
    false_advance_hard=0
    local_available_num=0; local_available_den=0
    schedule_mismatch=0
    envelope_violations=0
    for cid,state,change_ns in cases:
        expected=expected_disposition(state)
        deadline_ns=change_ns+DEADLINE_DELTA_NS
        frontier_decision_ns=FRONTIER_RETURN_NS
        frontier_miss=frontier_decision_ns>deadline_ns
        misses[ARMS[0]]+=int(frontier_miss)
        correct[ARMS[0]]+=1
        sample_ns=first_sample_at_or_after(change_ns)
        t0=time.perf_counter_ns(); got=select_disposition(state); t1=time.perf_counter_ns()
        c_ns=t1-t0
        cycle_ns=(sample_ns-change_ns)+c_ns
        compute_ns.append(c_ns); cycles_ns.append(cycle_ns)
        deterministic_miss=(change_ns+cycle_ns)>deadline_ns
        misses[ARMS[1]]+=int(deterministic_miss)
        is_correct=got==expected
        correct[ARMS[1]]+=int(is_correct)
        if got not in ALLOWED: envelope_violations+=1
        if state=="HARD_INVALIDATION" and got=="ADVANCE": false_advance_hard+=1
        if frontier_decision_ns!=FRONTIER_RETURN_NS: schedule_mismatch+=1
        local_decision_ns=change_ns+cycle_ns
        local_available_num += max(0, FRONTIER_RETURN_NS-local_decision_ns)
        local_available_den += max(0, FRONTIER_RETURN_NS-change_ns)
        if construction:
            rows.append({
              "case_id":cid,"state":state,"change_ns":change_ns,"deadline_ns":deadline_ns,
              "frontier_return_ns":FRONTIER_RETURN_NS,"expected":expected,"deterministic":got,
              "sample_wait_ns":sample_ns-change_ns,"compute_ns":c_ns,"cycle_ns":cycle_ns,
              "frontier_miss":frontier_miss,"deterministic_miss":deterministic_miss,
            })
    n=len(cases)
    front_rate=misses[ARMS[0]]/n
    det_rate=misses[ARMS[1]]/n
    coverage=local_available_num/local_available_den if local_available_den else 0.0
    summary={
      "cases":n,
      "frontier_schedule":{"request_ns":0,"return_ns":FRONTIER_RETURN_NS},
      "frontier_deadline_misses":misses[ARMS[0]],
      "deterministic_deadline_misses":misses[ARMS[1]],
      "frontier_deadline_miss_rate":front_rate,
      "deterministic_deadline_miss_rate":det_rate,
      "deadline_miss_improvement_pp":100*(front_rate-det_rate),
      "frontier_correct_disposition_rate":correct[ARMS[0]]/n,
      "deterministic_correct_disposition_rate":correct[ARMS[1]]/n,
      "false_advance_hard":false_advance_hard,
      "envelope_violations":envelope_violations,
      "schedule_mismatches":schedule_mismatch,
      "decision_compute_ns":{"p50":pct(compute_ns,.5),"p95":pct(compute_ns,.95),"p99":pct(compute_ns,.99),"max":max(compute_ns)},
      "whole_local_cycle_ns":{"p50":pct(cycles_ns,.5),"p95":pct(cycles_ns,.95),"p99":pct(cycles_ns,.99),"max":max(cycles_ns)},
      "correct_local_disposition_frontier_open_coverage":coverage,
    }
    pass_gate=(
      schedule_mismatch==0 and envelope_violations==0 and false_advance_hard==0 and
      correct[ARMS[1]]==n and 100*(front_rate-det_rate)>=50 and
      summary["whole_local_cycle_ns"]["p99"]<=12_000_000 and coverage>0.5
    )
    if front_rate<=0.05:
        decision="HOLD_NO_REALTIME_GAP"
    elif pass_gate:
        decision="PASS_T0_DETERMINISTIC_CONCURRENCY_SHADOW_SCOPED"
    elif correct[ARMS[1]]==n and false_advance_hard==0 and envelope_violations==0:
        decision="HOLD_FAST_LANE_TOO_SLOW"
    else:
        decision="FAIL_ENVELOPE_OR_AUTHORITY"
    result={
      "task":TASK,"phase":"construction" if construction else "formal",
      "formal_invocations":0 if construction else 1,"reruns":0,"seed":None if construction else SEED,
      "n":n,"summary":summary,"decision":decision,
      "parent_disposition_if_no_residual":"HOLD_DETERMINISTIC_LANE_SUFFICIENT" if decision.startswith("PASS_") else None,
      "rows":rows if construction else [],
    }
    out_path.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"decision":decision,**summary},sort_keys=True))

if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--out",required=True); ap.add_argument("--construction",action="store_true")
    a=ap.parse_args(); run(Path(a.out),a.construction)
