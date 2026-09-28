"""One deterministic synthetic contract allocation; no GUI/model/input."""
from __future__ import annotations
import json
from pathlib import Path
from contract import classify
from oracle import oracle

HERE = Path(__file__).resolve().parent


def base():
    return {"session_id":"s1","plan_id":"p1","actuation_id":"a1","clock_axis_attested":True,
        "physical":{"owner_id":"owner1","empty_release_verified":True,
            "down":{"session_id":"s1","plan_id":"p1","actuation_id":"a1","owner_id":"owner1","key":"space","lower_ns":100,"upper_ns":110},
            "up":{"session_id":"s1","plan_id":"p1","actuation_id":"a1","owner_id":"owner1","key":"space","lower_ns":200,"upper_ns":210}},
        "state_feedback":[],"task_effects":[]}


def effect():
    return {"effect_id":"e1","session_id":"s1","plan_id":"p1","actuation_id":"a1","observed_ns":220,
        "scorer_source":"independent_progress_clock_v2","scored":True,"scorer_independent":True,
        "controller_visible":False,"kind":"KILL_COUNT_INCREASE","polarity":"useful"}


def cases():
    rows=[]
    x=base(); x["task_effects"]=[effect()]; rows.append(("positive_bound_effect",x,"TASK_EFFECT_SCOPED"))
    x=base(); x["state_feedback"]=[{"session_id":"s1","observed_ns":150,"signal":"health","before":90,"after":80}]; rows.append(("state_only",x,"UNRESOLVED_NO_TASK_EFFECT"))
    x=base(); x["physical"]={}; x["task_effects"]=[effect()]; rows.append(("effect_without_actuation",x,"UNRESOLVED_UNBOUND_OR_INVALID_EFFECT"))
    for cid,field,value in [
        ("viewport_as_effect","kind","VIEWPORT_PIXEL_CHANGE"),
        ("hud_as_effect","kind","HUD_HEALTH_CHANGE"),
        ("terminal_as_effect","kind","PROGRAM_COMPLETED"),
        ("run_total_as_effect","kind","RUN_FINAL_KILL_TOTAL"),
        ("effect_before_down","observed_ns",109),
        ("mismatched_plan","plan_id","foreign-plan"),
        ("mismatched_actuation","actuation_id","foreign-actuation"),
        ("scorer_not_independent","scorer_independent",False),
        ("controller_scorer","scorer_source","controller"),
    ]:
        x=base(); e=effect(); e[field]=value; x["task_effects"]=[e]
        rows.append((cid,x,"UNRESOLVED_UNBOUND_OR_INVALID_EFFECT"))
    x=base(); x["clock_axis_attested"]=False; x["task_effects"]=[effect()]; rows.append(("unrelated_clock",x,"UNRESOLVED_UNBOUND_OR_INVALID_EFFECT"))
    return rows


def main():
    output=[]
    for cid, raw, expected in cases():
        output.append({"case_id":cid,"raw":raw,"expected_task_effect":expected,
                       "candidate":classify(raw),"oracle":oracle(raw)})
    result={"schema":"map01-task-effect-contract-result-v1","allocation":"MAP01-TASK-EFFECT-CONTRACT-1839-20260928-01",
            "input_authority":False,"live_calls":0,"cases":output}
    path=HERE/"result.json"; path.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps({"result":str(path),"cases":len(output),
        "candidate_oracle_mismatches":sum(r["candidate"]!=r["oracle"] for r in output),
        "expected_gate_mismatches":sum(r["candidate"]["task_effect"]!=r["expected_task_effect"] for r in output)},sort_keys=True))


if __name__=="__main__": main()
