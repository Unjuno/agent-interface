from __future__ import annotations
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
class AuditFailure(ValueError):pass
def need(ok,msg):
    if not ok:raise AuditFailure(msg)
def exact(a,b):
    if type(a)is not type(b):return False
    if type(a)is dict:return a.keys()==b.keys() and all(exact(a[k],b[k]) for k in a)
    if type(a)is list:return len(a)==len(b) and all(exact(x,y) for x,y in zip(a,b))
    return a==b
def audit(raw,result,freeze,scenario):
    need(raw.get("run_id")==freeze["run_id"]==result.get("run_id"),"run identity mismatch")
    need(exact(raw.get("scenario"),scenario),"raw scenario mismatch")
    need(result.get("status")=="PENDING_INDEPENDENT_AUDIT","result status mismatch")
    need(type(result.get("baseline_invocations"))is int and result["baseline_invocations"]==5,"baseline invocation receipt mismatch")
    need(type(result.get("successor_invocations"))is int and result["successor_invocations"]==5,"successor invocation receipt mismatch")
    base=raw.get("baseline");succ=raw.get("successor");names=["owner","intent","key","bracket","valid"]
    need(type(base)is list and type(succ)is list and [x.get("case") for x in base]==names and [x.get("case") for x in succ]==names,"case matrix mismatch")
    for old,new in zip(base[:4],succ[:4]):
        need(len(old.get("events",[]))==1 and old["events"][0].get("event")=="input_release_measurement","baseline did not falsely contextualize mismatch")
        need(old.get("context_count")==0,"baseline did not consume admitted context")
        need(len(new.get("events",[]))==1 and new["events"][0].get("event")=="input_cleanup_unscoped","successor mismatch was not left unscoped")
        need(new.get("held")==[scenario["key"]] and new.get("active_count")==1 and new.get("context_count")==1,"mismatch corrupted active admission state")
    valid=succ[4]
    need(len(valid.get("events",[]))==1 and valid["events"][0].get("event")=="input_release_measurement","valid control did not forward contextually")
    event=valid["events"][0];need((event.get("id"),event.get("step"),event.get("owner_id"),event.get("intent_token"),event.get("key"))==(scenario["program_id"],scenario["step"],scenario["owner_id"],scenario["intent_token"],scenario["key"]),"valid control identity mismatch")
    need(valid.get("held")==[] and valid.get("active_count")==0 and valid.get("context_count")==0,"valid release did not retire actuation")
    env=result.get("environment",{});need(env.get("in_memory_stub")is True and env.get("os_input")is False and env.get("gui")is False and env.get("game")is False and env.get("model_calls")==0,"scope receipt mismatch")
    return {"schema":"map01-v39-perkey-bridge-a04-identity-guard-audit-v1","disposition":"PASS_EXACT_CLEANUP_IDENTITY_GUARD_SCOPED",
      "run_id":freeze["run_id"],"mismatch_cases":4,"baseline_false_contextualizations":4,"successor_unscoped_mismatches":4,
      "valid_contextual_positive_control":True,"authority_granted":False,"application_effect_observed":False,"scope":freeze["scope"]}
def load(out):
    fb=(HERE/"FREEZE.json").read_bytes();freeze=json.loads(fb)
    for rel,digest in freeze["source_sha256"].items():need(hashlib.sha256((HERE/rel).read_bytes()).hexdigest()==digest,"frozen source mismatch: "+rel)
    sb=(HERE/"scenario.json").read_bytes();need(hashlib.sha256(sb).hexdigest()==freeze["input_sha256"],"scenario hash mismatch")
    rb=(out/"RAW.json").read_bytes();zb=(out/"RESULT.json").read_bytes();raw=json.loads(rb);result=json.loads(zb)
    need(result.get("raw_sha256")==hashlib.sha256(rb).hexdigest(),"raw/result digest mismatch")
    need(result.get("freeze_sha256")==hashlib.sha256(fb).hexdigest(),"result/freeze digest mismatch")
    return freeze,raw,result,json.loads(sb),fb,rb,zb
def main():
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--out",required=True);out=Path(p.parse_args().out)
    f,r,z,s,fb,rb,zb=load(out);v=audit(r,z,f,s);v.update({"candidate_raw_sha256":hashlib.sha256(rb).hexdigest(),"candidate_result_sha256":hashlib.sha256(zb).hexdigest(),"candidate_freeze_sha256":hashlib.sha256(fb).hexdigest(),"audit_source_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
    (out/"AUDIT.json").write_text(json.dumps(v,indent=2,sort_keys=True)+"\n",encoding="utf-8",newline="\n");print(json.dumps(v,sort_keys=True))
if __name__=="__main__":main()
