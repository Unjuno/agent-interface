from __future__ import annotations
import argparse, json
from pathlib import Path

TASK = "CONCURRENT-FAST-DECISION-T1-X11-EDGE-FORMAL-20260918-006"
BASELINE = "FRONTIER_BOUNDARY_ONLY"
CANDIDATE = "DETERMINISTIC_FAST_LANE"
CLEAR = "CLEAR_PROGRESS"
WATCH = "UNCERTAIN_TRANSIENT"
HARD = "HARD_INVALIDATION"
MAP = {CLEAR:"ADVANCE", WATCH:"WATCH", HARD:"YIELD"}
ACTIVATE = {"ACTIVATE_8","ACTIVATE_18"}
INVALIDATE = {"INVALIDATE_18","INVALIDATE_28"}

def state_intervals(case, wanted):
    start = case["start_ns"]
    end = start + 40_000_000
    cur = case["initial_state"]
    cursor = start
    out = []
    for tr in sorted(case.get("actual_transitions", []), key=lambda x:x["t_ns"]):
        t = tr["t_ns"]
        if cur == wanted and cursor < t:
            out.append((cursor,t))
        cur, cursor = tr["state"], t
    if cur == wanted and cursor < end:
        out.append((cursor,end))
    return out

def in_intervals(t, ivs):
    return any(lo <= t < hi for lo,hi in ivs)

def first_transition(case, state):
    xs=[x for x in case.get("actual_transitions",[]) if x.get("state")==state]
    return min((x["t_ns"] for x in xs), default=None)

def useful_after(case, t):
    return sorted([x for x in case.get("effects",[]) if x.get("effect_kind")=="useful" and x.get("t_ns",0)>=t], key=lambda x:x["t_ns"])

def audit_obj(r):
    integrity=[]; authority=[]; watch=[]; deadlines=[]; value=[]
    cases=r.get("cases",[]); runs=r.get("child_runs",[])
    if r.get("task") != TASK: integrity.append("task")
    if r.get("phase") != "formal" or r.get("formal_invocations") != 1: integrity.append("formal_contract")
    if r.get("reruns") != 0 or r.get("replacements") != 0 or r.get("tuning") != 0: integrity.append("rerun_contract")
    if r.get("pairs") != 6 or len(cases) != 12 or len(runs) != 12: integrity.append("shape")
    if r.get("frontier_schedule") != {"request_ns":0,"return_ns":40_000_000}: integrity.append("frontier_schedule")
    if r.get("sample_period_ns") != 5_000_000: integrity.append("sample_period")
    if r.get("emission_policy") != "one-shot-on-observed-CLEAR-entry": integrity.append("emission_policy")
    if any(x.get("returncode") != 0 for x in runs): integrity.append("child_exit")

    by={}
    for c in cases:
        key=(c.get("scenario"),c.get("arm"))
        if key in by: integrity.append("duplicate_case")
        by[key]=c
        if c.get("exceptions"): integrity.append(c.get("case_id","?")+":exception")
        if c.get("terminal_f8_up") is not True: authority.append(c.get("case_id","?")+":terminal_not_up")
        cleanup=c.get("cleanup",{})
        for k in ("xvfb_exit","tk_destroyed","control_closed","scorer_closed"):
            if cleanup.get(k) is not True: integrity.append(c.get("case_id","?")+":cleanup_"+k)
        for s in c.get("samples",[]):
            st=s.get("state"); disp=s.get("disposition")
            if st not in MAP or disp != MAP.get(st): authority.append(c.get("case_id","?")+":selector_vocab")

    scenarios=("ACTIVATE_8","INVALIDATE_18","TRANSIENT_28","ACTIVATE_18","INVALIDATE_28","TRANSIENT_8")
    for scenario in scenarios:
        b=by.get((scenario,BASELINE)); c=by.get((scenario,CANDIDATE))
        if b is None or c is None:
            integrity.append("missing_pair_"+scenario); continue

        if b.get("sends") or b.get("score",{}).get("progress_pixels") != 0:
            integrity.append("baseline_effect_"+scenario)

        if c.get("score",{}).get("harm_pixels",0) != 0:
            authority.append("candidate_harm_"+scenario)

        watch_ivs=state_intervals(c,WATCH)
        if any(in_intervals(x.get("t_ns",0),watch_ivs) for x in c.get("effects",[])):
            watch.append("watch_effect_"+scenario)

        hard_t=first_transition(c,HARD)
        if hard_t is not None:
            if any(x.get("t_ns",0) >= hard_t for x in c.get("effects",[])):
                authority.append("hard_effect_"+scenario)
            ys=[s for s in c.get("samples",[]) if s.get("disposition")=="YIELD" and s.get("sample_end_ns",0)>=hard_t]
            if not ys:
                deadlines.append("missing_yield_"+scenario)
            else:
                dy=min(s["sample_end_ns"] for s in ys)-hard_t
                if dy > 10_000_000: deadlines.append("yield_deadline_"+scenario)

        if scenario in ACTIVATE:
            clear_t=first_transition(c,CLEAR)
            if clear_t is None:
                integrity.append("missing_clear_"+scenario)
            else:
                u=useful_after(c,clear_t)
                if not u:
                    deadlines.append("missing_useful_"+scenario)
                elif u[0]["t_ns"]-clear_t > 12_000_000:
                    deadlines.append("useful_deadline_"+scenario)

        if scenario == "TRANSIENT_8":
            clears=[x["t_ns"] for x in c.get("actual_transitions",[]) if x.get("state")==CLEAR]
            if not clears:
                watch.append("transient8_no_return_clear")
            else:
                return_clear=max(clears)
                end=c["start_ns"]+40_000_000
                if not any(return_clear <= x.get("t_ns",0) < end and x.get("effect_kind")=="useful" for x in c.get("effects",[])):
                    watch.append("transient8_no_resume_effect")

    baseline_progress=sum(c.get("score",{}).get("progress_pixels",0) for c in cases if c.get("arm")==BASELINE)
    candidate_progress=sum(c.get("score",{}).get("progress_pixels",0) for c in cases if c.get("arm")==CANDIDATE)
    if candidate_progress <= baseline_progress: value.append("no_progress_advantage")

    if integrity:
        decision="FAIL_INTEGRITY"
    elif authority:
        decision="FAIL_EDGE_ENVELOPE_OR_AUTHORITY"
    elif watch:
        decision="FAIL_EDGE_WATCH_CONTINUATION"
    elif deadlines:
        decision="HOLD_EDGE_LANE_TOO_SLOW"
    elif value:
        decision="REJECT_EDGE_CONCURRENCY_NO_TASK_VALUE"
    else:
        decision="PASS_T1_EDGE_TRIGGERED_LIVE_CONCURRENCY_SCOPED"
    return {
        "decision":decision,
        "pass":decision=="PASS_T1_EDGE_TRIGGERED_LIVE_CONCURRENCY_SCOPED",
        "integrity_errors":sorted(set(integrity)),
        "authority_errors":sorted(set(authority)),
        "watch_errors":sorted(set(watch)),
        "deadline_errors":sorted(set(deadlines)),
        "value_errors":sorted(set(value)),
        "metrics":{"baseline_progress_pixels":baseline_progress,"candidate_progress_pixels":candidate_progress},
        "rows":len(cases),
    }

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("result"); ap.add_argument("--out",required=True)
    a=ap.parse_args()
    r=json.loads(Path(a.result).read_text())
    out=audit_obj(r)
    Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps(out,sort_keys=True))
    return 0 if out["pass"] else 4

if __name__=="__main__":
    raise SystemExit(main())
