"""Candidate causal-cut certificate for a tiny asynchronous evidence corpus."""
import itertools
PROCESSES=("A","B")
FRESH_AGE=1
MAX_FRESH_AGE=2
def _e(eid,p,seq,kind,vc,parents=(),message=None,digest=None):
 return {"id":eid,"process":p,"seq":seq,"kind":kind,"vc":dict(vc),"parents":list(parents),"message":message,"digest":digest,"freshness_age":FRESH_AGE}
def topologies():
 cross=[_e("a1","A",1,"SEND",{"A":1,"B":0},message="m1",digest="d1"),_e("a2","A",2,"RECEIVE",{"A":2,"B":3},["a1","b3"],"m2","d2"),_e("b1","B",1,"LOCAL_OBSERVATION",{"A":0,"B":1}),_e("b2","B",2,"RECEIVE",{"A":1,"B":2},["b1","a1"],"m1","d1"),_e("b3","B",3,"SEND",{"A":1,"B":3},["b2"],"m2","d2")]
 reorder=[_e("a1","A",1,"SEND",{"A":1,"B":0},message="m1",digest="d1"),_e("a2","A",2,"SEND",{"A":2,"B":0},["a1"],"m2","d2"),_e("b1","B",1,"RECEIVE",{"A":2,"B":1},["a1","a2"],"m2","d2"),_e("b2","B",2,"RECEIVE",{"A":2,"B":2},["b1","a1"],"m1","d1")]
 independent=[_e("a1","A",1,"LOCAL_OBSERVATION",{"A":1,"B":0}),_e("b1","B",1,"LOCAL_RECEIPT",{"A":0,"B":1})]
 return {"cross_ack":cross,"reordered_delivery":reorder,"independent_concurrent":independent}
def valid_vector_metadata(events):
 by={e["id"]:e for e in events};memo={}
 def derive(eid,visiting):
  if eid in memo:return memo[eid]
  if eid in visiting or eid not in by:return None
  e=by[eid];visiting=visiting|{eid};parents=[derive(p,visiting) for p in e["parents"]]
  if any(v is None for v in parents):return None
  clock={p:max([v[p] for v in parents],default=0) for p in PROCESSES};clock[e["process"]]+=1;memo[eid]=clock;return clock
 return all(derive(e["id"],set())==e["vc"] for e in events)
def selected_events(events,cut):return [e for e in events if e["seq"]<=cut[e["process"]]]
def classify(events,cut,channel_states=None,metadata_complete=True):
 channel_states=channel_states or {}
 if not metadata_complete:return "UNKNOWN"
 selected=selected_events(events,cut)
 if not selected:return "UNKNOWN"
 ids={e["id"] for e in selected}
 if not valid_vector_metadata(events):return "CONTRADICTORY"
 for e in selected:
  if any(parent not in ids for parent in e["parents"]):return "INCOMPLETE_IN_FLIGHT"
  if any(e["vc"][p]>cut[p] for p in PROCESSES):return "INCOMPLETE_IN_FLIGHT"
 receives={};sends={}
 for e in selected:
  if e["kind"]=="SEND":sends[e["message"]]=e
  if e["kind"]=="RECEIVE":receives.setdefault(e["message"],[]).append(e["digest"])
 if any(len(set(ds))>1 for ds in receives.values()):return "CONTRADICTORY"
 for mid in sends:
  if mid not in receives:
   if channel_states.get(mid)=="DELIVERED":return "CONTRADICTORY"
   return "INCOMPLETE_IN_FLIGHT"
 for mid in receives:
  if mid not in sends:return "INCOMPLETE_IN_FLIGHT"
 return "CONSISTENT"
def decision_row(name,events,cut,channel_states=None,metadata_complete=True):
 selected=selected_events(events,cut);fresh=bool(selected) and all(e["freshness_age"]<=MAX_FRESH_AGE for e in selected);decision=classify(events,cut,channel_states,metadata_complete);streams={e["process"] for e in selected}
 return {"case":name,"cut":dict(cut),"selected_event_ids":[e["id"] for e in selected],"per_record_freshness_admits":fresh,"decision":decision,"certified_cross_source_claim":decision=="CONSISTENT" and len(streams)>=2,"channel_states":channel_states or {},"metadata_complete":metadata_complete}
def build_raw():
 rows=[]
 for name,events in topologies().items():
  maxima={p:max([e["seq"] for e in events if e["process"]==p],default=0) for p in PROCESSES}
  for a in range(maxima["A"]+1):
   for b in range(maxima["B"]+1):rows.append(decision_row(name,events,{"A":a,"B":b}))
 cross=topologies()["cross_ack"]
 rows.extend([decision_row("channel_in_flight_control",cross,{"A":1,"B":1},{"m1":"IN_FLIGHT"}),decision_row("dropped_ack_control",cross,{"A":1,"B":1},{"m1":"DROPPED"}),decision_row("missing_channel_control",cross,{"A":1,"B":1},{}),decision_row("missing_metadata_control",cross,{"A":1,"B":1},{},False)])
 duplicate=[_e("a1","A",1,"SEND",{"A":1,"B":0},message="m1",digest="d1"),_e("b1","B",1,"RECEIVE",{"A":1,"B":1},["a1"],"m1","d1"),_e("b2","B",2,"RECEIVE",{"A":1,"B":2},["b1"],"m1","d1")]
 conflict=[_e("a1","A",1,"SEND",{"A":1,"B":0},message="m1",digest="d1"),_e("b1","B",1,"RECEIVE",{"A":1,"B":1},["a1"],"m1","d1"),_e("b2","B",2,"RECEIVE",{"A":1,"B":2},["b1"],"m1","different")]
 rows.extend([decision_row("identical_duplicate_delivery",duplicate,{"A":1,"B":2}),decision_row("conflicting_duplicate_delivery",conflict,{"A":1,"B":2})])
 return {"schema":"causal-cut-5348-t1-raw-v1","allocation":"causal-cut-5348-t1-20260930-01","source_identity":{"core_git_blob_sha":"PENDING"},"model":"finite deterministic two-stream event DAG; all timestamps synthetic; all records locally fresh","counts":{"rows":len(rows),"topology_prefix_cuts":25,"control_rows":6,"per_record_freshness_admissions":sum(r["per_record_freshness_admits"] for r in rows),"certified_cross_source_claims":sum(r["certified_cross_source_claim"] for r in rows),"candidate_nonconsistent_admissions":sum(r["certified_cross_source_claim"] and r["decision"]!="CONSISTENT" for r in rows)},"rows":rows,"side_effects":{"authority_grants":0,"actions_dispatched":0,"network_calls":0,"model_calls":0,"gpu_calls":0}}
