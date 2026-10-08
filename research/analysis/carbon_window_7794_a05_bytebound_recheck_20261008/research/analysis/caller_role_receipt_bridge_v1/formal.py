import copy,hashlib,json,pathlib,sys
ROOT=pathlib.Path(__file__).resolve().parents[3]
CALLER=ROOT/"research/live_control/adaptive_acquisition_caller_v3.py"
EXPECTED_CALLER_BLOB="7faf042304728ce91a3e4f89d465b251ea0bf70d"

def git_blob(data):
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
assert git_blob(CALLER.read_bytes())==EXPECTED_CALLER_BLOB
sys.path.insert(0,str(CALLER.parent))
from adaptive_acquisition_caller_v3 import run
from bridge import RoleReceiptBridge,FOCUS_BLOB,TARGET_BLOB,REUSABLE,FRESH

class Clock:
    def __init__(self): self.n=0
    def __call__(self): self.n+=1; return self.n

TARGET={"handle":"persistent_a_field","point":[271,243]}
def focus(current=True):
    return {"disposition":"EMIT","scope":"FOCUS_OBSERVATION_CURRENTNESS",
      "role":REUSABLE,"storage":"PERSIST_DEPENDENCY","source_blob":FOCUS_BLOB,
      "current":current,"lineage":"focus_case","prepared_version":"g0",
      "current_version":"g0" if current else "g1","identity_relation":"SAME"}
def gate(truth="TRUE",lineage_current=True,role=FRESH,storage="EPHEMERAL_ONLY"):
    return {"disposition":"EMIT","scope":"TARGET_HANDLE_CURRENTNESS",
      "role":role,"storage":storage,"source_blob":TARGET_BLOB,"truth":truth,
      "lineage":"persistent_a_field@58","lineage_current":lineage_current,
      "handle":"persistent_a_field","observation_sequence":58}

def spec(session):
    return {"target":"field","route":"reuse","coarse_origin":"caller_provided",
      "provided_coarse":None,"cached_target":copy.deepcopy(TARGET),
      "local_repair_on":[],"repair_on":[],"session_id":session}

def one(name,dep,raw_gate,intent,epoch,*,bind_intent=None,bind_epoch=None,
        try_persist_gate=False,bridge=None):
    b=bridge or RoleReceiptBridge()
    dep_store=b.store(copy.deepcopy(dep)) if dep is not None else False
    persist_gate_result=None
    if try_persist_gate and raw_gate is not None:
        persist_gate_result=b.store(copy.deepcopy(raw_gate))
    env=None
    if raw_gate is not None:
        env=b.bind_gate(copy.deepcopy(raw_gate),
          bind_intent if bind_intent is not None else intent,
          bind_epoch if bind_epoch is not None else epoch)
    calls={"execute":0,"verify_effect":0}
    journal=[]
    adapters={
      "journal":journal.append,
      "reuse_revalidate":b.reuse_revalidate,
      "final_revalidate":lambda payload:b.final_revalidate(payload,env,intent,epoch),
      "execute":lambda payload:(calls.__setitem__("execute",calls["execute"]+1) or {"status":"completed"}),
      "verify_effect":lambda payload:(calls.__setitem__("verify_effect",calls["verify_effect"]+1) or {"status":"succeeded"}),
    }
    result=run(spec(name),adapters,clock=Clock(),id_factory=lambda:"unused")
    return {
      "name":name,"outcome":result["outcome"],"reason":result["reason"],
      "input_authority":result["input_authority"],
      "execute_count":calls["execute"],"verify_effect_count":calls["verify_effect"],
      "reuse_stage":result["stages"]["reuse_revalidate"],
      "final_stage":result["stages"]["final_revalidate"],
      "execute_stage":result["stages"]["execute"],
      "persistent_roles":[x.get("role") for x in b.persistent],
      "persistent_commit_count":sum(x.get("role")==FRESH for x in b.persistent),
      "gate_consumed_count":len(b.consumed),"bridge_rejections":list(b.rejections),
      "dep_store":dep_store,"persist_gate_result":persist_gate_result
    },b,env

rows=[]
r,_,_=one("positive",focus(True),gate("TRUE"),"intentA",1);rows.append(r)
r,_,_=one("stale_dependency",focus(False),gate("TRUE"),"intentA",1);rows.append(r)
r,_,_=one("false_gate",focus(True),gate("FALSE"),"intentA",1);rows.append(r)
r,_,_=one("missing_gate",focus(True),None,"intentA",1);rows.append(r)
r,_,_=one("prior_epoch_replay",focus(True),gate("TRUE"),"intentA",2,bind_epoch=1);rows.append(r)
r,_,_=one("wrong_intent",focus(True),gate("TRUE"),"intentA",1,bind_intent="intentB");rows.append(r)
r,_,_=one("persist_commit_attempt",focus(True),gate("TRUE"),"intentA",1,try_persist_gate=True);rows.append(r)
r,_,_=one("unknown_role",focus(True),gate("TRUE",role="UNKNOWN_ROLE"),"intentA",1);rows.append(r)

pair_bridge=RoleReceiptBridge()
assert pair_bridge.store(focus(True))
p1,_,_=one("paired_commit_1",None,gate("TRUE"),"pair",1,bridge=pair_bridge);rows.append(p1)
p2,_,_=one("paired_commit_2",None,gate("FALSE"),"pair",2,bridge=pair_bridge);rows.append(p2)

result={
 "caller_blob":git_blob(CALLER.read_bytes()),"rows":rows,
 "scenario_count":len(rows),
 "negative_execute_total":sum(x["execute_count"] for x in rows
   if x["name"] in {"stale_dependency","false_gate","missing_gate","prior_epoch_replay",
                    "wrong_intent","persist_commit_attempt","unknown_role"}),
 "cross_intent_epoch_replay_accepts":sum(
   x["execute_count"] for x in rows if x["name"] in {"prior_epoch_replay","wrong_intent"}),
 "persistent_commit_receipts":max(x["persistent_commit_count"] for x in rows),
 "paired":{"first_outcome":p1["outcome"],"first_execute":p1["execute_count"],
           "second_outcome":p2["outcome"],"second_execute":p2["execute_count"],
           "persistent_roles":p2["persistent_roles"]},
 "formal_invocations":1,"reruns":0,"replacements":0,"tuning":0,
 "decision":None
}
positive=next(x for x in rows if x["name"]=="positive")
neg=[x for x in rows if x["name"] in {"stale_dependency","false_gate","missing_gate",
 "prior_epoch_replay","wrong_intent","persist_commit_attempt","unknown_role"}]
stale=next(x for x in rows if x["name"]=="stale_dependency")
pass_gate=(positive["outcome"]=="TASK_SUCCEEDED" and positive["execute_count"]==1 and
 all(x["execute_count"]==0 and x["input_authority"]=="none" for x in neg) and
 stale["final_stage"]["status"]=="skipped" and result["persistent_commit_receipts"]==0 and
 result["cross_intent_epoch_replay_accepts"]==0 and
 p1["outcome"]=="TASK_SUCCEEDED" and p1["execute_count"]==1 and
 p2["execute_count"]==0 and p2["persistent_roles"]==[REUSABLE])
result["decision"]="PASS_CALLER_ROLE_RECEIPT_BRIDGE_SCOPED" if pass_gate else "FAIL_CALLER_ROLE_RECEIPT_BRIDGE"
print(json.dumps(result,indent=2,sort_keys=True))
