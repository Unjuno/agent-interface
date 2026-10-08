import copy
from audit import validate
def mutation_checks(raw):
 out={"baseline_passes":validate(raw)["status"]=="PASS_CONSTRUCTION_SCOPED"}
 def row(x,k):return next(r for r in x["cases"][1]["events"] if r.get("event")=="input_release_transition" and r.get("key")==k)
 def reject(n,f):
  x=copy.deepcopy(raw);f(x);out[n]=validate(x)["status"]=="FAIL"
 reject("wrong_receipt_identity",lambda x:row(x,"F9")["owner_thread_keyup_receipt"].update(key="F8"))
 reject("missing_transition",lambda x:x["cases"][1]["events"].remove(row(x,"F9")))
 reject("missing_retry",lambda x:row(x,"F9")["owner_thread_keyup_receipt"]["server_keyup_attempts"].pop())
 reject("false_physical_authority",lambda x:row(x,"F9")["owner_thread_keyup_receipt"].update(physical_verification_authoritative=True))
 reject("held_final_key",lambda x:x["cases"][1].update(server_keycodes_down_after_executor_release=[39]))
 reject("wrong_order",lambda x:row(x,"F9").update(release_batch_position=0))
 return out
if __name__=="__main__":
 import json,pathlib
 v=mutation_checks(json.loads(pathlib.Path("results/candidate.json").read_text()));print(json.dumps({"status":"PASS" if all(v.values()) else "FAIL","checks":v},sort_keys=True));raise SystemExit(0 if all(v.values()) else 1)
