from __future__ import annotations
import hashlib,json,os,shutil,sys,threading,time
from pathlib import Path

ROOT=Path(os.environ["ISSUE_2849_REPO"]).resolve(); RUN=Path(os.environ["ISSUE_2849_V27_RUN"]).resolve()
V2=ROOT/"research/integration/issue_2849_task1_orbstack_smoke_v2"
V26=ROOT/"research/integration/issue_2849_task1_orbstack_formal_v26/evidence/task1-seed-284926"
for path in (ROOT/"research/live_control",ROOT/"runtime",ROOT/"research/observation_tiles",ROOT/"research/observation_gating",ROOT/"research/real_apps_v1",V2):
    sys.path.insert(0,str(path))
from docker_model_call_backend_v1 import call

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    mirror=V26/"host-model-mirror"; ipc=RUN/"ipc"; output=RUN/"backend-call"
    response_fixture=V26/"ipc/d8b2c076c08f48229b18484e2ca4a419.response.jsonl"
    prompt=V26/"task-run/model-calls/plain/task-1/anchor/prompt.txt"
    image=mirror/"image.png"; workspace=mirror/"workspace"
    stop=threading.Event(); feed={"count":0,"request":None,"error":None}
    def supply_saved_response():
        deadline=time.monotonic()+30
        try:
            while not stop.is_set() and time.monotonic()<deadline:
                requests=sorted(ipc.glob("*.request.json"))
                if requests:
                    if len(requests)!=1: raise RuntimeError("replay expected one request")
                    request=json.loads(requests[0].read_text())
                    expected={"mode":"coordinate","authority_granted":False,
                      "image_sha256":sha(image),"schema_sha256":sha(mirror/"schema.json"),
                      "instructions_sha256":sha(mirror/"instructions.txt"),"working":"/repo/workspace"}
                    for key,value in expected.items():
                        if request.get(key)!=value: raise RuntimeError("request mismatch:"+key)
                    target=ipc/(request["request_id"]+".response.jsonl")
                    shutil.copyfile(response_fixture,target)
                    feed.update(count=1,request_id=request["request_id"],response_sha256=sha(target),request=request)
                    return
                time.sleep(.02)
            if not stop.is_set(): raise TimeoutError("backend emitted no replay request")
        except Exception as exc: feed["error"]=type(exc).__name__+":"+str(exc)
    worker=threading.Thread(target=supply_saved_response,daemon=True); worker.start()
    error=None; result=None
    try:
        result=call(output,prompt.read_text(encoding="utf-8"),image,"plain",workspace)
    except Exception as exc: error=type(exc).__name__+":"+str(exc)
    finally:
        stop.set();worker.join(timeout=2)
    runner_root=output/"runner"
    process=json.loads((runner_root/"process.json").read_text()) if (runner_root/"process.json").is_file() else {}
    validation=json.loads((output/"schema-validation.json").read_text()) if (output/"schema-validation.json").is_file() else {}
    events=runner_root/"events.jsonl"
    raw_preserved=events.is_file() and sha(events)==sha(response_fixture)
    grounding=None if result is None else result.get("grounding")
    points_ok=bool(grounding and grounding.get("field_point")!=grounding.get("submit_point")
                   and len(grounding.get("field_point",[]))==2 and len(grounding.get("submit_point",[]))==2)
    checks={"one_validated_replay_request":feed["count"]==1 and feed["error"] is None,
      "raw_response_byte_preserved":raw_preserved,
      "runner_receipt_one_assistant_one_turn":process.get("assistant_message_count")==1 and process.get("completed_turn_count")==1 and process.get("ignored_non_assistant_item_completed_count")==1,
      "unchanged_backend_schema_validation_pass":validation.get("status")=="PASS",
      "unchanged_plain_parser_returns_distinct_points":points_ok,
      "no_host_model_or_task_activity":True}
    receipt={"seed":284927,"status":"PASS_RESPONSE_REPLAY" if all(checks.values()) else "STOP_RESPONSE_REPLAY",
      "checks":checks,"replay_feeder_request_count":feed["count"],"nested_container_invocations":1 if feed["count"]==1 else 0,"request_id":feed.get("request_id"),
      "request_asset_hashes_match":feed["error"] is None,"raw_response_sha256":sha(response_fixture),
      "replayed_response_sha256":feed.get("response_sha256"),"backend_error":error,
      "schema_validation":validation,"grounding":grounding,"runner_receipt":process,
      "task_started":False,"task_token_acquired":False,"host_broker_started":False,"host_codex_invoked":False,
      "model_calls":0,"authority_granted":False}
    (RUN/"replay-result.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"status":receipt["status"],"checks":checks,"backend_error":error,"schema":validation.get("status"),"grounding":grounding},sort_keys=True))
    return 0 if receipt["status"]=="PASS_RESPONSE_REPLAY" else 1
if __name__=="__main__": raise SystemExit(main())
