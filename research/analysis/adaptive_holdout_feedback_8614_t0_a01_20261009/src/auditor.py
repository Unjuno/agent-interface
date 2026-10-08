#!/usr/bin/env python3
"""Independent reconstruction of adaptive feedback, selection, lockbox and gates."""
import json, math, pathlib, random, statistics, sys
P=json.loads(pathlib.Path(sys.argv[1]).read_text()); Q=P["protocol"]; R=json.loads(pathlib.Path(sys.argv[2]).read_text()); errors=[]
def ck(ok,msg):
    if not ok: errors.append(msg)
def sm(seed,fam,tag,var=0): return (seed*1000003+fam*9176+tag*65537+var*104729+0x6A09E667)&0xffffffff
def validation_cohort(seed,fam):
    rr=random.Random(sm(seed,fam,11)); shared=[rr.uniform(-Q["shared_case_halfwidth"],Q["shared_case_halfwidth"]) for _ in range(Q["validation_cases"])]; allv=[]
    for j in range(Q["candidate_variants"]):
        eff=Q["true_effect"] if fam==1 and j==0 else 0.0; r=random.Random(sm(seed,fam,19,j))
        allv.append([Q["baseline_mean"]+eff+shared[i]+r.uniform(-Q["candidate_case_halfwidth"],Q["candidate_case_halfwidth"]) for i in range(Q["validation_cases"])])
    return allv
def confirm_cohort(seed,fam,j):
    rr=random.Random(sm(seed,fam,31)); sh=[rr.uniform(-Q["shared_case_halfwidth"],Q["shared_case_halfwidth"]) for _ in range(Q["confirmatory_cases"])]; eff=Q["true_effect"] if fam==1 and j==0 else 0.0; r=random.Random(sm(seed,fam,37,j))
    return [Q["baseline_mean"]+eff+sh[i]+r.uniform(-Q["candidate_case_halfwidth"],Q["candidate_case_halfwidth"]) for i in range(Q["confirmatory_cases"])]
def avg(xs): return sum(xs)/len(xs)
def std_error(xs): return statistics.stdev(xs)/math.sqrt(len(xs))
def code_for(pol,response):
    if pol=="FULL_RELEASE": return sum((i+1)*int(round(v*1000000)) for i,v in enumerate(response["case_values"]))&0xffffffff
    value=response["mean"] if pol=="AGGREGATE_RELEASE" else response["bounded_answer"]
    return int(round(value*1000000))&0xffffffff
def proposal(state,code,used,k):
    state=(state*1664525+code+1013904223)&0xffffffff; candidate=1+(state%(k-1))
    while candidate in used: candidate=1+(candidate%(k-1))
    return candidate,state

def audit_one(seed,fam,policy,rounds,validation,got):
    ck(got.get("policy")==policy and got.get("rounds")==rounds, "policy/horizon identity")
    trace=got.get("audit_trace",[]); visible=got.get("selector_transcript",[])
    ck(len(trace)==rounds and len(visible)==rounds,"query row count")
    used=set(); state=(seed^(fam*0x9E3779B9)^(sum(ord(c) for c in policy)*2654435761)^rounds)&0xffffffff; noise=random.Random(sm(seed,fam,53,rounds)); current=0; winner=None
    for t,(row,view) in enumerate(zip(trace,visible)):
        ck(row.get("turn")==t+1 and row.get("variant")==current,"adaptive proposal/sequence")
        ck(view.get("turn")==t+1 and view.get("variant")==current,"selector transcript identity")
        ck(set(view)=={"turn","variant","released"},"audit-only fields entered selector transcript")
        ck(current not in used,"candidate repeated");used.add(current); values=validation[current]; truth=avg(values); ck(abs(row.get("validation_mean_truth",1e9)-truth)<1e-12,"validation reconstruction")
        response=view.get("released",{})
        if policy=="FULL_RELEASE":
            ck(response=={"case_values":values},"full-release vector")
            ck(row.get("released_case_values")==values,"full-release audit copy")
            score=avg(response["case_values"])
        elif policy=="AGGREGATE_RELEASE":
            ck(set(response)=={"mean","se"},"aggregate selector channel fields")
            ck(abs(response.get("mean",1e9)-truth)<1e-12,"aggregate mean")
            ck(abs(response.get("se",1e9)-std_error(values))<1e-12,"aggregate uncertainty")
            ck(abs(row.get("released_mean",1e9)-truth)<1e-12,"aggregate audit mean")
            ck(abs(row.get("released_se",1e9)-std_error(values))<1e-12,"aggregate audit uncertainty")
            ck("released_case_values" not in row,"case data leaked to aggregate arm")
            score=response["mean"]
        else:
            draw=noise.gauss(0.0,Q["reusable_noise_sigma"]); bounded=min(Q["reusable_answer_bounds"][1],max(Q["reusable_answer_bounds"][0],truth+draw))
            ck(set(view.get("released",{}))=={"bounded_answer"},"reusable selector channel fields")
            ck(abs(view.get("released",{}).get("bounded_answer",1e9)-bounded)<1e-12,"bounded selector answer")
            ck(abs(row.get("noise_draw",1e9)-draw)<1e-12,"bounded-answer audit noise draw")
            ck(abs(row.get("released_bounded_answer",1e9)-bounded)<1e-12,"bounded audit answer")
            ck("released_case_values" not in row and "released_mean" not in row,"reusable channel leaked detailed metric")
            response=view.get("released",{}); score=response["bounded_answer"]
        ck(abs(row.get("selector_score",1e9)-score)<1e-12,"selector-visible score")
        c=code_for(policy,response);ck(row.get("feedback_code")==c,"feedback encoding")
        if winner is None or score>winner["score"]: winner={"variant":current,"score":score,"validation":truth}
        if t+1<rounds:
            nxt,state=proposal(state,c,used,Q["candidate_variants"]);ck(row.get("next_variant")==nxt,"next candidate not adapted from released result");current=nxt
    selected=winner["variant"] if winner else 0
    ck(got.get("selected_variant")==selected,"selected winner")
    ck(abs(got.get("selected_validation_mean",1e9)-winner["validation"])<1e-12,"selected validation score")
    pop=Q["baseline_mean"]+(Q["true_effect"] if fam==1 and selected==0 else 0.0)
    ck(abs(got.get("selected_population_mean",1e9)-pop)<1e-12,"population mean")
    confirm=confirm_cohort(seed,fam,selected);ck(got.get("confirmatory_scores_after_selection")==confirm,"untouched confirmatory raw")
    ck(got.get("lockbox_opened_after_selection") is True,"lockbox ordering receipt")
    ck(got.get("hard_gates")==Q["safety_gates"],"exact hard gate result")
    ck(got.get("query_count")==rounds and rounds<=Q["query_composition_budget"],"query budget")
    expected_units=rounds if policy=="REUSABLE_HOLDOUT" else 0
    ck(got.get("composition_units")==expected_units and got.get("composition_budget")==Q["query_composition_budget"],"composition accounting")
    expected_state="EXHAUSTED" if rounds==Q["query_composition_budget"] else "AVAILABLE"
    ck(got.get("budget_state")==expected_state,"budget terminal state")

def median(xs):
    a=sorted(xs);n=len(a);return (a[(n-1)//2]+a[n//2])/2 if n else 0.0
def metrics(family,policy,rounds):
    rows=[x["evaluation"] for x in R["runs"] if x["family"]==family and x["evaluation"]["policy"]==policy and x["evaluation"]["rounds"]==rounds]
    opt=[x["selected_validation_mean"]-x["selected_population_mean"] for x in rows]
    false=[x["selected_validation_mean"]>Q["baseline_mean"]+Q["false_superiority_margin"] for x in rows] if family=="null" else []
    power=[]
    if family=="planted":
      for x in rows:
        y=x["confirmatory_scores_after_selection"]; m=avg(y); low=m-Q["confirmatory_confidence_z"]*std_error(y)
        power.append(x["selected_variant"]==0 and low>Q["baseline_mean"])
    return {"n":len(rows),"median_optimism":median(opt),"mean_optimism":avg(opt),"false_superiority_rate":avg([float(z) for z in false]) if false else None,"planted_discovery_power":avg([float(z) for z in power]) if power else None}

famcode={"null":0,"planted":1}; by={(x["family"],x["seed"],x["evaluation"]["policy"],x["evaluation"]["rounds"]):x["evaluation"] for x in R["runs"]}
expected_count=len(P["replicate_seeds"])*2*(3*len(Q["rounds"])+1);ck(R.get("run_count")==expected_count and len(R.get("runs",[]))==expected_count,"run count")
for family,fam in famcode.items():
  for seed in P["replicate_seeds"]:
    v=validation_cohort(seed,fam)
    for rounds in Q["rounds"]:
      for policy in ("FULL_RELEASE","AGGREGATE_RELEASE","REUSABLE_HOLDOUT"):
        row=by.get((family,seed,policy,rounds),{});audit_one(seed,fam,policy,rounds,v,row)
    lock=by.get((family,seed,"ONE_SHOT_LOCKBOX",0),{}); c=confirm_cohort(seed,fam,0)
    ck(lock.get("selected_variant")==0 and lock.get("query_count")==0 and lock.get("selector_transcript")==[] and lock.get("audit_trace")==[],"one-shot lockbox selection/query")
    ck(lock.get("confirmatory_scores_after_selection")==c and lock.get("lockbox_opened_after_selection") is True,"lockbox confirmatory cohort")
    ck(lock.get("hard_gates")==Q["safety_gates"] and lock.get("budget_state")=="NOT_USED","lockbox hard gates/state")
ck(R.get("budget_probe")=={"attempted_turn":Q["query_composition_budget"]+1,"budget_state":"STOP_EXHAUSTED","candidate_proposed":False},"post-budget stop probe")
summary={}
for family in famcode:
  summary[family]={}
  for policy in ("FULL_RELEASE","AGGREGATE_RELEASE","REUSABLE_HOLDOUT"):
    summary[family][policy]={str(q):metrics(family,policy,q) for q in Q["rounds"]}
# Preregistered null-family holdout utility at the maximum query horizon.
qmax=Q["query_composition_budget"]; full=summary["null"]["FULL_RELEASE"][str(qmax)]; agg=summary["null"]["AGGREGATE_RELEASE"][str(qmax)]; reuse=summary["null"]["REUSABLE_HOLDOUT"][str(qmax)]
ck(summary["null"]["FULL_RELEASE"][str(Q["rounds"][0])]["median_optimism"]<full["median_optimism"],"full-release optimism did not grow with rounds")
ck(reuse["median_optimism"]<=full["median_optimism"]*(1-Q["required_reusable_optimism_fractional_reduction"]),"reusable holdout optimism reduction vs full missed")
ck(reuse["median_optimism"]<=agg["median_optimism"]*(1-Q["required_reusable_optimism_fractional_reduction"]),"reusable holdout optimism reduction vs aggregate missed")
ck(reuse["false_superiority_rate"]<full["false_superiority_rate"],"reusable false-superiority rate not below full")
plant_full=summary["planted"]["FULL_RELEASE"][str(qmax)]["planted_discovery_power"];plant_reuse=summary["planted"]["REUSABLE_HOLDOUT"][str(qmax)]["planted_discovery_power"]
ck(plant_reuse>=Q["minimum_reusable_planted_power"],"reusable planted-effect power below floor")
ck(plant_reuse>=plant_full-Q["maximum_planted_power_loss"],"reusable planted-effect power loss exceeds bound")
lock_rows=[x["evaluation"] for x in R["runs"] if x["family"]=="null" and x["evaluation"]["policy"]=="ONE_SHOT_LOCKBOX"]
covered=0
for x in lock_rows:
  y=x["confirmatory_scores_after_selection"];m=avg(y); margin=Q["confirmatory_confidence_z"]*std_error(y);covered+=int(margin>=abs(m-Q["baseline_mean"]))
coverage=covered/len(lock_rows);ck(Q["lockbox_null_coverage_bounds"][0]<=coverage<=Q["lockbox_null_coverage_bounds"][1],"one-shot lockbox interval coverage outside frozen bounds")
result={"audit":"PASS_ADAPTIVE_FEEDBACK_METHOD_SCOPED" if not errors else "FAIL_METHOD","runs_reconstructed":expected_count,"replicates_per_family":len(P["replicate_seeds"]),"metrics":summary,"one_shot_null_lockbox_95pct_coverage":coverage,"budget_probe_rejected":R.get("budget_probe",{}).get("candidate_proposed") is False,"errors":errors,"scope":"synthetic adaptive-selector method only; no repository benchmark bias inference"}
pathlib.Path(sys.argv[3]).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n");print(json.dumps(result,sort_keys=True));sys.exit(0 if not errors else 1)
