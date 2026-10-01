import hashlib,json,sys
DECK={"localize_target","abstain_no_target","action_schema","temporal_cue","negative_control"}
EXPECTED={"stationary_noise":"NO_SHIFT_DETECTED_IN_DECK","in_deck_behavior_shift":"HOLD_MODEL_STABILITY","out_of_deck_shift":"UNKNOWN_COVERAGE","schema_only_break":"HOLD_SCHEMA_BREAK","prompt_context_drift":"HOLD_PROMPT_CONTEXT_DRIFT","within_block_model_switch":"HOLD_MODEL_STABILITY"}

def rate(rows,case,phase,probe):
 xs=[r["correct"] for r in rows if r["case"]==case and r["phase"]==phase and (r["probe"] in DECK if probe=="__DECK__" else r["probe"]==probe) and r["correct"] is not None]
 return sum(xs)/len(xs) if xs else None
def route_rate(rows,case,arm,episode=None):
 xs=[r["correct"] for r in rows if r["case"]==case and r["probe"]=="route_task" and r["route"]==arm and (episode is None or r["episode"]==episode) and r["correct"] is not None]
 return sum(xs)/len(xs) if xs else None
def classify(rows,case,episode=0):
 xs=[r for r in rows if r["case"]==case and r["episode"]==episode]
 if case=="schema_only_break": return "HOLD_SCHEMA_BREAK" if any(r.get("schema_ok") is False for r in xs) else "FAIL_METHOD"
 if case=="prompt_context_drift":
  h={r["route"]:r["prompt_hash"] for r in xs if r["probe"]=="route_task"}
  if h.get("A")!=h.get("B"): return "HOLD_PROMPT_CONTEXT_DRIFT"
 if case=="out_of_deck_shift":
  deck_delta=rate(rows,case,"pre","__DECK__")-rate(rows,case,"post","__DECK__")
  task_delta=rate(rows,case,"pre","route_task")-rate(rows,case,"post","route_task")
  return "UNKNOWN_COVERAGE" if abs(deck_delta)<.2 and abs(task_delta)>=.2 and any(r["probe"]=="out_of_deck" for r in xs) else "FAIL_METHOD"
 if case=="within_block_model_switch":
  d=rate(rows,case,"pre","__DECK__")-rate(rows,case,"mid","__DECK__")
  return "HOLD_MODEL_STABILITY" if d>=.2 else "FAIL_METHOD"
 d=rate(rows,case,"pre","__DECK__")-rate(rows,case,"post","__DECK__")
 if case=="stationary_noise": return "NO_SHIFT_DETECTED_IN_DECK" if abs(d)<.2 else "FAIL_METHOD"
 return "HOLD_MODEL_STABILITY" if d>=.2 else "FAIL_METHOD"
def main(path):
 raw=open(path,"rb").read(); rows=[json.loads(x) for x in raw.splitlines()]
 errs=[]
 keys=[(r.get("case"),r.get("episode"),r.get("phase"),r.get("probe"),r.get("route"),r.get("attempt")) for r in rows]
 if len(keys)!=len(set(keys)): errs.append("duplicate-row")
 if any(r.get("alias")!="fixed-v1" or r.get("model_fingerprint")!="opaque-fixed-v1" or r.get("metadata")!="fixed-v1" for r in rows): errs.append("identity-metadata-drift")
 null_eps=sorted({r["episode"] for r in rows if r["case"]=="stationary_noise"})
 null_flags=[classify(rows,"stationary_noise",ep)!="NO_SHIFT_DETECTED_IN_DECK" for ep in null_eps]
 false_rate=sum(null_flags)/len(null_flags) if null_flags else 1.0
 # Wilson upper confidence bound; this is finite-fixture evidence, not
 # a provider-wide false-alarm guarantee.
 z=1.96; n=len(null_flags); phat=false_rate
 denom=1+z*z/n if n else 1
 wilson_upper=(phat+z*z/(2*n)+z*((phat*(1-phat)/n+z*z/(4*n*n))**.5))/denom if n else 1.0
 if wilson_upper>.05: errs.append("stationary-false-alarm-upper-bound")
 actual={c:(("NO_SHIFT_DETECTED_IN_DECK" if false_rate<=.05 else "FAIL_METHOD") if c=="stationary_noise" else classify(rows,c)) for c in sorted(EXPECTED)}
 # Demonstrate the exact false-attribution counterexample: same alias and metadata,
 # but a temporal task shift makes a naive A-before/B-after comparison look causal.
 a=route_rate(rows,"in_deck_behavior_shift","A",0)
 b=route_rate(rows,"in_deck_behavior_shift","B",0)
 alias_only="FALSE_ROUTE_EFFECT_PROMOTED" if a-b>=.2 else "NO_FALSE_PROMOTION"
 metadata_only="FALSE_ROUTE_EFFECT_PROMOTED" if a-b>=.2 and all(r["metadata"]=="fixed-v1" for r in rows if r["case"]=="in_deck_behavior_shift") else "NO_FALSE_PROMOTION"
 if alias_only!="FALSE_ROUTE_EFFECT_PROMOTED" or metadata_only!="FALSE_ROUTE_EFFECT_PROMOTED": errs.append("baseline-counterexample-missing")
 order_rows=[r for r in rows if r["case"]=="in_deck_behavior_shift" and r["probe"]=="route_task"]
 orders={r["episode"]:r.get("order") for r in order_rows}
 balanced_delta=route_rate(rows,"in_deck_behavior_shift","A")-route_rate(rows,"in_deck_behavior_shift","B")
 balanced="NO_FALSE_PROMOTION_AFTER_AB_BA_BALANCE" if orders.get(0)=="AB" and orders.get(1)=="BA" and abs(balanced_delta)<.2 else "FAIL_ORDER_BALANCE"
 if balanced!="NO_FALSE_PROMOTION_AFTER_AB_BA_BALANCE": errs.append("order-balance-counterexample")
 if actual!={k:EXPECTED[k] for k in sorted(EXPECTED)}: errs.append("classification-mismatch")
 if not any(r.get("schema_ok") is False for r in rows): errs.append("schema-control-missing")
 print(json.dumps({"status":"PASS_METHOD_SCOPED" if not errs else "FAIL_METHOD","rows":len(rows),"raw_sha256":hashlib.sha256(raw).hexdigest(),"classifications":actual,"alias_only_unbalanced_AB":alias_only,"metadata_only_unbalanced_AB":metadata_only,"order_balanced_AB_BA":balanced,"balanced_route_difference":balanced_delta,"bracketed_canary":"REFUSE_FALSE_ROUTE_EFFECT" if actual.get("in_deck_behavior_shift")=="HOLD_MODEL_STABILITY" else "FAIL","stationary_null_replicates":n,"stationary_false_alarms":sum(null_flags),"stationary_false_alarm_fraction":false_rate,"stationary_false_alarm_wilson_upper_95":wilson_upper,"errors":errs},sort_keys=True))
 if errs: raise SystemExit(1)
if __name__=="__main__": main(sys.argv[1])
