#!/usr/bin/env python3
"""Reconstruct choices and score them only against the separate oracle fixture."""
import json, math, pathlib, random, sys
Q=json.loads(pathlib.Path(sys.argv[1]).read_text())
F=json.loads(pathlib.Path(sys.argv[2]).read_text())
O=json.loads(pathlib.Path(sys.argv[3]).read_text())
R=json.loads(pathlib.Path(sys.argv[4]).read_text())
errors=[]
def ck(ok,msg):
    if not ok: errors.append(msg)
def estimate_source(c):
    ordered=sorted(c["source_cues"].items(),key=lambda item:(item[1],item[0]),reverse=True)
    return ordered[0][0],ordered[0][1]-ordered[1][1]
def choose(policy,c):
    if policy=="DECOMPOSED":
        source,confidence=estimate_source(c)
        if confidence<Q["decomposition_confidence_floor"] or c["dependency_warning"]: return "UNKNOWN"
        return {"ALEATORIC":"REPEAT","EPISTEMIC":"ALTERNATE","DYNAMIC":"WAIT","INTENT":"UNKNOWN"}[source]
    if policy=="TOTAL_UNCERTAINTY":
        u=c["total_uncertainty"];t=Q["total_uncertainty_thresholds"]
        if u>=t["repeat_at_or_above"]: return "REPEAT"
        if u>=t["alternate_at_or_above"]: return "ALTERNATE"
        if u>=t["wait_at_or_above"]: return "WAIT"
        return "UNKNOWN"
    if policy=="DECISION_VALUE":
        if c["decision_value_confidence"]<Q["decision_value_confidence_floor"]: return "UNKNOWN"
        w=Q["decision_value_cost_weight"];v={a:c["estimated_correct_probability"][a]-w*Q["costs"][a] for a in Q["actions"]}
        return max(Q["actions"],key=lambda a:(v[a],-Q["actions"].index(a)))
    return "REPEAT"
def seed_for(seed,case_id,action,tag):
    return (seed*1000003+sum(map(ord,case_id))*9176+sum(map(ord,action))*65537+tag*104729+0x6A09E667)&0xffffffff
def metric_seed(seed,case_id,action,tag): return random.Random(seed_for(seed,case_id,action,tag)).random()
truth={x["case_id"]:x for x in O["truth"]};cases={x["case_id"]:x for x in F["cases"]}
expected=len(F["replicate_seeds"])*len(F["cases"])*len(Q["policies"])
ck(R.get("protocol_id")==Q["protocol_id"],"protocol identity")
ck(len(R.get("rows",[]))==expected,"row count")
by={(x.get("seed"),x.get("case_id"),x.get("policy")):x for x in R.get("rows",[])}
ck(len(by)==expected,"duplicate/malformed row keys")
metrics={p:{"correct":0,"decision_changed":0,"cost":0.0,"unknown":0,"repeat":0,"n":0,"hard_gate_violations":0} for p in Q["policies"]+["ORACLE_INTERVENTION"]}
source_correct=0;source_n=0
for seed in F["replicate_seeds"]:
  for cid,c in cases.items():
    o=truth[cid];source_correct+=int(estimate_source(c)[0]==o["true_cause"]);source_n+=1
    for policy in Q["policies"]:
      row=by.get((seed,cid,policy),{});act=choose(policy,c)
      ck(set(row)=={"seed","case_id","policy","action","reported_cost","hard_gates"},"candidate output schema or truth-label leak")
      ck(row.get("action")==act,"policy action reconstruction")
      ck(row.get("reported_cost")==Q["costs"][act],"reported intervention cost")
      ck(row.get("hard_gates")==Q["hard_gates"],"exact hard-gate record")
      m=metrics[policy];m["n"]+=1;m["cost"]+=Q["costs"][act];m["unknown"]+=int(act=="UNKNOWN");m["repeat"]+=int(act=="REPEAT")
      m["correct"]+=int(metric_seed(seed,cid,act,1)<o["correct_probability"][act])
      m["decision_changed"]+=int(metric_seed(seed,cid,act,2)<o["decision_change_probability"][act])
    # Oracle is audit-only and may use declared true action effects.
    w=Q["decision_value_cost_weight"];oracle=max(Q["actions"],key=lambda a:(o["correct_probability"][a]-w*Q["costs"][a],-Q["actions"].index(a)))
    m=metrics["ORACLE_INTERVENTION"];m["n"]+=1;m["cost"]+=Q["costs"][oracle];m["unknown"]+=int(oracle=="UNKNOWN");m["repeat"]+=int(oracle=="REPEAT")
    m["correct"]+=int(metric_seed(seed,cid,oracle,1)<o["correct_probability"][oracle])
    m["decision_changed"]+=int(metric_seed(seed,cid,oracle,2)<o["decision_change_probability"][oracle])
for m in metrics.values():
  n=m["n"] or 1
  for k in ("correct","decision_changed","cost","unknown","repeat"):m[k]/=n
# Dependence and misspecification controls must abstain under DECOMPOSED.
for cid in ("correlated_duplicate","misspecified_decomposition"):
  ck(choose("DECOMPOSED",cases[cid])=="UNKNOWN","decomposition did not abstain on control "+cid)
source_accuracy=source_correct/source_n
h_gates={}
for comparator in ("TOTAL_UNCERTAINTY","DECISION_VALUE"):
  d=metrics["DECOMPOSED"];b=metrics[comparator]
  h_gates[comparator]={"correctness_matched":d["correct"]>=b["correct"]-Q["matched_correctness_tolerance"],"cost_reduced":d["cost"]<=b["cost"]-Q["minimum_cost_reduction"]}
result={"audit":"PASS_METHOD_SCOPED" if not errors else "FAIL_AUDIT","hypothesis":"H_HOLD_AUDIT_PENDING" if errors else "H_FAIL_NO_ADDED_DECISION_VALUE","rows_reconstructed":expected,"source_classifier_accuracy":source_accuracy,"metrics":metrics,"hypothesis_gates":h_gates,"errors":errors,"scope":"finite synthetic intervention-choice fixture only"}
if not errors and all(all(g.values()) for g in h_gates.values()) and source_accuracy>=Q["minimum_source_classifier_accuracy"]:
  result["hypothesis"]="H_PASS_SCOPED"
elif not errors and source_accuracy<Q["minimum_source_classifier_accuracy"]:
  result["hypothesis"]="H_FAIL_SOURCE_DECOMPOSITION_NOT_PREDICTIVE"
pathlib.Path(sys.argv[5]).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
print(json.dumps(result,sort_keys=True));sys.exit(0 if not errors else 1)
