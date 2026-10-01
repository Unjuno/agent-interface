from __future__ import annotations
import copy,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
CALLER_ROOT=Path('/mnt/data/runtime-preview-extracted/research/live_control')
sys.path.insert(0,str(CALLER_ROOT));sys.path.insert(0,str(HERE))
from adaptive_acquisition_caller_v3 import run
from two_dispatch_gate_v1 import open_replan_token,current_revalidation,consume_for_execute

TARGET={"handle":"recovery-v1","point":[0,0]}
ROWS=[
{"seed":993200,"terminal_status":"authority_ended","steps_completed":0,"release_verified":True,"keys_down":[],"buttons_down":[],"post_release_input_admissions":0,"post_authority":{"captures":1,"sequence":2,"error":None,"lifecycle_deadline_ns":1224313306625,"grants_input_authority":False,"tail_program_steps_resumed":0,"sequence_advanced":True,"snapshot_finished_ns":1223972533155,"within_lifecycle_deadline":True},"score_agreement":True},
{"seed":993201,"terminal_status":"authority_ended","steps_completed":0,"release_verified":True,"keys_down":[],"buttons_down":[],"post_release_input_admissions":0,"post_authority":{"captures":1,"sequence":2,"error":None,"lifecycle_deadline_ns":1228750869346,"grants_input_authority":False,"tail_program_steps_resumed":0,"sequence_advanced":True,"snapshot_finished_ns":1228408906993,"within_lifecycle_deadline":True},"score_agreement":True},
{"seed":993202,"terminal_status":"authority_ended","steps_completed":0,"release_verified":True,"keys_down":[],"buttons_down":[],"post_release_input_admissions":0,"post_authority":{"captures":1,"sequence":2,"error":None,"lifecycle_deadline_ns":1241927499720,"grants_input_authority":False,"tail_program_steps_resumed":0,"sequence_advanced":True,"snapshot_finished_ns":1241593137584,"within_lifecycle_deadline":True},"score_agreement":True},
]

def spec():
    return {"target":"Recovery","route":"reuse","coarse_origin":"caller_provided","provided_coarse":None,
            "cached_target":TARGET,"local_repair_on":[],"repair_on":[],"session_id":"two-dispatch-v1"}

def second_dispatch(token,current_sequence,*,association_changed=False):
    calls=[]
    def reuse(payload):
        calls.append("reuse_revalidate")
        return current_revalidation(token,current_sequence,association_changed=association_changed)
    def final(payload):
        calls.append("final_revalidate")
        return current_revalidation(token,current_sequence,association_changed=association_changed)
    def execute(payload):
        calls.append("execute"); consume_for_execute(token); return {"status":"completed"}
    def verify(payload): calls.append("verify_effect"); return {"status":"succeeded"}
    result=run(spec(),{"reuse_revalidate":reuse,"final_revalidate":final,"execute":execute,"verify_effect":verify})
    return result,calls

def missing_post(r):
    x=copy.deepcopy(r);x["post_authority"]=None;return x

def stale_post(r):
    x=copy.deepcopy(r);x["post_authority"]["sequence_advanced"]=False;return x

def session_case(src,kind):
    receipt=copy.deepcopy(src)
    if kind=="missing_post": receipt=missing_post(receipt)
    elif kind=="stale_post": receipt=stale_post(receipt)
    elif kind=="privacy": receipt["score_agreement"]=False
    try: token=open_replan_token(receipt)
    except Exception as e:
        return {"kind":kind,"seed":src["seed"],"gate":"BLOCK_BEFORE_SECOND","error":repr(e),"second_invoked":False,"execute_calls":0,"task_succeeded":False}
    if kind=="stale_current": current=token.post_sequence
    else: current=token.post_sequence+1
    assoc=(kind=="association_changed")
    result,calls=second_dispatch(token,current,association_changed=assoc)
    replay=None
    if kind=="valid":
        replay_result,replay_calls=second_dispatch(token,current+1)
        replay={"outcome":replay_result["outcome"],"reason":replay_result["reason"],"calls":replay_calls}
    return {"kind":kind,"seed":src["seed"],"gate":"OPENED","second_invoked":True,
            "outcome":result["outcome"],"reason":result["reason"],"calls":calls,
            "execute_calls":calls.count("execute"),"task_succeeded":result["outcome"]=="TASK_SUCCEEDED",
            "token_used":token.used,"replay":replay}

def formal(out):
    kinds=["valid","privacy","missing_post","stale_post","stale_current","association_changed"]
    rows=[session_case(src,k) for src in ROWS for k in kinds]
    hard=[]
    for r in rows:
        k=r["kind"]
        if k in {"valid","privacy"}:
            if r.get("outcome")!="TASK_SUCCEEDED" or r.get("execute_calls")!=1: hard.append(f"{r['seed']}:{k}:second")
            if r["calls"] != ["reuse_revalidate","final_revalidate","execute","verify_effect"]: hard.append(f"{r['seed']}:{k}:order")
            if k=="valid":
                rp=r.get("replay") or {}
                if rp.get("outcome")!="CALLER_FAILED" or "execute" in rp.get("calls",[]): hard.append(f"{r['seed']}:replay")
        elif k in {"missing_post","stale_post"}:
            if r["gate"]!="BLOCK_BEFORE_SECOND" or r["second_invoked"]: hard.append(f"{r['seed']}:{k}:preblock")
        elif k in {"stale_current","association_changed"}:
            if r.get("outcome")!="SAFE_STOP" or r.get("execute_calls")!=0 or "execute" in r.get("calls",[]): hard.append(f"{r['seed']}:{k}:input")
    summary={"schema":"authority-ended-two-dispatch-integration-v1-result","caller_git_blob":"7faf042304728ce91a3e4f89d465b251ea0bf70d",
             "source_quiet_result_git_blob":"0627dba669903d3d8cc6e707cae9b9d329a623e5",
             "sessions":len(rows),"hard_failures":hard,"rows":rows,
             "valid_task_succeeded":sum(r.get("task_succeeded",False) for r in rows if r["kind"]=="valid"),
             "privacy_task_succeeded":sum(r.get("task_succeeded",False) for r in rows if r["kind"]=="privacy"),
             "pre_observation_blocks":sum(r["gate"]=="BLOCK_BEFORE_SECOND" for r in rows if r["kind"] in {"missing_post","stale_post"}),
             "freshness_safe_stops":sum(r.get("outcome")=="SAFE_STOP" for r in rows if r["kind"] in {"stale_current","association_changed"}),
             "replay_blocks":sum((r.get("replay") or {}).get("outcome")=="CALLER_FAILED" for r in rows if r["kind"]=="valid"),
             "decision":"PASS_TWO_DISPATCH_GATE" if not hard else "FAIL"}
    out.write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:v for k,v in summary.items() if k!='rows'},indent=2,sort_keys=True));return 0 if not hard else 2

def construction():
    r=session_case(ROWS[0],"valid"); assert r['outcome']=='TASK_SUCCEEDED' and r['execute_calls']==1
    r=session_case(ROWS[0],"missing_post"); assert r['gate']=='BLOCK_BEFORE_SECOND'
    r=session_case(ROWS[0],"stale_current"); assert r['outcome']=='SAFE_STOP' and r['execute_calls']==0
    print('PASS construction')

if __name__=='__main__':
    if sys.argv[1]=='--construction': construction()
    else: raise SystemExit(formal(Path(sys.argv[1])))
