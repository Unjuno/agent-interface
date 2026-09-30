"""Pre-run independent graph-based auditor; does not import causal_core."""
import json,sys
PROCS=("A","B")
def evt(i,p,n,k,vc,parents=(),mid=None,digest=None):
 return {"id":i,"process":p,"seq":n,"kind":k,"vc":dict(vc),"parents":list(parents),"message":mid,"digest":digest,"freshness_age":1}
def fixtures():
 return {"cross_ack":[evt("a1","A",1,"SEND",{"A":1,"B":0},mid="m1",digest="d1"),evt("a2","A",2,"RECEIVE",{"A":2,"B":3},("a1","b3"),"m2","d2"),evt("b1","B",1,"LOCAL_OBSERVATION",{"A":0,"B":1}),evt("b2","B",2,"RECEIVE",{"A":1,"B":2},("b1","a1"),"m1","d1"),evt("b3","B",3,"SEND",{"A":1,"B":3},("b2",),"m2","d2")],
 "reordered_delivery":[evt("a1","A",1,"SEND",{"A":1,"B":0},mid="m1",digest="d1"),evt("a2","A",2,"SEND",{"A":2,"B":0},("a1",),"m2","d2"),evt("b1","B",1,"RECEIVE",{"A":2,"B":1},("a1","a2"),"m2","d2"),evt("b2","B",2,"RECEIVE",{"A":2,"B":2},("b1","a1"),"m1","d1")],
 "independent_concurrent":[evt("a1","A",1,"LOCAL_OBSERVATION",{"A":1,"B":0}),evt("b1","B",1,"LOCAL_RECEIPT",{"A":0,"B":1})]}
def prefix(events,cut):return [e for e in events if e["seq"]<=cut[e["process"]]]
def oracle(events,cut,channels=None,meta=True):
 channels=channels or {}
 if not meta:return "UNKNOWN"
 selected=prefix(events,cut)
 if not selected:return "UNKNOWN"
 ids={e["id"] for e in selected};allids={e["id"] for e in events};parents={e["id"]:e["parents"] for e in events}
 if any(p not in allids for ps in parents.values() for p in ps):return "CONTRADICTORY"
 for e in selected:
  if any(p not in ids for p in parents[e["id"]]):return "INCOMPLETE_IN_FLIGHT"
 done={}
 def derive(eid,stack):
  if eid in done:return done[eid]
  if eid in stack or eid not in {x["id"] for x in events}:return None
  e=next(x for x in events if x["id"]==eid);stack=stack|{eid};vals=[derive(p,stack) for p in e["parents"]]
  if any(x is None for x in vals):return None
  c={p:max([v[p] for v in vals],default=0) for p in PROCS};c[e["process"]]+=1;done[eid]=c;return c
 if any(derive(e["id"],set())!=e["vc"] for e in events):return "CONTRADICTORY"
 if any(e["vc"][p]>cut[p] for e in selected for p in PROCS):return "INCOMPLETE_IN_FLIGHT"
 sends={e["message"]:e for e in selected if e["kind"]=="SEND"};recvs={}
 for e in selected:
  if e["kind"]=="RECEIVE":recvs.setdefault(e["message"],[]).append(e["digest"])
 if any(len(set(v))>1 for v in recvs.values()):return "CONTRADICTORY"
 if any(mid not in recvs for mid in sends):
  if any(channels.get(mid)=="DELIVERED" for mid in sends if mid not in recvs):return "CONTRADICTORY"
  return "INCOMPLETE_IN_FLIGHT"
 if any(mid not in sends for mid in recvs):return "INCOMPLETE_IN_FLIGHT"
 return "CONSISTENT"
def row(name,events,cut,channels,meta=True):
 selected=prefix(events,cut);d=oracle(events,cut,channels,meta);streams={e["process"] for e in selected}
 return {"case":name,"cut":cut,"selected_event_ids":[e["id"] for e in selected],"unique_received_message_ids":sorted({e["message"] for e in selected if e["kind"]=="RECEIVE"}),"per_record_freshness_admits":bool(selected) and all(e["freshness_age"]<=2 for e in selected),"decision":d,"certified_cross_source_claim":d=="CONSISTENT" and len(streams)>=2,"channel_states":channels,"metadata_complete":meta}
def expected_raw():
 rows=[]
 for name,events in fixtures().items():
  high={p:max([e["seq"] for e in events if e["process"]==p],default=0) for p in PROCS}
  for a in range(high["A"]+1):
   for b in range(high["B"]+1):rows.append(row(name,events,{"A":a,"B":b},{}))
 cross=fixtures()["cross_ack"]
 rows.extend([row("channel_in_flight_control",cross,{"A":1,"B":1},{"m1":"IN_FLIGHT"}),row("dropped_ack_control",cross,{"A":1,"B":1},{"m1":"DROPPED"}),row("missing_channel_control",cross,{"A":1,"B":1},{}),row("missing_metadata_control",cross,{"A":1,"B":1},{},False)])
 same=[evt("a1","A",1,"SEND",{"A":1,"B":0},mid="m1",digest="d1"),evt("b1","B",1,"RECEIVE",{"A":1,"B":1},("a1",),"m1","d1"),evt("b2","B",2,"RECEIVE",{"A":1,"B":2},("b1",),"m1","d1")]
 bad=[evt("a1","A",1,"SEND",{"A":1,"B":0},mid="m1",digest="d1"),evt("b1","B",1,"RECEIVE",{"A":1,"B":1},("a1",),"m1","d1"),evt("b2","B",2,"RECEIVE",{"A":1,"B":2},("b1",),"m1","different")]
 rows.extend([row("identical_duplicate_delivery",same,{"A":1,"B":2},{}),row("conflicting_duplicate_delivery",bad,{"A":1,"B":2},{})])
 return {"schema":"causal-cut-5348-t1-raw-v1","allocation":"causal-cut-5348-t1-20260930-01","source_identity":{"core_git_blob_sha":EXPECTED_CORE_SHA},"model":"finite deterministic two-stream event DAG; all timestamps synthetic; all records locally fresh","counts":{"rows":len(rows),"topology_prefix_cuts":25,"control_rows":6,"per_record_freshness_admissions":sum(r["per_record_freshness_admits"] for r in rows),"certified_cross_source_claims":sum(r["certified_cross_source_claim"] for r in rows),"candidate_nonconsistent_admissions":0},"rows":rows,"side_effects":{"authority_grants":0,"actions_dispatched":0,"network_calls":0,"model_calls":0,"gpu_calls":0}}
def audit(raw):
 errors=[]
 if raw!=expected_raw():errors.append("raw_reconstruction_mismatch")
 if raw.get("source_identity",{}).get("core_git_blob_sha")!=EXPECTED_CORE_SHA:errors.append("core_source_identity")
 if raw.get("side_effects")!={"authority_grants":0,"actions_dispatched":0,"network_calls":0,"model_calls":0,"gpu_calls":0}:errors.append("side_effects")
 result={"schema":"causal-cut-5348-t1-audit-v1","errors":errors,"integrity_pass":not errors,"cut_rows_recomputed":25,"control_rows_recomputed":6,"candidate_imported":False}
 print(json.dumps(result,sort_keys=True,separators=(",",":")));return 0 if not errors else 1
EXPECTED_CORE_SHA="d26f28200ff6c50b60d8984978ad14431df67470"
if __name__=="__main__":raise SystemExit(audit(json.loads(sys.stdin.read())))
