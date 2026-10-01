from __future__ import annotations
import hashlib,json,random
from candidate import classify
from oracle import classify_oracle
SEED=183920260919002
N=150000

def call(fn,r):
    try:return ("OK",fn(r))
    except Exception as e:return ("ERR",type(e).__name__,str(e))

def valid_base(i):
    return {"plan_id":f"p{i}","actuation_id":f"a{i}","input_authority":False,"semantic_authority":False}

def gen(rng,i):
    b=valid_base(i); t=rng.randrange(1_000,10_000_000); typ=rng.randrange(13)
    if typ==0:
        lo=t; dh=t+rng.randrange(0,1000); ul=dh+rng.randrange(0,100000); uh=ul+rng.randrange(0,1000)
        return {**b,"kind":"physical_actuation","owner_id":"o","intent_token":"i","key":"F8","down_lo_ns":lo,"down_hi_ns":dh,"up_lo_ns":ul,"up_hi_ns":uh}
    if typ==1:
        return {**b,"kind":"state_feedback","signal":rng.choice(["health","ammo"]),"value":rng.randrange(0,201),"t_ns":t}
    if typ in [2,3,4]:
        dhi=t+500; et=t+(1000 if typ!=3 else 100); cr=("same_process_monotonic" if typ in [2,3] else "unknown")
        return {**b,"kind":"task_effect","effect_id":f"e{i}","scorer_source":"independent_public_scorer","scored":True,"effect_type":rng.choice(["kill","death","map_exit","progress"]),"t_ns":et,"down_hi_ns":dhi,"clock_relation":cr}
    if typ==5:return {**b,"kind":"viewport_change","t_ns":t}
    if typ==6:return {**b,"kind":"program_terminal","t_ns":t}
    if typ==7:return {"kind":"run_total","kill_count":rng.randrange(5),"death_count":rng.randrange(5),"map_exit":False}
    if typ==8:return {**b,"kind":"hud_delta_unscored","signal":"health","t_ns":t}
    if typ==9:return {**b,"kind":"no_task_effect"}
    if typ==10:return {**b,"kind":"task_effect","effect_id":f"e{i}","scorer_source":"s","scored":False,"effect_type":"kill","t_ns":t+10,"down_hi_ns":t,"clock_relation":"same_process_monotonic"}
    if typ==11:return {**b,"kind":"task_effect","effect_id":"","scorer_source":"s","scored":True,"effect_type":"kill","t_ns":t+10,"down_hi_ns":t,"clock_relation":"same_process_monotonic"}
    return {**b,"kind":"state_feedback","signal":"health","value":100,"t_ns":t,"input_authority":True}

def fixed_cases():
    return [
      ({"kind":"viewport_change","plan_id":"p","input_authority":False,"semantic_authority":False},"UNRESOLVED"),
      ({"kind":"program_terminal","plan_id":"p","input_authority":False,"semantic_authority":False},"UNRESOLVED"),
      ({"kind":"run_total","kill_count":1,"death_count":0,"map_exit":False},"UNRESOLVED"),
      ({"kind":"hud_delta_unscored","plan_id":"p","signal":"health"},"UNRESOLVED"),
      ({"kind":"task_effect","effect_id":"e","plan_id":"p","actuation_id":"a","scorer_source":"s","scored":True,"effect_type":"kill","t_ns":99,"down_hi_ns":100,"clock_relation":"same_process_monotonic"},"UNRESOLVED"),
      ({"kind":"task_effect","effect_id":"e","plan_id":"p","actuation_id":"a","scorer_source":"s","scored":True,"effect_type":"kill","t_ns":101,"down_hi_ns":100,"clock_relation":"unknown"},"UNRESOLVED"),
      ({"kind":"task_effect","effect_id":"e","plan_id":"p","actuation_id":"a","scorer_source":"s","scored":True,"effect_type":"kill","t_ns":101,"down_hi_ns":100,"clock_relation":"same_process_monotonic"},"TASK_EFFECT"),
      ({"kind":"state_feedback","plan_id":"p","signal":"health","value":90,"t_ns":101},"STATE_FEEDBACK"),
      ({"kind":"physical_actuation","plan_id":"p","actuation_id":"a","owner_id":"o","intent_token":"i","key":"F8","down_lo_ns":1,"down_hi_ns":2,"up_lo_ns":3,"up_hi_ns":4},"PHYSICAL_ACTUATION"),
      ({"kind":"no_task_effect","plan_id":"p"},"UNRESOLVED"),
    ]

def compute():
    rng=random.Random(SEED); mismatch=0; roles={}; digest=hashlib.sha256()
    for i in range(N):
        r=gen(rng,i); a=call(classify,r); o=call(classify_oracle,r)
        if a!=o:mismatch+=1
        if a[0]=="OK": roles[a[1]["role"]]=roles.get(a[1]["role"],0)+1
        digest.update(json.dumps([r,a],sort_keys=True,separators=(",",":")).encode()+b"\n")
    fixed_ok=0
    for r,want in fixed_cases():
        a=call(classify,r); o=call(classify_oracle,r)
        if a==o and a[0]=="OK" and a[1]["role"]==want: fixed_ok+=1
    return {"candidate_oracle_mismatch":mismatch,"fixed_controls_pass":fixed_ok,"fixed_controls_total":len(fixed_cases()),"role_counts":roles,"row_digest_sha256":digest.hexdigest()}

def main():
    core=compute()
    out={"schema":"map01-task-effect-contract-formal-v1","seed":SEED,"rows":N,**core,"formal_invocations":1,"reruns":0,"replacements":0,"tuning":0}
    out["decision"]="PASS_MAP01_TASK_EFFECT_INSTRUMENTATION_CONTRACT_SCOPED" if core["candidate_oracle_mismatch"]==0 and core["fixed_controls_pass"]==core["fixed_controls_total"] and all(core["role_counts"].get(x,0)>0 for x in ["PHYSICAL_ACTUATION","STATE_FEEDBACK","TASK_EFFECT","UNRESOLVED"]) else "FAIL_MAP01_TASK_EFFECT_INSTRUMENTATION_CONTRACT"
    print(json.dumps(out,sort_keys=True,indent=2))
    return 0 if out["decision"].startswith("PASS") else 1
if __name__=="__main__":raise SystemExit(main())
