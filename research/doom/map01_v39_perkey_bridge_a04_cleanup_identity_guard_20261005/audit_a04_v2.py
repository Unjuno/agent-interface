from __future__ import annotations
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;OUT=HERE/"results/a04"
class AuditFailure(ValueError):pass
def need(ok,msg):
    if not ok:raise AuditFailure(msg)
def exact(a,b):
    if type(a)is not type(b):return False
    if type(a)is dict:return a.keys()==b.keys() and all(exact(a[k],b[k]) for k in a)
    if type(a)is list:return len(a)==len(b) and all(exact(x,y) for x,y in zip(a,b))
    return a==b
def audit(raw,candidate_result,freeze,scenario,raw_sha,freeze_sha):
    need(raw.get("run_id")==freeze["run_id"]==candidate_result.get("run_id"),"run identity mismatch")
    need(exact(raw.get("scenario"),scenario),"scenario mismatch")
    need(candidate_result.get("status")=="PENDING_INDEPENDENT_AUDIT","candidate status mismatch")
    need(candidate_result.get("raw_sha256")==raw_sha,"candidate result/raw mismatch")
    need(candidate_result.get("freeze_sha256")==freeze_sha,"candidate result/freeze mismatch")
    baseline=raw.get("baseline");successor=raw.get("successor");names=["owner","intent","key","bracket","valid"]
    need(type(baseline)is list and type(successor)is list and [x.get("case") for x in baseline]==names and [x.get("case") for x in successor]==names,"case matrix/order mismatch")
    need(type(freeze.get("baseline_invocations"))is int and freeze["baseline_invocations"]==5,"frozen baseline method-case count mismatch")
    need(type(freeze.get("successor_invocations"))is int and freeze["successor_invocations"]==5,"frozen successor method-case count mismatch")
    need(type(candidate_result.get("baseline_invocations"))is int and candidate_result["baseline_invocations"]==1,"candidate probe-process count mismatch")
    need(type(candidate_result.get("successor_invocations"))is int and candidate_result["successor_invocations"]==1,"successor probe-process count mismatch")
    env=candidate_result.get("environment",{})
    need(env.get("in_memory_stub")is True and env.get("os_input")is False and env.get("gui")is False and env.get("game")is False and type(env.get("model_calls"))is int and env["model_calls"]==0,"environment scope mismatch")
    for old,new in zip(baseline[:4],successor[:4]):
        case=old["case"];expect_owner=scenario["owner_id"];expect_intent=scenario["intent_token"];expect_key=scenario["key"]
        if case=="owner":expect_owner="owner-other"
        elif case=="intent":expect_intent="intent-other"
        elif case=="key":expect_key=scenario["mismatch_key"]
        elif case=="bracket":pass
        expected_source={"actuation_id":scenario["actuation_id"],"owner_id":expect_owner,"intent_token":expect_intent,"key":expect_key}
        for trace in (old,new):
            ev=trace["events"][0]
            rec=ev.get("owner_cleanup_record")
            need(type(rec)is dict and type(rec.get("per_key_release_measurements"))is list and len(rec["per_key_release_measurements"])==1,"source cleanup row missing")
            source=rec["per_key_release_measurements"][0]
            need(exact({k:source.get(k) for k in expected_source},expected_source),"source cleanup identity does not match case")
            expected_bracket={"owner_id":expect_owner,"intent_token":expect_intent,"key":scenario["mismatch_key"] if case=="bracket" else expect_key}
            need(exact({k:source.get("bracket",{}).get(k) for k in expected_bracket},expected_bracket),"source bracket identity does not match case")
        oe=old.get("events");ne=new.get("events")
        need(type(oe)is list and len(oe)==1 and oe[0].get("event")=="input_release_measurement" and oe[0].get("id")==scenario["program_id"] and oe[0].get("physical_key_measurement",{}).get("actuation_id")==scenario["actuation_id"],"baseline did not misattribute mismatch")
        need(old.get("context_count")==0,"baseline did not consume matching context")
        need(type(ne)is list and len(ne)==1 and ne[0].get("event")=="input_cleanup_unscoped","successor mismatch not unscoped")
        need(new.get("held")==[scenario["key"]] and new.get("active_count")==1 and new.get("context_count")==1,"successor altered admitted state")
    old_valid=baseline[4];new_valid=successor[4]
    need(old_valid["events"][0].get("event")=="input_release_measurement","baseline valid control missing")
    need(new_valid["events"][0].get("event")=="input_release_measurement","successor valid control missing")
    ve=new_valid["events"][0]
    need((ve.get("id"),ve.get("step"),ve.get("owner_id"),ve.get("intent_token"),ve.get("key"))==(scenario["program_id"],scenario["step"],scenario["owner_id"],scenario["intent_token"],scenario["key"]),"successor valid identity mismatch")
    need(new_valid.get("held")==[] and new_valid.get("active_count")==0 and new_valid.get("context_count")==0,"successor valid control did not retire")
    return {"schema":"map01-v39-perkey-bridge-a04-identity-guard-audit-v2","disposition":"PASS_EXACT_CLEANUP_IDENTITY_GUARD_SCOPED",
      "run_id":freeze["run_id"],"mismatch_cases":4,"baseline_false_contextualizations":4,"successor_unscoped_mismatches":4,
      "successor_valid_contextual_positive_control":True,"candidate_probe_invocations":1,"per_arm_case_rows":5,
      "count_units":"freeze invocation counts denote five per-arm method cases; candidate result invocation counts denote one probe process per arm",
      "corrected_method_case_counts":{"baseline":5,"successor":5},
      "authority_granted":False,"application_effect_observed":False,"scope":freeze["scope"]}
def load():
    fb=(HERE/"FREEZE.json").read_bytes();freeze=json.loads(fb)
    for rel,digest in freeze["source_sha256"].items():need(hashlib.sha256((HERE/rel).read_bytes()).hexdigest()==digest,"frozen source mismatch: "+rel)
    sb=(HERE/"scenario.json").read_bytes();need(hashlib.sha256(sb).hexdigest()==freeze["input_sha256"],"scenario hash mismatch")
    rb=(OUT/"RAW.json").read_bytes();zb=(OUT/"RESULT_CANDIDATE.json").read_bytes();raw=json.loads(rb);result=json.loads(zb)
    need(result.get("raw_sha256")==hashlib.sha256(rb).hexdigest(),"candidate raw hash mismatch")
    need(result.get("freeze_sha256")==hashlib.sha256(fb).hexdigest(),"candidate freeze hash mismatch")
    return freeze,raw,result,json.loads(sb),fb,rb,zb
def verify_v2_freeze():
    f=json.loads((HERE/"FREEZE-AUDIT-V2.json").read_bytes())
    for field,name in (("audit_source_sha256","audit_a04_v2.py"),("test_source_sha256","test_a04_v2.py")):
        need(hashlib.sha256((HERE/name).read_bytes()).hexdigest()==f[field],"audit v2 source hash mismatch: "+name)
    need(hashlib.sha256((HERE/"FREEZE.json").read_bytes()).hexdigest()==f["parent_candidate_freeze_sha256"],"parent freeze mismatch")
    need(hashlib.sha256((OUT/"RAW.json").read_bytes()).hexdigest()==f["parent_raw_sha256"],"parent raw mismatch")
    need(hashlib.sha256((OUT/"RESULT_CANDIDATE.json").read_bytes()).hexdigest()==f["parent_candidate_result_sha256"],"parent candidate result mismatch")
    return f
def main():
    verify_v2_freeze();f,r,z,s,fb,rb,zb=load();v=audit(r,z,f,s,hashlib.sha256(rb).hexdigest(),hashlib.sha256(fb).hexdigest())
    corrected={"schema":"map01-v39-perkey-bridge-a04-result-audit-reconstruction-v1","source_candidate_result_sha256":hashlib.sha256(zb).hexdigest(),"raw_sha256":hashlib.sha256(rb).hexdigest(),"freeze_sha256":hashlib.sha256(fb).hexdigest(),"baseline_method_cases":5,"successor_method_cases":5,"candidate_probe_processes":1,"note":"Derived from the retained five-row-per-arm raw; the original RESULT_CANDIDATE.json is preserved unchanged."}
    v.update({"candidate_raw_sha256":hashlib.sha256(rb).hexdigest(),"candidate_result_sha256":hashlib.sha256(zb).hexdigest(),"candidate_freeze_sha256":hashlib.sha256(fb).hexdigest(),"audit_source_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
    (OUT/"RESULT-AUDIT-V2.json").write_text(json.dumps(corrected,indent=2,sort_keys=True)+"\n",encoding="utf-8",newline="\n")
    (OUT/"AUDIT-V2.json").write_text(json.dumps(v,indent=2,sort_keys=True)+"\n",encoding="utf-8",newline="\n");print(json.dumps(v,sort_keys=True))
if __name__=="__main__":main()
