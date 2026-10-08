#!/opt/pyvenv/bin/python3
import itertools,json,pathlib
from model import EffectPendingTracker, EVENTS
from oracle import oracle, normalize_candidate


def check_invariants(trace, view):
    errs=[]
    if view["current_input_authority"] is not False: errs.append("input_authority")
    if view["new_input_admissible"] is not False: errs.append("new_input_admissible")
    if view["semantic_authority"] is not False: errs.append("semantic_authority")
    if "RELEASE_OK" not in trace and view["client_can_resume_reasoning"]: errs.append("resume_without_release")
    if "EFFECT_OK" not in trace and view["task_effect_resolved"]: errs.append("effect_without_effect")
    if "TERMINAL_OK" in trace and "EFFECT_OK" not in trace and view["task_effect_resolved"]: errs.append("terminal_implies_effect")
    if "RELEASE_OK" in trace and "EFFECT_OK" not in trace and view["task_effect_resolved"]: errs.append("release_implies_effect")
    if "EFFECT_OK" in trace and "RELEASE_OK" not in trace and view["client_can_resume_reasoning"]: errs.append("effect_causes_resume")
    return errs


def run(max_len=5):
    total=0; mismatches=[]; invariant_errors=[]; states={}
    for n in range(max_len+1):
        for trace in itertools.product(EVENTS, repeat=n):
            total += 1
            t=EffectPendingTracker()
            for sym in trace: t.ingest_symbol(sym)
            cv=normalize_candidate(t.view()); ov=oracle(trace)
            states[cv["state"]+":"+cv["task_effect_status"]+":"+str(cv["physical_release_verified"])+":"+str(cv["terminal_received"])]=states.get(cv["state"]+":"+cv["task_effect_status"]+":"+str(cv["physical_release_verified"])+":"+str(cv["terminal_received"]),0)+1
            if cv != ov:
                mismatches.append({"trace":trace,"candidate":cv,"oracle":ov})
                if len(mismatches)>=20: break
            errs=check_invariants(trace,cv)
            if errs:
                invariant_errors.append({"trace":trace,"errors":errs,"view":cv})
                if len(invariant_errors)>=20: break
        if mismatches or invariant_errors: break
    return {"max_len":max_len,"event_count":len(EVENTS),"trace_count":total,
            "mismatch_count":len(mismatches),"invariant_error_count":len(invariant_errors),
            "mismatches":mismatches,"invariant_errors":invariant_errors,
            "state_histogram":states}

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser(); ap.add_argument('--out',required=True); a=ap.parse_args()
    r=run(); pathlib.Path(a.out).write_text(json.dumps(r,indent=2,sort_keys=True)); print(json.dumps({k:v for k,v in r.items() if k not in ('mismatches','invariant_errors','state_histogram')},indent=2))
