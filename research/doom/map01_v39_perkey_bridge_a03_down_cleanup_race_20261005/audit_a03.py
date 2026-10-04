from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
def need(ok,msg):
    if not ok: raise ValueError(msg)
def audit(raw,result,freeze):
    need(raw.get("run_id")==freeze["run_id"]==result.get("run_id"),"run id mismatch")
    need(result.get("status")=="PENDING_INDEPENDENT_AUDIT","result status mismatch")
    need(result.get("baseline_invocations")==1 and type(result.get("baseline_invocations")) is int,"baseline invocation receipt mismatch")
    need(result.get("successor_invocations")==1 and type(result.get("successor_invocations")) is int,"successor invocation receipt mismatch")
    baseline=raw.get("baseline",{}); fixed=raw.get("successor",{}); s=raw.get("scenario",{})
    old=baseline.get("events"); new=fixed.get("events")
    need(type(old) is list and [r.get("event") for r in old]==["input_cleanup_unscoped","input_admission","input_release_measurement"],"baseline race signature missing")
    need(old[0].get("measurement",{}).get("actuation_id")==s["actuation_id"],"baseline unscoped witness mismatch")
    need(old[2].get("physical_key_measurement",{}).get("classification")=="NOOP_ALREADY_UP","baseline duplicate noop missing")
    need(type(new) is list and len(new)==2 and [r.get("event") for r in new]==["input_admission","input_release_measurement"],"successor event cardinality/order mismatch")
    down,up=new
    need((down.get("id"),down.get("step"),up.get("id"),up.get("step"))==(s["program_id"],s["step"],s["program_id"],s["step"]),"successor context mismatch")
    need(up.get("physical_key_measurement",{}).get("actuation_id")==s["actuation_id"],"successor actuation join mismatch")
    edge=up.get("physical_key_measurement",{}).get("adapter_edge")
    need(type(edge) is dict and edge.get("edge")=="up" and edge.get("status")=="CONFIRMED_PHYSICAL_UP"
         and edge.get("actuation_id")==s["actuation_id"] and edge.get("interval")==s["cleanup_interval"],"successor physical-up edge mismatch")
    need(up.get("owner_cleanup_record")==fixed.get("owner_records",[None])[0],"forwarded owner record differs from source stream")
    need(fixed.get("physical_keys")==[] and fixed.get("held_keys")==[],"successor did not reach neutral state")
    need(fixed.get("authority_granted") is False and fixed.get("application_effect_observed") is False
         and result.get("environment")=={"in_memory_stub":True,"os_input":False,"gui":False,"game":False,"model_calls":0,
         "python_version":freeze["python_version"],"image_id":freeze["image_id"],"platform":freeze["platform"]},"scope/authority receipt mismatch")
    return {"schema":"map01-v39-perkey-bridge-a03-race-audit-v1","disposition":"PASS_DOWN_CLEANUP_RACE_REPAIRED",
            "run_id":freeze["run_id"],"baseline_event_count":len(old),"successor_event_count":len(new),
            "baseline_unscoped_cleanup":True,"baseline_duplicate_noop":True,"successor_contextual_cleanup":True,
            "successor_duplicate_noop":False,"authority_granted":False,"application_effect_observed":False,
            "scope":freeze["scope"]}
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--out",required=True);out=Path(ap.parse_args().out)
    f=json.loads((HERE/"FREEZE.json").read_text())
    for rel,digest in f["source_sha256"].items(): need(hashlib.sha256((HERE/rel).read_bytes()).hexdigest()==digest,"source mismatch: "+rel)
    rawbytes=(out/"RAW.json").read_bytes();need(hashlib.sha256(rawbytes).hexdigest()==f["input_sha256"],"scenario/raw digest mismatch")
    resultbytes=(out/"RESULT.json").read_bytes();result=json.loads(resultbytes)
    need(result.get("raw_sha256")==hashlib.sha256(rawbytes).hexdigest(),"result raw digest mismatch")
    need(result.get("freeze_sha256")==hashlib.sha256((HERE/"FREEZE.json").read_bytes()).hexdigest(),"result freeze mismatch")
    verdict=audit(json.loads(rawbytes),result,f)
    verdict.update({"raw_sha256":hashlib.sha256(rawbytes).hexdigest(),"result_sha256":hashlib.sha256(resultbytes).hexdigest(),
                    "freeze_sha256":hashlib.sha256((HERE/"FREEZE.json").read_bytes()).hexdigest()})
    (out/"AUDIT.json").write_text(json.dumps(verdict,indent=2,sort_keys=True)+"\n",encoding="utf-8",newline="\n")
    print(json.dumps(verdict,sort_keys=True))
if __name__=="__main__":main()
