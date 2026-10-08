from __future__ import annotations
import copy, json, statistics, sys, time
from pathlib import Path

HERE=Path(__file__).resolve().parent
CALLER_ROOT=Path('/mnt/data/runtime-preview-extracted/research/live_control')
sys.path.insert(0,str(CALLER_ROOT)); sys.path.insert(0,str(HERE))
from adaptive_acquisition_caller_v3 import run
from authority_ended_bridge_v1 import to_caller_execution_decision

TARGET={"handle":"recovery-v1","point":[0,0]}
QUIET_ROWS=[
{"seed":993200,"arm":"quiet_hold","terminal_status":"authority_ended","steps_completed":0,"release_verified":True,"keys_down":[],"buttons_down":[],"post_release_input_admissions":0,"post_authority":{"captures":1,"sequence":2,"error":None,"lifecycle_deadline_ns":1224313306625,"grants_input_authority":False,"tail_program_steps_resumed":0,"sequence_advanced":True,"snapshot_finished_ns":1223972533155,"within_lifecycle_deadline":True},"score_agreement":True},
{"seed":993201,"arm":"quiet_hold","terminal_status":"authority_ended","steps_completed":0,"release_verified":True,"keys_down":[],"buttons_down":[],"post_release_input_admissions":0,"post_authority":{"captures":1,"sequence":2,"error":None,"lifecycle_deadline_ns":1228750869346,"grants_input_authority":False,"tail_program_steps_resumed":0,"sequence_advanced":True,"snapshot_finished_ns":1228408906993,"within_lifecycle_deadline":True},"score_agreement":True},
{"seed":993202,"arm":"quiet_hold","terminal_status":"authority_ended","steps_completed":0,"release_verified":True,"keys_down":[],"buttons_down":[],"post_release_input_admissions":0,"post_authority":{"captures":1,"sequence":2,"error":None,"lifecycle_deadline_ns":1241927499720,"grants_input_authority":False,"tail_program_steps_resumed":0,"sequence_advanced":True,"snapshot_finished_ns":1241593137584,"within_lifecycle_deadline":True},"score_agreement":True},
]

def spec():
    return {"target":"Recovery","route":"reuse","coarse_origin":"caller_provided",
            "provided_coarse":None,"cached_target":TARGET,"local_repair_on":[],
            "repair_on":[],"session_id":"authority-ended-integration-v1"}

def mapping(receipt,calls):
    def stage(name,value):
        def f(payload): calls.append(name); return copy.deepcopy(value)
        return f
    return {
      "reuse_revalidate":stage("reuse_revalidate",{"status":"revalidated"}),
      "final_revalidate":stage("final_revalidate",{"status":"revalidated"}),
      "execute":lambda payload: (calls.append("execute") or to_caller_execution_decision(receipt)),
      "verify_effect":stage("verify_effect",{"status":"succeeded"}),
    }

def mutate(row,name):
    x=copy.deepcopy(row)
    if name=="missing_post": x["post_authority"]=None
    elif name=="stale_sequence": x["post_authority"]["sequence_advanced"]=False
    elif name=="unverified_release": x["release_verified"]=False
    elif name=="post_input": x["post_release_input_admissions"]=1
    elif name=="tail_revived": x["post_authority"]["tail_program_steps_resumed"]=1
    elif name=="authority_regrant": x["post_authority"]["grants_input_authority"]=True
    elif name=="late_observation": x["post_authority"]["within_lifecycle_deadline"]=False
    elif name=="nonempty_keys": x["keys_down"]=["Shift_L"]
    elif name=="observation_error": x["post_authority"]["error"]="capture failed"
    elif name=="scorer_disagree": x["score_agreement"]=False
    else: raise KeyError(name)
    return x

def run_case(row):
    calls=[]
    result=run(spec(),mapping(row,calls))
    return result,calls

def formal(out):
    faults=["missing_post","stale_sequence","unverified_release","post_input",
            "tail_revived","authority_regrant","late_observation","nonempty_keys",
            "observation_error"]
    rows=[]
    for i,src in enumerate(QUIET_ROWS):
        result,calls=run_case(src)
        rows.append({"case":f"valid-{i}","source_seed":src["seed"],"kind":"valid",
                     "outcome":result["outcome"],"reason":result["reason"],
                     "verify_effect_called":"verify_effect" in calls,"calls":calls})
        privacy=mutate(src,"scorer_disagree")
        p,c=run_case(privacy)
        rows.append({"case":f"privacy-scorer-disagree-{i}","source_seed":src["seed"],"kind":"privacy_control",
                     "outcome":p["outcome"],"reason":p["reason"],
                     "verify_effect_called":"verify_effect" in c,"calls":c})
        for f in faults:
            r,c=run_case(mutate(src,f))
            rows.append({"case":f"{f}-{i}","source_seed":src["seed"],"kind":"fault",
                         "fault":f,"outcome":r["outcome"],"reason":r["reason"],
                         "verify_effect_called":"verify_effect" in c,"calls":c})
    valid=[r for r in rows if r["kind"]=="valid"]
    privacy=[r for r in rows if r["kind"]=="privacy_control"]
    faults_rows=[r for r in rows if r["kind"]=="fault"]
    hard=[]
    for r in valid+privacy:
        if (r["outcome"],r["reason"]) != ("EXECUTION_INCOMPLETE","authority_unavailable"):
            hard.append(r["case"]+":classification")
        if r["verify_effect_called"]: hard.append(r["case"]+":verify_effect")
    for r in faults_rows:
        if r["outcome"]=="TASK_SUCCEEDED": hard.append(r["case"]+":task_succeeded")
        if r["verify_effect_called"]: hard.append(r["case"]+":verify_effect")
        if r["outcome"]!="CALLER_FAILED": hard.append(r["case"]+":not_failed_closed")
    summary={"schema":"authority-ended-adaptive-caller-integration-v1-result",
             "caller_git_blob":"7faf042304728ce91a3e4f89d465b251ea0bf70d",
             "source_quiet_result_git_blob":"0627dba669903d3d8cc6e707cae9b9d329a623e5",
             "valid_cases":len(valid),"privacy_controls":len(privacy),"fault_cases":len(faults_rows),
             "valid_execution_incomplete":sum(r["outcome"]=="EXECUTION_INCOMPLETE" for r in valid),
             "privacy_control_execution_incomplete":sum(r["outcome"]=="EXECUTION_INCOMPLETE" for r in privacy),
             "faults_task_succeeded":sum(r["outcome"]=="TASK_SUCCEEDED" for r in faults_rows),
             "faults_failed_closed":sum(r["outcome"]=="CALLER_FAILED" for r in faults_rows),
             "verify_effect_calls":sum(r["verify_effect_called"] for r in rows),
             "hard_failures":hard,"rows":rows,
             "decision":"PASS_CALLER_INTEGRATION" if not hard else "FAIL"}
    out.write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:v for k,v in summary.items() if k!='rows'},indent=2,sort_keys=True))
    return 0 if not hard else 2

def construction():
    # Exact caller v3 should reject raw authority_ended as an unknown execution status.
    raw=copy.deepcopy(QUIET_ROWS[0]); calls=[]
    def rawmap(payload): calls.append("execute"); return {"status":"authority_ended"}
    m=mapping(raw,calls); m["execute"]=rawmap
    r=run(spec(),m)
    assert r["outcome"]=="CALLER_FAILED" and "unsupported" not in r.get("reason","") or r["outcome"]=="CALLER_FAILED"
    # Candidate bridge turns valid receipt into safe-yield, never verify-effect.
    r,c=run_case(QUIET_ROWS[0])
    assert (r["outcome"],r["reason"])==("EXECUTION_INCOMPLETE","authority_unavailable")
    assert "verify_effect" not in c
    # Missing post observation fails closed.
    r,c=run_case(mutate(QUIET_ROWS[0],"missing_post"))
    assert r["outcome"]=="CALLER_FAILED" and "verify_effect" not in c
    print("PASS construction")

if __name__=="__main__":
    if len(sys.argv)>1 and sys.argv[1]=="--construction": construction()
    else: raise SystemExit(formal(Path(sys.argv[1])))
