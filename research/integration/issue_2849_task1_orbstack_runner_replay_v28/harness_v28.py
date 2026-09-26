from __future__ import annotations
import hashlib,json,os,shutil,sys,threading,time
from pathlib import Path
ROOT=Path(os.environ["ISSUE_2849_REPO"]).resolve(); RUN=Path(os.environ["ISSUE_2849_V28_RUN"]).resolve()
V26=ROOT/"research/integration/issue_2849_task1_orbstack_formal_v26/evidence/task1-seed-284926"
for path in (ROOT,ROOT/"research/live_control",ROOT/"runtime",ROOT/"research/observation_tiles",ROOT/"research/observation_gating",ROOT/"research/real_apps_v1",ROOT/"research/integration/issue_2849_task1_orbstack_smoke_v2"):
    sys.path.insert(0,str(path))
from docker_model_call_backend_v1 import call
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    mirror=V26/"host-model-mirror"; ipc=RUN/"ipc"; output=RUN/"backend-call"
    response_fixture=V26/"ipc/d8b2c076c08f48229b18484e2ca4a419.response.jsonl"
    prompt=V26/"task-run/model-calls/plain/task-1/anchor/prompt.txt"; image=mirror/"image.png"; workspace=mirror/"workspace"
    stop=threading.Event(); feed={"count":0,"error":None,"request_id":None}
    def supply():
        deadline=time.monotonic()+30
        try:
            while not stop.is_set() and time.monotonic()<deadline:
                requests=sorted(ipc.glob("*.request.json"))
                if requests:
                    if len(requests)!=1: raise RuntimeError("expected one IPC request")
                    q=json.loads(requests[0].read_text())
                    expected={"mode":"coordinate","authority_granted":False,"image_sha256":sha(image),
                      "schema_sha256":sha(mirror/"schema.json"),"instructions_sha256":sha(mirror/"instructions.txt"),"working":"/repo/workspace"}
                    if any(q.get(k)!=v for k,v in expected.items()): raise RuntimeError("replay request digest/scope mismatch")
                    target=ipc/(q["request_id"]+".response.jsonl"); shutil.copyfile(response_fixture,target)
                    feed.update(count=1,error=None,request_id=q["request_id"],request=q,response_sha256=sha(target)); return
                time.sleep(.02)
            if not stop.is_set(): raise TimeoutError("nested runner emitted no request")
        except Exception as exc: feed["error"]=type(exc).__name__+":"+str(exc)
    worker=threading.Thread(target=supply,daemon=True);worker.start(); result=None;error=None
    try: result=call(output,prompt.read_text(encoding="utf-8"),image,"plain",workspace)
    except Exception as exc: error=type(exc).__name__+":"+str(exc)
    finally: stop.set();worker.join(timeout=2)
    rr=output/"runner"; process=json.loads((rr/"process.json").read_text()) if (rr/"process.json").is_file() else {}
    validation=json.loads((output/"schema-validation.json").read_text()) if (output/"schema-validation.json").is_file() else {}
    events=rr/"events.jsonl"; raw_ok=events.is_file() and sha(events)==sha(response_fixture)
    grounding=None if result is None else result.get("grounding"); field=None if grounding is None else grounding.get("field_point"); submit=None if grounding is None else grounding.get("submit_point")
    points_ok=isinstance(field,list) and isinstance(submit,list) and len(field)==len(submit)==2 and field!=submit and all(type(x) is int and 0<=x<1280 for x in field+submit)
    checks={"one_request_asset_digests_validated":feed["count"]==1 and feed["error"] is None,
      "raw_response_byte_preserved":raw_ok,"corrected_runner_one_message_one_turn_and_error_retained":process.get("assistant_message_count")==1 and process.get("completed_turn_count")==1 and process.get("ignored_non_assistant_item_completed_count")==1 and process.get("event_count")==5,
      "unchanged_main_schema_validation_pass":validation.get("status")=="PASS" and validation.get("schema_valid") is True,
      "unchanged_plain_parser_points_bounded_and_distinct":points_ok,"no_model_or_task_activity":True}
    receipt={"seed":284928,"status":"PASS_RESPONSE_REPLAY" if all(checks.values()) else "STOP_RESPONSE_REPLAY","checks":checks,
      "nested_container_invocations":1 if feed["count"]==1 else 0,"request_id":feed.get("request_id"),"request_asset_hashes_match":feed["error"] is None,
      "raw_response_sha256":sha(response_fixture),"replayed_response_sha256":feed.get("response_sha256"),"backend_error":error,
      "schema_validation":validation,"grounding":grounding,"runner_receipt":process,"task_started":False,
      "task_token_acquired":False,"host_broker_started":False,"host_codex_invoked":False,"model_calls":0,"authority_granted":False}
    (RUN/"replay-result.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"seed":284928,"status":receipt["status"],"checks":checks,"schema":validation.get("status"),"backend_error":error},sort_keys=True))
    return 0 if receipt["status"]=="PASS_RESPONSE_REPLAY" else 1
if __name__=="__main__": raise SystemExit(main())
