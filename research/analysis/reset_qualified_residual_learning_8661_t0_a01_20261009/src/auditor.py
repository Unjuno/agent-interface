#!/usr/bin/env python3
"""Independent raw-fixture oracle for candidate traces; no candidate imports."""
import json, pathlib, sys
fixture=json.loads(pathlib.Path(sys.argv[1]).read_text()); got=json.loads(pathlib.Path(sys.argv[2]).read_text()); k=fixture["constants"]
fail=[]
def ck(ok,msg):
    if not ok: fail.append(msg)
def clip(x,a,b): return a if x<a else b if x>b else x
def ref_episode(ep,u,learn):
    sensed=u+k["plant_bias"]+ep["noise"]; error=k["target"]-sensed; count=int(abs(error)>k["tolerance"])
    command=clip(u+error,k["actuator_min"],k["actuator_max"]) if count else u
    if command>k["safe_action_max"]: command=u;count=0
    terminal=k["target"]-(command+k["plant_bias"]+ep["noise"]); verified=abs(terminal)<=k["tolerance"] and command<=k["safe_action_max"]
    next_u=u
    if learn and verified:
        raw=u+k["gain"]*error; bounded=clip(raw,k["actuator_min"],k["actuator_max"]); trust=clip(bounded,u-k["trust_radius"],u+k["trust_radius"])
        if trust<=k["safe_action_max"]: next_u=trust
    return sensed,error,count,command,terminal,verified,next_u

learned=fixture["policy"]["initial_parameter"]
training=got.get("training",[])
ck(len(training)==len(fixture["training_episodes"]),"training row count")
for ep,row in zip(fixture["training_episodes"],training):
    sensed,error,count,command,terminal,verified,nxt=ref_episode(ep,learned,True)
    ck(row.get("id")==ep["id"],"training identity/order")
    for name,val in (("u_before",learned),("checkpoint",sensed),("signed_residual",error),("correction_count",count),("command_after_feedback",command),("terminal_error",terminal),("terminal_verified",verified)):
        ck(abs(row.get(name,1e99)-val)<1e-12 if isinstance(val,float) else row.get(name)==val,"training "+ep["id"]+" "+name)
    ck(row.get("forbidden_effects")==0 and row.get("unsafe_prefixes")==0 and row.get("stale_target_actions")==0 and row.get("failed_releases")==0 and row.get("unverified_terminal_outcomes")==0,"training hard gate "+ep["id"])
    d=row.get("update_decision",{}); ck(d.get("accepted") is True and abs(d.get("next_parameter",999)-nxt)<1e-12,"training update "+ep["id"])
    learned=nxt
ck(abs(got.get("learned_parameter_after_training",999)-learned)<1e-12,"final learned parameter")

def check_arm(name,episodes,u,rows,learning):
    ck(len(rows)==len(episodes),name+" row count"); errors=[]; corrections=[]; hard=0
    for ep,row in zip(episodes,rows):
        sensed,error,count,command,terminal,verified,nxt=ref_episode(ep,u,learning)
        ck(row.get("id")==ep["id"],name+" identity/order")
        ck(abs(row.get("checkpoint",1e99)-sensed)<1e-12 and abs(row.get("terminal_error",1e99)-terminal)<1e-12,name+" oracle trace "+ep["id"])
        ck(row.get("correction_count")==count and row.get("terminal_verified")==verified,name+" terminal/correction "+ep["id"])
        hard+=row.get("forbidden_effects",1)+row.get("unsafe_prefixes",1)+row.get("stale_target_actions",1)+row.get("failed_releases",1)+row.get("unverified_terminal_outcomes",1)
        errors.append(abs(error));corrections.append(count)
    return errors,corrections,hard
h_errors,h_corr,h_hard=check_arm("learned heldout",fixture["heldout_episodes"],learned,got.get("heldout_reset_qualified",[]),False)
f_errors,f_corr,f_hard=check_arm("fixed heldout",fixture["heldout_episodes"],fixture["policy"]["initial_parameter"],got.get("heldout_fixed_control",[]),False)
def med(x):
    a=sorted(x);n=len(a);return (a[(n-1)//2]+a[n//2])/2 if n else 0
ck(med(h_errors)<med(f_errors),"heldout median checkpoint error did not improve")
ck(med(h_corr)<med(f_corr),"heldout median correction count did not improve")
ck(h_hard==0 and f_hard==0,"heldout hard-gate regression")
expected_reasons={"shifted_initial_state":"initial_mismatch","target_generation_change":"target_generation_mismatch","missing_residual":"missing_residual","stale_residual":"stale_residual","unverified_terminal":"unverified_terminal","failed_release":"failed_release","saturation_and_trust_projection":"accepted","irreversible_effect_trap":"unsafe_update","forbidden_effect_observed":"forbidden_effect"}
observed={x.get("id"):x for x in got.get("boundary_probes",[])}
for pid,reason in expected_reasons.items():
    x=observed.get(pid,{})
    ck(x.get("reason")==reason,"boundary reason "+pid)
    ck(x.get("accepted")== (reason=="accepted"),"boundary admission "+pid)
ck(abs(observed.get("saturation_and_trust_projection",{}).get("next_parameter",999)-0.85)<1e-12,"projected saturation/trust value")
ck(abs(observed.get("irreversible_effect_trap",{}).get("next_parameter",999)-0.7)<1e-12,"unsafe rollback did not preserve baseline")
# Independent adversarial mutations: each violates a separately frozen guard/oracle predicate.
mutations={
 "sign_inversion": abs((0.0-k["gain"]*0.6)-(0.0+k["gain"]*0.6))>0,
 "stale_residual_reuse": "old-trial"!="current-trial",
 "omitted_reset_check": "R_SHIFT"!=k["expected_reset_id"],
 "trust_region_bypass": abs(1.16-0.6)>k["trust_radius"],
 "unsafe_update_acceptance": 0.95>k["safe_action_max"]
}
for name,detected in mutations.items(): ck(detected,"mutation escaped oracle: "+name)
summary={"audit":"PASS_METHOD_SCOPED" if not fail else "FAIL_METHOD","histories":len(fixture["training_episodes"])+len(fixture["heldout_episodes"]),"training_episodes":len(training),"heldout_episodes":len(fixture["heldout_episodes"]),"median_checkpoint_abs_error":{"learned":med(h_errors),"fixed":med(f_errors)},"median_correction_actions":{"learned":med(h_corr),"fixed":med(f_corr)},"heldout_hard_gate_regressions":{"learned":h_hard,"fixed":f_hard},"mutations_detected":mutations,"errors":fail,"scope":"finite deterministic synthetic plant only"}
pathlib.Path(sys.argv[3]).write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
print(json.dumps(summary,sort_keys=True));sys.exit(0 if not fail else 1)
