from __future__ import annotations
import argparse
import copy
import json
from pathlib import Path

TASK = "CONCURRENT-FAST-DECISION-T1-X11-20260918-001"
CLEAR="CLEAR_PROGRESS"; WATCH="UNCERTAIN_TRANSIENT"; HARD="HARD_INVALIDATION"
ALLOWED={"ADVANCE","WATCH","YIELD"}
EXPECTED={CLEAR:"ADVANCE",WATCH:"WATCH",HARD:"YIELD"}
FORMAL_SCENARIOS={"ACTIVATE_8","INVALIDATE_18","TRANSIENT_28","ACTIVATE_18","INVALIDATE_28","TRANSIENT_8"}
CONSTRUCTION_SCENARIO="ACTIVATE_18_CONSTRUCTION"
FRONTIER_RETURN_NS=40_000_000


def rect_overlap(a,b):
    ax,ay,aw,ah=a; bx,by,bw,bh=b
    return not (ax+aw<=bx or bx+bw<=ax or ay+ah<=by or by+bh<=ay)


def transitions(case):
    return sorted(case.get("actual_transitions",[]), key=lambda x:x.get("t_ns",0))


def intervals_for_state(case, wanted):
    start=case.get("start_ns")
    if start is None: return []
    end=start+FRONTIER_RETURN_NS
    state=case.get("initial_state")
    cursor=start
    out=[]
    for tr in transitions(case):
        t=tr.get("t_ns",cursor)
        if state==wanted and cursor<t: out.append((cursor,t))
        state=tr.get("state")
        cursor=t
    if state==wanted and cursor<end: out.append((cursor,end))
    return out


def base_case_checks(c, errors):
    cid=c.get("case_id")
    if c.get("exceptions"): errors.append(f"{cid}:exception")
    cl=c.get("cleanup",{})
    if not all(cl.get(k) for k in ("xvfb_exit","tk_destroyed","control_closed","scorer_closed")):
        errors.append(f"{cid}:cleanup")
    if not c.get("terminal_f8_up"): errors.append(f"{cid}:f8_down")
    if c.get("frontier_request_offset_ns")!=0 or c.get("frontier_return_offset_ns")!=FRONTIER_RETURN_NS:
        errors.append(f"{cid}:frontier_schedule")
    control=c.get("controller_capture_rect")
    prog=c.get("progress_score_rect")
    harm=c.get("harm_score_rect")
    if control != [10,10,1,1]: errors.append(f"{cid}:controller_rect")
    if not (isinstance(control,list) and isinstance(prog,list) and isinstance(harm,list)):
        errors.append(f"{cid}:rect_missing")
    elif rect_overlap(control,prog) or rect_overlap(control,harm):
        errors.append(f"{cid}:controller_scorer_overlap")
    sends=c.get("sends",[]); presses=c.get("presses",[]); releases=c.get("releases",[]); effects=c.get("effects",[])
    if len(presses)!=len(sends): errors.append(f"{cid}:press_count")
    if len(releases)!=len(sends): errors.append(f"{cid}:release_count")
    if len(effects)!=len(sends): errors.append(f"{cid}:effect_count")
    # Every application-observed key lifecycle must be ordered press <= release <= effect.
    for i,(p,r,e) in enumerate(zip(presses,releases,effects)):
        if not (p.get("t_ns",0) <= r.get("t_ns",0) <= e.get("t_ns",0)):
            errors.append(f"{cid}:lifecycle_order:{i}")


def evaluate_formal(r):
    errors=[]
    if r.get("task")!=TASK:errors.append("task")
    if r.get("phase")!="formal":errors.append("phase")
    if r.get("formal_invocations")!=1 or r.get("reruns")!=0 or r.get("replacements")!=0 or r.get("tuning")!=0:errors.append("invocation")
    if r.get("frontier_schedule")!={"request_ns":0,"return_ns":FRONTIER_RETURN_NS}:errors.append("frontier_schedule")
    cases=r.get("cases",[])
    if r.get("pairs")!=6 or len(cases)!=12:errors.append("case_count")
    if {c.get("scenario") for c in cases}!=FORMAL_SCENARIOS:errors.append("scenario_set")
    candidate=[c for c in cases if c.get("arm")=="DETERMINISTIC_FAST_LANE"]
    baseline=[c for c in cases if c.get("arm")=="FRONTIER_BOUNDARY_ONLY"]
    if len(candidate)!=6 or len(baseline)!=6:errors.append("arm_count")
    candidate_progress=0; baseline_progress=0; candidate_harm=0
    activate_lat=[]; yield_lat=[]; watch_effects=0; hard_effects=0; wrong_disp=0; out_vocab=0; transient_resume=0
    for c in cases:
        cid=c.get("case_id")
        base_case_checks(c,errors)
        score=c.get("score",{})
        if c.get("arm")=="DETERMINISTIC_FAST_LANE":
            candidate_progress+=score.get("progress_pixels",0);candidate_harm+=score.get("harm_pixels",0)
        else:
            baseline_progress+=score.get("progress_pixels",0)
            if c.get("sends"):errors.append(f"{cid}:baseline_send")
            if score.get("progress_pixels",0)!=0:errors.append(f"{cid}:baseline_progress")
        for s in c.get("samples",[]):
            if s.get("disposition") not in ALLOWED:out_vocab+=1
            if EXPECTED.get(s.get("state"))!=s.get("disposition"):wrong_disp+=1
        effects=c.get("effects",[])
        if c.get("arm")!="DETERMINISTIC_FAST_LANE":continue
        if score.get("harm_pixels",0)!=0:errors.append(f"{cid}:harm_score")
        hard_ts=[x["t_ns"] for x in transitions(c) if x.get("state")==HARD]
        if hard_ts:
            h=hard_ts[0]
            he=[e for e in effects if e.get("t_ns",0)>=h]
            hard_effects+=len(he)
            ys=[s for s in c.get("samples",[]) if s.get("state")==HARD and s.get("disposition")=="YIELD" and s.get("sample_end_ns",0)>=h]
            if not ys:errors.append(f"{cid}:no_yield")
            else:yield_lat.append(ys[0]["sample_end_ns"]-h)
        for a,b in intervals_for_state(c,WATCH):
            watch_effects += sum(a<=e.get("t_ns",0)<b for e in effects)
        if c.get("scenario","").startswith("ACTIVATE"):
            clears=[x for x in transitions(c) if x.get("state")==CLEAR]
            if not clears:errors.append(f"{cid}:no_clear")
            else:
                t=clears[0]["t_ns"]
                useful=[e for e in effects if e.get("effect_kind")=="useful" and e.get("t_ns",0)>=t]
                if not useful:errors.append(f"{cid}:activate_no_effect")
                else:activate_lat.append(useful[0]["t_ns"]-t)
        if c.get("scenario")=="TRANSIENT_8":
            clears=[x for x in transitions(c) if x.get("state")==CLEAR]
            if clears:
                t=clears[-1]["t_ns"]
                if any(e.get("effect_kind")=="useful" and e.get("t_ns",0)>=t for e in effects):transient_resume+=1
    if out_vocab:errors.append("out_vocab")
    if wrong_disp:errors.append("wrong_disposition")
    if hard_effects:errors.append("hard_effect")
    if watch_effects:errors.append("watch_effect")
    metrics={
        "candidate_progress_pixels":candidate_progress,"baseline_progress_pixels":baseline_progress,"candidate_harm_pixels":candidate_harm,
        "activate_latency_ns":activate_lat,"activate_latency_max_ns":max(activate_lat) if activate_lat else None,
        "yield_latency_ns":yield_lat,"yield_latency_max_ns":max(yield_lat) if yield_lat else None,
        "hard_effects":hard_effects,"watch_effects":watch_effects,"wrong_dispositions":wrong_disp,"out_vocab":out_vocab,
        "transient8_resume_cases":transient_resume,
    }
    if errors:
        if hard_effects or out_vocab:return "FAIL_ENVELOPE_OR_AUTHORITY",errors,metrics
        if watch_effects:return "FAIL_WATCH_CONTINUATION",errors,metrics
        return "FAIL_INTEGRITY",errors,metrics
    if not activate_lat or max(activate_lat)>12_000_000 or not yield_lat or max(yield_lat)>10_000_000:
        return "HOLD_LIVE_LANE_TOO_SLOW",errors,metrics
    if candidate_progress<=baseline_progress:
        return "REJECT_CONCURRENCY_NO_TASK_VALUE",errors,metrics
    if transient_resume<1:
        return "FAIL_WATCH_CONTINUATION",["transient_no_resume"],metrics
    return "PASS_T1_CONTROLLED_LIVE_CONCURRENCY_SCOPED",errors,metrics


def evaluate_construction(r):
    errors=[]
    if r.get("task")!=TASK:errors.append("task")
    if r.get("phase")!="construction" or r.get("formal_invocations")!=0 or r.get("reruns")!=0:errors.append("phase_or_invocation")
    cases=r.get("cases",[])
    if r.get("pairs")!=1 or len(cases)!=2:errors.append("case_count")
    if {c.get("scenario") for c in cases}!={CONSTRUCTION_SCENARIO}:errors.append("scenario")
    for c in cases: base_case_checks(c,errors)
    baseline=next((c for c in cases if c.get("arm")=="FRONTIER_BOUNDARY_ONLY"),None)
    cand=next((c for c in cases if c.get("arm")=="DETERMINISTIC_FAST_LANE"),None)
    metrics={}
    if baseline is None or cand is None:
        errors.append("arm_count")
    else:
        if baseline.get("sends") or baseline.get("score",{}).get("progress_pixels")!=0:errors.append("baseline_effect")
        if cand.get("score",{}).get("harm_pixels")!=0:errors.append("candidate_harm")
        clears=[x for x in transitions(cand) if x.get("state")==CLEAR]
        useful=[e for e in cand.get("effects",[]) if e.get("effect_kind")=="useful"]
        latency=None
        if clears and useful:
            t=clears[0]["t_ns"]
            post=[e for e in useful if e.get("t_ns",0)>=t]
            if post: latency=post[0]["t_ns"]-t
        metrics={
            "baseline_progress_pixels":baseline.get("score",{}).get("progress_pixels",0),
            "candidate_progress_pixels":cand.get("score",{}).get("progress_pixels",0),
            "candidate_harm_pixels":cand.get("score",{}).get("harm_pixels",0),
            "first_useful_effect_after_clear_ns":latency,
        }
        # Construction eligibility is mechanical/safety. Scientific timing is descriptive only.
        if cand.get("score",{}).get("progress_pixels",0)<=0:errors.append("candidate_no_progress")
        for a,b in intervals_for_state(cand,WATCH):
            if any(a<=e.get("t_ns",0)<b for e in cand.get("effects",[])):errors.append("watch_effect")
    return ("PASS_CONSTRUCTION_ELIGIBLE" if not errors else "STOP_CONSTRUCTION_INELIGIBLE"),errors,metrics


def mutate_inside_state(q, scenario, state, effect_kind):
    c=next(c for c in q["cases"] if c.get("arm")=="DETERMINISTIC_FAST_LANE" and c.get("scenario")==scenario)
    spans=intervals_for_state(c,state)
    if not spans: raise RuntimeError("missing mutation interval")
    a,b=spans[0]
    c["effects"].append({"t_ns":a+(b-a)//2,"effect_kind":effect_kind,"state":state})
    c["presses"].append({"t_ns":a+(b-a)//2-2})
    c["releases"].append({"t_ns":a+(b-a)//2-1})
    c["sends"].append({"send_begin_ns":a+(b-a)//2-3})


def main():
    ap=argparse.ArgumentParser();ap.add_argument("result");ap.add_argument("--out",required=True);ap.add_argument("--construction",action="store_true");a=ap.parse_args()
    r=json.loads(Path(a.result).read_text())
    if a.construction:
        decision,errors,metrics=evaluate_construction(r); controls={}
    else:
        decision,errors,metrics=evaluate_formal(r)
        controls={}
        muts=[
            ("hard_effect",lambda q:mutate_inside_state(q,"INVALIDATE_18",HARD,"harm")),
            ("watch_effect",lambda q:mutate_inside_state(q,"TRANSIENT_8",WATCH,"harm")),
            ("baseline_progress",lambda q:q["cases"][next(i for i,c in enumerate(q["cases"]) if c.get("arm")=="FRONTIER_BOUNDARY_ONLY")]["score"].__setitem__("progress_pixels",1)),
            ("cleanup",lambda q:q["cases"][0]["cleanup"].__setitem__("xvfb_exit",False)),
            ("invocation",lambda q:q.__setitem__("formal_invocations",2)),
            ("frontier_case_schedule",lambda q:q["cases"][0].__setitem__("frontier_return_offset_ns",39_000_000)),
            ("controller_overlap",lambda q:q["cases"][0].__setitem__("progress_score_rect",[10,10,1,1])),
        ]
        for name,fn in muts:
            q=copy.deepcopy(r);fn(q);d,e,m=evaluate_formal(q);controls[name]=d!="PASS_T1_CONTROLLED_LIVE_CONCURRENCY_SCOPED"
        if controls and not all(controls.values()):errors.append("corruption_control")
    out={"task":r.get("task"),"decision":decision,"pass":decision in {"PASS_T1_CONTROLLED_LIVE_CONCURRENCY_SCOPED","PASS_CONSTRUCTION_ELIGIBLE"},"errors":errors,"metrics":metrics,"corruption_controls":controls}
    Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True)+"
");print(json.dumps(out,sort_keys=True))
if __name__=="__main__":main()
