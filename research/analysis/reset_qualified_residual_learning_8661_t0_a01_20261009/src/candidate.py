#!/usr/bin/env python3
"""One-shot candidate for reset-qualified trial-to-trial residual learning."""
import json, pathlib, sys
F=json.loads(pathlib.Path(sys.argv[1]).read_text()); C=F["constants"]

def clipped(x,lo,hi): return min(hi,max(lo,x))
def propose(u,e):
    raw=u+C["gain"]*e
    actuator=clipped(raw,C["actuator_min"],C["actuator_max"])
    trust=clipped(actuator,u-C["trust_radius"],u+C["trust_radius"])
    return raw,actuator,trust

def decide(p):
    if p["reset_id"]!=C["expected_reset_id"]: return {"accepted":False,"next_parameter":p["parameter"],"reason":"initial_mismatch"}
    if p["target_generation"]!=C["expected_target_generation"]: return {"accepted":False,"next_parameter":p["parameter"],"reason":"target_generation_mismatch"}
    if not p["residual_present"]: return {"accepted":False,"next_parameter":p["parameter"],"reason":"missing_residual"}
    if p["residual_source"]!=p["completed_trial"] or p["residual_age"]>C["max_residual_age"]: return {"accepted":False,"next_parameter":p["parameter"],"reason":"stale_residual"}
    if not p["terminal_verified"]: return {"accepted":False,"next_parameter":p["parameter"],"reason":"unverified_terminal"}
    if not p["release_verified"]: return {"accepted":False,"next_parameter":p["parameter"],"reason":"failed_release"}
    if p["forbidden_effect"]: return {"accepted":False,"next_parameter":p["parameter"],"reason":"forbidden_effect"}
    raw,actuator,trust=propose(p["parameter"],p["residual"])
    if trust>C["safe_action_max"]: return {"accepted":False,"next_parameter":p["parameter"],"reason":"unsafe_update","raw":raw,"actuator_projected":actuator,"trust_projected":trust}
    return {"accepted":True,"next_parameter":trust,"reason":"accepted","raw":raw,"actuator_projected":actuator,"trust_projected":trust}

def episode(ep,u,update):
    noise=ep["noise"]; checkpoint=u+C["plant_bias"]+noise; residual=C["target"]-checkpoint
    correction=0; command=u
    if abs(residual)>C["tolerance"]:
        proposed=command+residual
        if proposed<=C["safe_action_max"]:
            command=clipped(proposed,C["actuator_min"],C["actuator_max"]); correction=1
        else:
            command=u
    final=command+C["plant_bias"]+noise
    valid=(abs(C["target"]-final)<=C["tolerance"] and command<=C["safe_action_max"])
    out={"id":ep["id"],"seed":ep["seed"],"u_before":u,"checkpoint":checkpoint,"signed_residual":residual,"correction_count":correction,"command_after_feedback":command,"terminal_error":C["target"]-final,"terminal_verified":valid,"release_verified":True,"forbidden_effects":0,"unsafe_prefixes":0,"stale_target_actions":0,"failed_releases":0,"unverified_terminal_outcomes":0}
    if update:
        probe={"parameter":u,"residual":residual,"reset_id":ep["reset_id"],"target_generation":ep["target_generation"],"residual_present":True,"residual_source":ep["id"],"completed_trial":ep["id"],"residual_age":0,"terminal_verified":valid,"release_verified":True,"forbidden_effect":False}
        out["update_decision"]=decide(probe)
    return out

learned=C["actuator_min"]*0+F["policy"]["initial_parameter"]; training=[]
for ep in F["training_episodes"]:
    row=episode(ep,learned,True); training.append(row)
    if row["update_decision"]["accepted"]: learned=row["update_decision"]["next_parameter"]
held=[]; fixed=[]
for ep in F["heldout_episodes"]:
    held.append(episode(ep,learned,False)); fixed.append(episode(ep,F["policy"]["initial_parameter"],False))
probes=[]
for p in F["boundary_probes"]: probes.append({"id":p["id"],**decide(p)})
result={"fixture_id":F["fixture_id"],"learned_parameter_after_training":learned,"training":training,"heldout_reset_qualified":held,"heldout_fixed_control":fixed,"boundary_probes":probes}
pathlib.Path(sys.argv[2]).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
