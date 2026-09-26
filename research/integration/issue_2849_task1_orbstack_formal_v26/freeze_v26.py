from __future__ import annotations
import hashlib,json,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]; HERE=Path(__file__).resolve().parent; RUN=HERE/"evidence/task1-seed-284926"; OUT=RUN/"task-run"
V2=ROOT/"research/integration/issue_2849_task1_orbstack_smoke_v2"; PRIOR=V2/"evidence/formal-task1-seed-284902/pre-call-source-manifest.json"
LOCAL=[HERE/"README.md",HERE/"freeze_v26.py",HERE/"run_task1_v26.py",HERE/"launch_v26.py",HERE/"audit_v26.py"]
OUTER="issue-2849-task1-runtime:v3-20260921"; INNER="sha256:5cc4d237e6af4548147ddfffc35413faf2487fd585f6a0216221f153f61cf073"
def sha(b): return hashlib.sha256(b).hexdigest()
def main():
    if RUN.exists(): raise RuntimeError("STOP_RUN_PATH_EXISTS")
    main_sha=subprocess.check_output(["git","rev-parse","origin/main"],cwd=ROOT,text=True).strip()
    if main_sha!="4b2e84b79633281138b6f72c70e98d5fe9a5bf95": raise RuntimeError("STOP_MAIN_MOVED:"+main_sha)
    prior=json.loads(PRIOR.read_text()); entries=[]
    for item in prior["source_files"]:
        rel=item["path"]; path=ROOT/rel
        if not path.is_file() or sha(path.read_bytes())!=item["sha256"]: raise RuntimeError("STOP_PREDECESSOR_SOURCE_CHANGED:"+rel)
        remote=subprocess.check_output(["git","show",f"origin/main:{rel}"],cwd=ROOT,stderr=subprocess.DEVNULL)
        if sha(remote)!=item["sha256"]: raise RuntimeError("STOP_SOURCE_NOT_CURRENT_MAIN:"+rel)
        entries.append({"path":rel,"sha256":item["sha256"],"origin":"main"})
    for path in LOCAL: entries.append({"path":str(path.relative_to(ROOT)),"sha256":sha(path.read_bytes()),"origin":"successor"})
    sys.path.insert(0,str(ROOT)); from runtime.host_model_ipc_broker_v1 import executable_identity
    cli=executable_identity("/opt/homebrew/bin/codex")
    if cli["version"]!="codex-cli 0.146.1" or cli["sha256"]!="35d248101b211d6248ad4e6b8c1d441fe81236da87afb9f3e9ea51a049e9f179": raise RuntimeError("STOP_CODEX_IDENTITY")
    outer=subprocess.check_output(["docker","--context","orbstack","image","inspect",OUTER,"--format","{{.Id}} {{.Architecture}}"],text=True).strip()
    inner=subprocess.check_output(["docker","--context","orbstack","image","inspect",INNER,"--format","{{.Id}} {{.Architecture}}"],text=True).strip()
    if outer!="sha256:436172d89b145c6a9f9a57e655422c9558b3b0235347dd77607e9d61bcfa6393 arm64" or inner!="sha256:5cc4d237e6af4548147ddfffc35413faf2487fd585f6a0216221f153f61cf073 arm64": raise RuntimeError("STOP_IMAGE_IDENTITY")
    mirror=RUN/"host-model-mirror"; (mirror/"workspace").mkdir(parents=True); (RUN/"ipc").mkdir(parents=True); OUT.mkdir(parents=True)
    shutil.copyfile(ROOT/"research/live_control/container_host_model_ipc_runner_v1.py",mirror/"runner.py")
    shutil.copyfile(ROOT/"research/live_control/plain_form_points_schema_v1.json",mirror/"schema.json")
    shutil.copyfile(ROOT/"research/live_control/plain_form_points_responder_v1.txt",mirror/"instructions.txt")
    manifest={"status":"FROZEN_BEFORE_FORMAL_TASK","issue":2849,"seed":284926,"main_commit":main_sha,"task_scope":"task-1/layout-A/cold/plain",
      "model_call_limit":1,"no_retry":True,"authority_granted":False,"source_files":entries,"source_file_count":len(entries),
      "predecessor_source_closure_count":len(prior["source_files"]),"outer_image":outer,"nested_image":inner,"host_model_cli":cli,
      "PYTHONPATH":[str(ROOT/"research/live_control"),str(V2),str(ROOT/"research/observation_tiles"),str(ROOT/"research/observation_gating"),str(ROOT/"research/real_apps_v1"),str(ROOT/"runtime")],
      "host_mirror":str(mirror),"ipc":str(RUN/"ipc"),"outer_network":"none","nested_network":"none"}
    (OUT/"pre-call-source-manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"status":manifest["status"],"main":main_sha,"source_count":len(entries),"codex":cli["version"],"outer":outer,"nested":inner},indent=2))
if __name__=="__main__": main()
