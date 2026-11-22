from __future__ import annotations
import hashlib, importlib.util, json
from pathlib import Path
HERE=Path(__file__).resolve().parent
SRC=HERE/"SOURCE"
class AuditFailure(ValueError): pass
def need(ok,message):
    if not ok: raise AuditFailure(message)
def nat(v): return type(v) is int and v>=0
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    need(spec is not None and spec.loader is not None,"source module unavailable")
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
def strict_source_audit(raw,result,freeze,oracle):
    need(raw.get("run_id")==freeze["source_run_id"]==result.get("run_id"),"source run identity mismatch")
    need(result.get("status")=="PENDING_INDEPENDENT_AUDIT","result status mismatch")
    need(result.get("fake_physical_keys")==[] and raw.get("fake_physical_keys")==[],"fake display is not neutral")
    env=result.get("environment")
    need(type(env) is dict and env.get("fake_display") is True and env.get("os_input") is False
         and env.get("gui_capture") is False and env.get("game") is False and type(env.get("model_calls")) is int
         and env.get("model_calls")==0,
         "scope receipt mismatch")
    events=raw.get("events")
    need(type(events) is list and len(events)==2,"expected one admission and one cleanup release")
    downs=[e for e in events if type(e) is dict and e.get("event")=="input_admission"]
    ups=[e for e in events if type(e) is dict and e.get("event")=="input_release_measurement"]
    need(len(downs)==1 and len(ups)==1,"event cardinality mismatch")
    down,up=downs[0],ups[0]
    need((down.get("id"),down.get("step"),up.get("id"),up.get("step"))==(freeze["source_run_id"],3,freeze["source_run_id"],3),"event context mismatch")
    for field in ("owner_id","intent_token","key"):
        need(type(down.get(field)) is str and bool(down[field]) and up.get(field)==down[field],f"event identity mismatch: {field}")
    dm=down.get("physical_key_measurement")
    need(type(dm) is dict and dm.get("classification")=="CONFIRMED_PHYSICAL_DOWN" and dm.get("identity_status")=="MINTED","confirmed down missing")
    aid=dm.get("actuation_id"); de=dm.get("adapter_edge")
    need(type(aid) is str and bool(aid) and type(de) is dict and de.get("edge")=="down"
         and de.get("status")=="CONFIRMED_PHYSICAL_DOWN" and de.get("actuation_id")==aid,"down actuation invalid")
    for field in ("owner_id","intent_token","key"):
        need(de.get(field)==down.get(field),f"down edge identity mismatch: {field}")
    records=raw.get("owner_records")
    need(type(records) is list,"owner record stream missing")
    releases=[r for r in records if type(r) is dict and r.get("event")=="owner_release"]
    need(len(releases)==1,"owner release record must be unique")
    source=releases[0]
    need(up.get("owner_cleanup_record")==source,"projected cleanup record differs from raw owner stream")
    need(source.get("reason")=="cancelled" and source.get("verified") is True
         and source.get("keys_down")==[] and source.get("buttons_down")==[],"owner cleanup not verified and neutral")
    measurements=source.get("per_key_release_measurements")
    need(type(measurements) is list,"owner per-key cleanup rows missing")
    matches=[r for r in measurements if type(r) is dict and r.get("actuation_id")==aid]
    need(len(matches)==1,"exactly one owner cleanup row must match the admitted actuation")
    release=matches[0]
    need(release.get("edge")=="up" and release.get("classification")=="CONFIRMED_PHYSICAL_UP"
         and release.get("identity_status")=="RETIRED" and release.get("release_attempted") is True,
         "source cleanup row is not a confirmed retired release")
    bracket=release.get("bracket"); pre=release.get("pre_sample"); post=release.get("post_sample")
    need(type(bracket) is dict and type(pre) is dict and type(post) is dict,"source bracket/samples missing")
    need(release.get("key")==down.get("key"),"source cleanup key mismatch")
    for field in ("owner_id","intent_token","key"):
        need(bracket.get(field)==down.get(field),f"source bracket identity mismatch: {field}")
    interval=bracket.get("physical_up_interval")
    need(bracket.get("status")=="CONFIRMED_PHYSICAL_UP" and type(interval) is list and len(interval)==2
         and all(nat(v) for v in interval) and interval[0]<=interval[1],"source up interval invalid")
    need(pre.get("available") is True and pre.get("error") is None and pre.get("down") is True
         and post.get("available") is True and post.get("error") is None and post.get("down") is False,
         "source samples do not confirm down-to-up")
    for sample in (pre,post):
        need(nat(sample.get("started_ns")) and nat(sample.get("finished_ns"))
             and sample["started_ns"]<=sample["finished_ns"],"source sample timing invalid")
    need(interval==[pre["finished_ns"],post["finished_ns"]],"source interval differs from sample endpoints")
    request=release.get("release_request_ns"); sync=release.get("sync_return_ns")
    need(nat(request) and nat(sync) and pre["finished_ns"]<=request<=sync<=post["finished_ns"],"release operation outside sample bracket")
    need(release.get("grants_input_authority") is False and release.get("application_consumption_observed") is False
         and bracket.get("grants_input_authority") is False and bracket.get("application_consumption_observed") is False,
         "source cleanup claims authority or effect")
    um=up.get("physical_key_measurement")
    need(type(um) is dict and um.get("classification")=="CONFIRMED_PHYSICAL_UP"
         and um.get("actuation_id")==aid and um.get("identity_status")=="RETIRED","projected release identity/classification invalid")
    for key,value in release.items():
        if key!="adapter_edge": need(um.get(key)==value,f"projected measurement differs from source: {key}")
    edge=um.get("adapter_edge")
    need(type(edge) is dict and edge.get("edge")=="up" and edge.get("status")=="CONFIRMED_PHYSICAL_UP"
         and edge.get("actuation_id")==aid and edge.get("owner_id")==down["owner_id"]
         and edge.get("intent_token")==down["intent_token"] and edge.get("key")==down["key"]
         and edge.get("interval")==interval and edge.get("grants_input_authority") is False,
         "projected adapter edge differs from source cleanup")
    need(up.get("grants_input_authority") is False and um.get("grants_input_authority") is False
         and up.get("application_consumption_observed") is False and um.get("application_consumption_observed") is False,
         "projected release claims authority or effect")
    consumer=oracle(events)
    need(result.get("event_types")==[e.get("event") for e in events],"result event summary mismatch")
    need(result.get("raw_sha256")==hashlib.sha256((json.dumps(raw,sort_keys=True,indent=2)+"\n").encode()).hexdigest(),"raw digest mismatch")
    return {"schema":"map01-v39-perkey-bridge-a04-owner-source-audit-v1",
            "status":"PASS_OWNER_SOURCE_BOUND_CLEANUP_AUDIT","run_id":freeze["source_run_id"],
            "audit_run_id":freeze["run_id"],
            "raw_owner_release_records":len(releases),"matching_per_key_release_rows":len(matches),
            "event_count":len(events),"actuation_id":aid,"strict_consumer_result":consumer,
            "authority_granted":False,"application_effect_observed":False,
            "scope":"raw owner-source join and bracket audit for one retained fake-display cleanup trace"}
def load_oracle():
    module=load("strict_v39_consumer_a03",SRC/"CONSUMER/audit.py")
    return module.independently_reconstruct
def load_frozen():
    fb=(HERE/"FREEZE.json").read_bytes(); f=json.loads(fb)
    for rel,digest in f["source_sha256"].items():
        need(hashlib.sha256((HERE/rel).read_bytes()).hexdigest()==digest,"freeze source mismatch: "+rel)
    rb=(SRC/"BRIDGE/RAW_A03.json").read_bytes(); result=json.loads((SRC/"BRIDGE/RESULT_A03.json").read_text())
    need(hashlib.sha256(rb).hexdigest()==f["input_sha256"],"frozen raw digest mismatch")
    need(hashlib.sha256((SRC/"BRIDGE/RESULT_A03.json").read_bytes()).hexdigest()==f["result_sha256"],"frozen result digest mismatch")
    baseline=json.loads((SRC/"BRIDGE/AUDIT_A03.json").read_text())
    need(baseline.get("status")=="PASS" and baseline.get("run_id")==f["source_run_id"]
         and baseline.get("raw_sha256")==f["input_sha256"],"retained A03 audit does not match frozen source")
    return f,json.loads(rb),result
def main():
    freeze,raw,result=load_frozen(); verdict=strict_source_audit(raw,result,freeze,load_oracle())
    (HERE/"AUDIT.json").write_text(json.dumps(verdict,indent=2,sort_keys=True)+"\n",encoding="utf-8",newline="\n")
    print(json.dumps(verdict,sort_keys=True))
if __name__=="__main__": main()
