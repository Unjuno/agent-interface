from __future__ import annotations
import hashlib,json,os,runpy,shutil,subprocess,sys
from pathlib import Path
REPO=Path(os.environ["ISSUE_2849_REPO"]).resolve(); V2=REPO/"research/integration/issue_2849_task1_orbstack_smoke_v2"
RUN=Path(os.environ["ISSUE_2849_RUN_ROOT"]).resolve(); OUT=Path(os.environ["ISSUE_2849_RUN_DIR"]).resolve(); MIRROR=Path(os.environ["AGENT_INTERFACE_DOCKER_SCHEMA"]).resolve().parent
if int(os.environ.get("ISSUE_2849_SEED","0"))!=284930: raise RuntimeError("STOP_TASK_SEED_MISMATCH")
pre=json.loads((OUT/"pre-call-source-manifest.json").read_text())
if pre.get("status")!="FROZEN_BEFORE_FORMAL_TASK" or pre.get("seed")!=284930: raise RuntimeError("STOP_BAD_FREEZE")
if os.environ.get("DOCKER_HOST")!="unix:///var/run/docker.sock" or str(REPO) not in os.environ.get("PYTHONPATH","").split(":"): raise RuntimeError("STOP_SOCKET_OR_REPO_ROOT")
docker=subprocess.check_output(["docker","version","--format","{{.Server.Version}} {{.Server.Os}}/{{.Server.Arch}}"],text=True,timeout=20).strip()
if docker!="29.4.0 linux/arm64": raise RuntimeError("STOP_NESTED_DOCKER:"+docker)
for root in (REPO,REPO/"research/live_control",V2,REPO/"research/observation_tiles",REPO/"research/observation_gating",REPO/"research/real_apps_v1",REPO/"runtime"): sys.path.insert(0,str(root))
from model_call_backend_v1 import resolve
from docker_model_call_backend_v1 import call as selected_call
from scope_reconcile_v30 import reconcile_after_finish
import integrated_efficiency_client_v1 as client_module
from run_integrated_efficiency_live_v1 import run_task
client_module.HERE=V2; RuntimeClient=client_module.RuntimeClient
def forbidden(*_a,**_k): raise AssertionError("legacy backend invoked")
resolved=resolve(forbidden)
if (resolved.__module__,resolved.__name__)!=("docker_model_call_backend_v1","call"): raise RuntimeError("STOP_SELECTED_BACKEND")
calls=0
def model_call(root,prompt,image,contract,workspace):
    global calls
    calls+=1
    if calls!=1: raise RuntimeError("STOP_MODEL_CALL_LIMIT_NO_RETRY")
    source=Path(image).resolve(); dst=MIRROR/"image.png"
    if not source.is_file(): raise FileNotFoundError("STOP_SCREENSHOT_MISSING")
    digest=hashlib.sha256(source.read_bytes()).hexdigest(); shutil.copyfile(source,dst)
    if hashlib.sha256(dst.read_bytes()).hexdigest()!=digest: raise RuntimeError("STOP_SCREENSHOT_HASH_MISMATCH")
    (RUN/"model-image-bind.json").write_text(json.dumps({"image_sha256":digest,"source":str(source),"mirror":str(dst),"authority_granted":False},indent=2)+"\n")
    return resolved(root,prompt,dst,contract,MIRROR/"workspace")
def dump(path,value): path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(value,indent=2,sort_keys=True)+"\n")
def main():
    if sorted(p.name for p in OUT.iterdir())!=["pre-call-source-manifest.json"] or any((RUN/"ipc").iterdir()): raise RuntimeError("STOP_OUTPUT_NOT_FRESH")
    docker_check=subprocess.check_output(["docker","version","--format","{{.Server.Version}} {{.Server.Os}}/{{.Server.Arch}}"],text=True,timeout=20).strip()
    namespace=runpy.run_path(str(V2/"run_task1_smoke.py"),run_name="issue_2849_task1_v30")
    workspace=OUT/"workspace"; workspace.mkdir(); runtime_root=OUT/"runtime"
    with RuntimeClient(runtime_root,284930) as client:
        task=client.ready["goal"]["tasks"][0]
        if (task["task_id"],task["layout"],task["phase"])!=("task-1","A","cold"): raise RuntimeError("STOP_UNEXPECTED_FIRST_TASK")
        dump(OUT/"frozen-task.json",{"seed":284930,"task_id":task["task_id"],"layout":task["layout"],"phase":task["phase"],"token":task["token"],"url":task["url"],"route":"plain","maximum_image_model_calls":1})
        row,cached,detail=run_task(client,"plain",task,0,None,workspace,OUT/"model-calls/plain",model_call=model_call)
        dump(OUT/"trace-pre-finish.json",row)
        fixture=client.finish("issue-2849-task1-finish-reconcile-v30")
        history_path=client.runtime/"submission-history.jsonl"
        records=[json.loads(line) for line in history_path.read_text().splitlines()] if history_path.exists() else []
        task_for_scope={**task,"source_capture_ns":detail["source"]["capture_ns"]}
        row,matches,scope=reconcile_after_finish(row,records,task_for_scope)
        detail["trace"]=row; detail["submission_records"]=matches
        dump(OUT/"task-trace.json",row); dump(OUT/"task-detail.json",detail); dump(OUT/"six-task-fixture-evaluation.json",fixture); dump(OUT/"submission-history.snapshot.json",records)
        scope["full_six_task_fixture_success"]=fixture.get("success")
        dump(OUT/"task1-scope-result.json",scope)
    dump(RUN/"outer-runtime-receipt.json",{"status":"OUTER_RUN_RETURNED","seed":284930,"main_return":0 if scope["status"]=="PASS_TASK1_SCOPED" else 1,"calls":calls,"docker_version":docker_check,"selected_backend":[resolved.__module__,resolved.__name__],"finish_reconciliation":True,"authority_granted":False})
    return 0 if scope["status"]=="PASS_TASK1_SCOPED" else 1
if __name__=="__main__": raise SystemExit(main())
