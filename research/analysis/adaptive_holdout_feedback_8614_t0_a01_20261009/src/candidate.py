#!/usr/bin/env python3
"""Finite adaptive validation-feedback simulator; no model or application calls."""
import json, math, pathlib, random, statistics, sys
P=json.loads(pathlib.Path(sys.argv[1]).read_text()); Q=P["protocol"]

def seed_for(seed,fam,tag,variant=0):
    return (seed*1000003 + fam*9176 + tag*65537 + variant*104729 + 0x6A09E667) & 0xffffffff

def make_validation(seed,fam):
    n=Q["validation_cases"]; k=Q["candidate_variants"]
    shared_rng=random.Random(seed_for(seed,fam,11))
    shared=[shared_rng.uniform(-Q["shared_case_halfwidth"],Q["shared_case_halfwidth"]) for _ in range(n)]
    all_rows=[]
    for variant in range(k):
        eff=Q["true_effect"] if fam==1 and variant==0 else 0.0
        rng=random.Random(seed_for(seed,fam,19,variant))
        all_rows.append([Q["baseline_mean"]+eff+shared[i]+rng.uniform(-Q["candidate_case_halfwidth"],Q["candidate_case_halfwidth"]) for i in range(n)])
    return all_rows

def make_confirm(seed,fam,variant):
    n=Q["confirmatory_cases"]
    shared_rng=random.Random(seed_for(seed,fam,31))
    shared=[shared_rng.uniform(-Q["shared_case_halfwidth"],Q["shared_case_halfwidth"]) for _ in range(n)]
    eff=Q["true_effect"] if fam==1 and variant==0 else 0.0
    rng=random.Random(seed_for(seed,fam,37,variant))
    return [Q["baseline_mean"]+eff+shared[i]+rng.uniform(-Q["candidate_case_halfwidth"],Q["candidate_case_halfwidth"]) for i in range(n)]

def mean(xs): return sum(xs)/len(xs)
def se(xs): return statistics.stdev(xs)/math.sqrt(len(xs)) if len(xs)>1 else 0.0
def feedback_code(policy,response):
    if policy=="FULL_RELEASE":
        return sum((i+1)*int(round(v*1000000)) for i,v in enumerate(response["case_values"])) & 0xffffffff
    value=response["mean"] if policy=="AGGREGATE_RELEASE" else response["bounded_answer"]
    return int(round(value*1000000)) & 0xffffffff

def next_variant(state,code,used,k):
    state=(state*1664525+code+1013904223)&0xffffffff
    v=1+(state%(k-1))
    while v in used: v=1+(v%(k-1))
    return v,state

def run_policy(seed,fam,policy,rounds,validation):
    used=set(); selector_transcript=[]; audit_trace=[]; state=(seed ^ (fam*0x9E3779B9) ^ (sum(ord(c) for c in policy)*2654435761) ^ rounds)&0xffffffff
    noise_rng=random.Random(seed_for(seed,fam,53,rounds))
    current=0; best=None
    for turn in range(rounds):
        if current in used: raise RuntimeError("duplicate candidate proposal")
        used.add(current); values=validation[current]; actual=mean(values)
        if policy=="FULL_RELEASE":
            response={"case_values":list(values)}; score=mean(response["case_values"])
        elif policy=="AGGREGATE_RELEASE":
            response={"mean":actual,"se":se(values)}; score=response["mean"]
        else:
            noise=noise_rng.gauss(0.0,Q["reusable_noise_sigma"]); bounded=min(Q["reusable_answer_bounds"][1],max(Q["reusable_answer_bounds"][0],actual+noise)); response={"bounded_answer":bounded}; score=response["bounded_answer"]
        selector_transcript.append({"turn":turn+1,"variant":current,"released":response})
        audit_row={"turn":turn+1,"variant":current,"validation_mean_truth":actual,"selector_score":score}
        if policy=="FULL_RELEASE": audit_row["released_case_values"]=response["case_values"]
        elif policy=="AGGREGATE_RELEASE": audit_row["released_mean"]=response["mean"]; audit_row["released_se"]=response["se"]
        else: audit_row["noise_draw"]=noise; audit_row["released_bounded_answer"]=response["bounded_answer"]
        if best is None or score>best["selector_score"]: best={"variant":current,"selector_score":score,"validation_mean":actual}
        code=feedback_code(policy,response); audit_row["feedback_code"] = code
        if turn+1<rounds: current,state=next_variant(state,code,used,Q["candidate_variants"]); audit_row["next_variant"] = current
        audit_trace.append(audit_row)
    variant=best["variant"]; confirm=make_confirm(seed,fam,variant)
    qstate="EXHAUSTED" if rounds==Q["query_composition_budget"] else "AVAILABLE"
    return {"policy":policy,"rounds":rounds,"query_count":rounds,"composition_units":rounds if policy=="REUSABLE_HOLDOUT" else 0,"composition_budget":Q["query_composition_budget"],"budget_state":qstate,"selector_transcript":selector_transcript,"audit_trace":audit_trace,"selected_variant":variant,"selected_validation_mean":best["validation_mean"],"selected_population_mean":Q["baseline_mean"]+(Q["true_effect"] if fam==1 and variant==0 else 0.0),"confirmatory_scores_after_selection":confirm,"lockbox_opened_after_selection":True,"hard_gates":dict(Q["safety_gates"])}

runs=[]
for fam_name,fam in (("null",0),("planted",1)):
  for seed in P["replicate_seeds"]:
    validation=make_validation(seed,fam)
    for rounds in Q["rounds"]:
      for policy in ("FULL_RELEASE","AGGREGATE_RELEASE","REUSABLE_HOLDOUT"):
        runs.append({"family":fam_name,"seed":seed,"evaluation":run_policy(seed,fam,policy,rounds,validation)})
    lockbox=make_confirm(seed,fam,0)
    runs.append({"family":fam_name,"seed":seed,"evaluation":{"policy":"ONE_SHOT_LOCKBOX","rounds":0,"query_count":0,"composition_units":0,"composition_budget":Q["query_composition_budget"],"budget_state":"NOT_USED","selector_transcript":[],"audit_trace":[],"selected_variant":0,"selected_validation_mean":None,"selected_population_mean":Q["baseline_mean"]+(Q["true_effect"] if fam==1 else 0.0),"confirmatory_scores_after_selection":lockbox,"lockbox_opened_after_selection":True,"hard_gates":dict(Q["safety_gates"])}})
result={"protocol_id":Q["protocol_id"],"run_count":len(runs),"runs":runs,"budget_probe":{"attempted_turn":Q["query_composition_budget"]+1,"budget_state":"STOP_EXHAUSTED","candidate_proposed":False}}
pathlib.Path(sys.argv[2]).write_text(json.dumps(result,separators=(",",":"))+"\n")
