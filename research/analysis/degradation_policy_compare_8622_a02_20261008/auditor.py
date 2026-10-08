"""Independent raw-spec reconstruction and audit."""
COMPONENTS={"planner":["planner_process","planner_backend"],"raw_observation":["capture_source","raw_adapter"],
"semantic_observation":["capture_source","shared_parser","semantic_scheduler"],"verifier":["capture_source","shared_parser","semantic_scheduler"],
"effect_confirmation":["effect_source","shared_parser","effect_process"],"telemetry":["event_loop","telemetry_sink"],
"authority":["authority_owner"],"release":["release_channel"]}
OPERATIONS=[
{"id":"inspect_raw","requires":["raw_observation","authority","release"],"evidence":["raw_fresh","raw_intact"],"source":"raw_observation","claim":"RAW_OBSERVED"},
{"id":"present_semantics","requires":["semantic_observation","verifier","authority","release"],"evidence":["semantic_fresh","semantic_intact"],"source":"semantic_observation","claim":"SEMANTIC_VERIFIED"},
{"id":"preview_plan","requires":["planner","semantic_observation","verifier","authority","release"],"evidence":["semantic_fresh","semantic_intact"],"source":"planner","claim":"PREVIEW_ONLY"},
{"id":"show_effect_receipt","requires":["effect_confirmation","verifier","authority","release"],"evidence":["effect_fresh","effect_intact"],"source":"effect_confirmation","claim":"EFFECT_VERIFIED"}]
CASE_IDS=["healthy","independent_telemetry_loss","common_capture_loss","common_semantic_scheduler_stall",
"common_parser_lineage_corruption","independent_effect_process_loss","stale_semantic_evidence","release_channel_loss",
"authority_owner_loss","unknown_semantic_dependency"]
ARMS={"independence_assuming_lookup","dependency_aware_contract","unknown_dependency_fail_closed"}
def _row(op):
 return {"operation":op["id"],"source":op["source"],"claim":op["claim"],"freshness":"CURRENT"}
def _supported(case,available):
 ev=case.get("evidence",{})
 return [_row(op) for op in OPERATIONS if all(available.get(x,False) for x in op["requires"])
         and all(ev.get(x) is True for x in op["evidence"])]
def _spec_errors(spec):
 if not isinstance(spec,dict) or spec.get("schema")!="8622-degradation-policy-spec-v1" or spec.get("version")!="policy-v1": return ["spec_identity"]
 err=[]
 if spec.get("components")!=COMPONENTS: err.append("component_graph")
 if spec.get("operations")!=OPERATIONS: err.append("operation_contracts")
 ss=spec.get("scenarios")
 if not isinstance(ss,list) or [x.get("id") for x in ss if isinstance(x,dict)]!=CASE_IDS: err.append("scenario_identity_or_order")
 services=set(COMPONENTS)
 for c in ss if isinstance(ss,list) else []:
  if not isinstance(c,dict): err.append("scenario_type"); continue
  for f in ("failed_dependencies","corrupted_dependencies","unknown_services","naive_unavailable_services"):
   if not isinstance(c.get(f),list) or any(not isinstance(x,str) for x in c.get(f,[])): err.append(c["id"]+":"+f)
  if not set(c.get("unknown_services",[])).issubset(services): err.append(c["id"]+":unknown_service")
  if not set(c.get("naive_unavailable_services",[])).issubset(services): err.append(c["id"]+":naive_service")
  if not isinstance(c.get("evidence"),dict): err.append(c["id"]+":evidence")
 return err
def audit(spec,candidate):
 err=_spec_errors(spec)
 if not isinstance(candidate,dict) or set(candidate)!={"schema","cases"} or candidate.get("schema")!="8622-candidate-v1":
  return {"schema":"8622-audit-v1","audit_integrity":"FAIL","errors":err+["candidate_schema"],"cases_reconstructed":0,
  "independence_overclaim_cases":0,"independence_overclaim_operations":0,"dependency_aware_unsupported_operations":0,
  "unknown_fail_closed_cases":0,"unknown_fail_closed_admitted_operations":0,"mandatory_release_obligations_verified":0,"dispatches":0}
 rows=candidate.get("cases")
 if not isinstance(rows,list) or len(rows)!=len(CASE_IDS): err.append("candidate_denominator"); rows=rows if isinstance(rows,list) else []
 actual={}
 for r in rows:
  if not isinstance(r,dict) or not isinstance(r.get("case_id"),str) or r["case_id"] in actual: err.append("candidate_case_identity"); continue
  actual[r["case_id"]]=r
 oc=oo=sm=uc=ua=rel=0
 for c in spec.get("scenarios",[]) if isinstance(spec,dict) else []:
  if not isinstance(c,dict) or c.get("id") not in CASE_IDS: continue
  cid=c["id"]; r=actual.get(cid)
  if r is None: err.append(cid+":missing"); continue
  if set(r)!={"case_id","arms","release_obligation"}: err.append(cid+":fields")
  arms=r.get("arms")
  if not isinstance(arms,dict) or set(arms)!=ARMS: err.append(cid+":arms"); arms=arms if isinstance(arms,dict) else {}
  lost=set(c.get("failed_dependencies",[]))|set(c.get("corrupted_dependencies",[]))
  unknown=set(c.get("unknown_services",[]))
  dep={s:s not in unknown and not bool(set(ds)&lost) for s,ds in COMPONENTS.items()}
  ind={s:s not in set(c.get("naive_unavailable_services",[])) for s in COMPONENTS}
  closed=({s:False for s in COMPONENTS} if unknown else dep)
  expected={"independence_assuming_lookup":_supported(c,ind),"dependency_aware_contract":_supported(c,dep),
  "unknown_dependency_fail_closed":_supported(c,closed)}
  for arm,want in expected.items():
   if arms.get(arm)!=want: err.append(cid+":"+arm)
  extra=[x for x in expected["independence_assuming_lookup"] if x not in expected["dependency_aware_contract"]]
  if extra: oc+=1; oo+=len(extra)
  if arms.get("dependency_aware_contract")!=expected["dependency_aware_contract"]: sm+=1
  if unknown:
   uc+=1
   val=arms.get("unknown_dependency_fail_closed",[])
   if val!=[]: ua+=len(val) if isinstance(val,list) else 1
  if r.get("release_obligation")=="MANDATORY_RELEASE": rel+=1
  else: err.append(cid+":release")
  for rs in arms.values():
   if isinstance(rs,list) and any(isinstance(x,dict) and x.get("operation")=="dispatch_action" for x in rs): err.append(cid+":dispatch")
 if set(actual)!=set(CASE_IDS): err.append("case_coverage")
 if oc<1: err.append("no_overclaim")
 if oo!=6: err.append("overclaim_count")
 if sm: err.append("safe_contract_mismatch")
 if uc!=1 or ua: err.append("unknown_fail_closed")
 if rel!=len(CASE_IDS): err.append("release_coverage")
 err=sorted(set(err)); ok=not err
 return {"schema":"8622-audit-v1","audit_integrity":"PASS" if ok else "FAIL","status":"PASS_METHOD_SCOPED" if ok else "FAIL_METHOD",
 "errors":err,"cases_reconstructed":len(actual),"independence_overclaim_cases":oc,"independence_overclaim_operations":oo,
 "dependency_aware_unsupported_operations":sm,"unknown_fail_closed_cases":uc,"unknown_fail_closed_admitted_operations":ua,
 "mandatory_release_obligations_verified":rel,"dispatches":0}
