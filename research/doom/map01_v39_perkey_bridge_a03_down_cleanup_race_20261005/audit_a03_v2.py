from __future__ import annotations
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
OUT=HERE/"results/a03"
class AuditFailure(ValueError): pass
def need(ok,msg):
    if not ok: raise AuditFailure(msg)
def exact(a,b):
    if type(a) is not type(b): return False
    if type(a) is dict: return a.keys()==b.keys() and all(exact(a[k],b[k]) for k in a)
    if type(a) is list: return len(a)==len(b) and all(exact(x,y) for x,y in zip(a,b))
    return a==b
def audit(raw,result,freeze,scenario):
    need(raw.get("run_id")==freeze["run_id"]==result.get("run_id"),"run id mismatch")
    need(exact(raw.get("scenario"),scenario),"raw embedded scenario differs from frozen scenario")
    need(result.get("status")=="PENDING_INDEPENDENT_AUDIT","result status mismatch")
    need(type(result.get("baseline_invocations")) is int and result["baseline_invocations"]==1,"baseline count mismatch")
    need(type(result.get("successor_invocations")) is int and result["successor_invocations"]==1,"successor count mismatch")
    expected_env={"in_memory_stub":True,"os_input":False,"gui":False,"game":False,"model_calls":0,
                   "python_version":freeze["python_version"],"image_id":freeze["image_id"],"platform":freeze["platform"]}
    need(exact(result.get("environment"),expected_env),"runtime/scope receipt mismatch")
    base=raw.get("baseline");succ=raw.get("successor")
    need(type(base) is dict and type(succ) is dict,"baseline/successor traces missing")
    old=base.get("events");new=succ.get("events")
    need(type(old) is list and len(old)==3 and [x.get("event") for x in old]==["input_cleanup_unscoped","input_admission","input_release_measurement"],"baseline race signature missing")
    need(old[0].get("measurement",{}).get("actuation_id")==scenario["actuation_id"],"baseline unscoped cleanup identity mismatch")
    need(old[2].get("physical_key_measurement",{}).get("classification")=="NOOP_ALREADY_UP","baseline duplicate no-op missing")
    need(type(new) is list and len(new)==2 and [x.get("event") for x in new]==["input_admission","input_release_measurement"],"successor event order/cardinality mismatch")
    down,up=new
    need((down.get("id"),down.get("step"),up.get("id"),up.get("step"))==(scenario["program_id"],scenario["step"],scenario["program_id"],scenario["step"]),"successor context mismatch")
    dm=down.get("physical_key_measurement",{});um=up.get("physical_key_measurement",{})
    aid=scenario["actuation_id"]
    need(dm.get("actuation_id")==aid and um.get("actuation_id")==aid,"successor actuation lineage mismatch")
    need(um.get("classification")=="CONFIRMED_PHYSICAL_UP" and um.get("identity_status")=="RETIRED","successor cleanup state mismatch")
    owner_records=succ.get("owner_records")
    need(type(owner_records) is list and len(owner_records)==1,"successor owner stream cardinality mismatch")
    source=owner_records[0]
    need(source.get("event")=="owner_release" and source.get("verified") is True and source.get("keys_down")==[] and source.get("buttons_down")==[],"source cleanup not verified neutral")
    need(exact(up.get("owner_cleanup_record"),source),"forwarded owner record differs from raw owner stream")
    matches=[x for x in source.get("per_key_release_measurements",[]) if type(x) is dict and x.get("actuation_id")==aid]
    need(len(matches)==1,"matching source release row not unique")
    release=matches[0]
    need(exact(um.get("bracket"),release.get("bracket")),"projected bracket differs by value or type from owner source")
    edge=um.get("adapter_edge")
    expected_edge={"edge":"up","status":"CONFIRMED_PHYSICAL_UP","actuation_id":aid,"owner_id":scenario["owner_id"],
                   "intent_token":scenario["intent_token"],"key":scenario["key"],"interval":scenario["cleanup_interval"],"grants_input_authority":False}
    need(exact(edge,expected_edge),"projected edge differs by value or exact type")
    need(succ.get("physical_keys")==[] and succ.get("held_keys")==[],"successor neutral-state receipt mismatch")
    need(succ.get("authority_granted") is False and succ.get("application_effect_observed") is False,"authority/effect boundary mismatch")
    return {"schema":"map01-v39-perkey-bridge-a03-race-audit-v2","disposition":"PASS_DOWN_CLEANUP_RACE_REPAIRED",
            "run_id":freeze["run_id"],"baseline_event_count":len(old),"successor_event_count":len(new),
            "baseline_unscoped_cleanup":True,"baseline_duplicate_noop":True,"successor_contextual_cleanup":True,
            "successor_duplicate_noop":False,"matching_owner_release_rows":len(matches),"authority_granted":False,
            "application_effect_observed":False,"scope":freeze["scope"]}
def load():
    fb=(HERE/"FREEZE.json").read_bytes();freeze=json.loads(fb)
    for rel,digest in freeze["source_sha256"].items():
        need(hashlib.sha256((HERE/rel).read_bytes()).hexdigest()==digest,"frozen source mismatch: "+rel)
    sb=(HERE/"scenario.json").read_bytes();need(hashlib.sha256(sb).hexdigest()==freeze["input_sha256"],"frozen scenario digest mismatch")
    rawbytes=(OUT/"RAW.json").read_bytes();resultbytes=(OUT/"RESULT.json").read_bytes()
    raw=json.loads(rawbytes);result=json.loads(resultbytes)
    need(result.get("raw_sha256")==hashlib.sha256(rawbytes).hexdigest(),"raw/result digest mismatch")
    need(result.get("freeze_sha256")==hashlib.sha256(fb).hexdigest(),"result/freeze digest mismatch")
    need(exact(raw.get("scenario"),json.loads(sb)),"raw does not contain exact frozen scenario")
    return freeze,raw,result,json.loads(sb),fb,rawbytes,resultbytes
def main():
    freeze,raw,result,scenario,fb,rawbytes,resultbytes=load();v=audit(raw,result,freeze,scenario)
    code=Path(__file__).read_bytes();v.update({"audit_source_sha256":hashlib.sha256(code).hexdigest(),
        "candidate_raw_sha256":hashlib.sha256(rawbytes).hexdigest(),"candidate_result_sha256":hashlib.sha256(resultbytes).hexdigest(),
        "candidate_freeze_sha256":hashlib.sha256(fb).hexdigest()})
    (OUT/"AUDIT.json").write_text(json.dumps(v,indent=2,sort_keys=True)+"\n",encoding="utf-8",newline="\n")
    print(json.dumps(v,sort_keys=True))
if __name__=="__main__":main()
