from __future__ import annotations
import hashlib,json,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]; HERE=Path(__file__).resolve().parent
RUN=HERE/"evidence/task1-seed-284929"; OUT=RUN/"task-run"
V2=ROOT/"research/integration/issue_2849_task1_orbstack_smoke_v2"
PRIOR=V2/"evidence/formal-task1-seed-284902/pre-call-source-manifest.json"
V27=ROOT/"research/integration/issue_2849_task1_orbstack_runner_replay_v27/runner_v27.py"
OUTER="sha256:436172d89b145c6a9f9a57e655422c9558b3b0235347dd77607e9d61bcfa6393"
INNER="sha256:5cc4d237e6af4548147ddfffc35413faf2487fd585f6a0216221f153f61cf073"
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def cmd(args): return subprocess.check_output(args,cwd=ROOT,text=True).strip()
def main():
    if RUN.exists(): raise RuntimeError("STOP_RUN_PATH_EXISTS")
    main_sha=cmd(["git","rev-parse","origin/main"])
    expected="4b2e84b79633281138b6f72c70e98d5fe9a5bf95"
    if main_sha!=expected: raise RuntimeError("STOP_MAIN_MOVED:"+main_sha)
    prior=json.loads(PRIOR.read_text()); sources=[]
    for item in prior["source_files"]:
        rel=item["path"]; path=ROOT/rel
        if not path.is_file() or sha(path)!=item["sha256"]: raise RuntimeError("STOP_PREDECESSOR_SOURCE_CHANGED:"+rel)
        if sha_bytes(subprocess.check_output(["git","show",f"origin/main:{rel}"],cwd=ROOT,stderr=subprocess.DEVNULL))!=item["sha256"]:
            raise RuntimeError("STOP_SOURCE_NOT_CURRENT_MAIN:"+rel)
        sources.append({"path":rel,"sha256":item["sha256"],"origin":"main"})
    local=[HERE/"README.md",HERE/"freeze_v29.py",HERE/"run_task1_v29.py",HERE/"launch_v29.py",HERE/"audit_v29.py",V27]
    for p in local: sources.append({"path":str(p.relative_to(ROOT)),"sha256":sha(p),"origin":"successor"})
    sys.path.insert(0,str(ROOT)); from runtime.host_model_ipc_broker_v1 import executable_identity
    cli=executable_identity("/opt/homebrew/bin/codex")
    if cli.get("version")!="codex-cli 0.146.1" or cli.get("sha256")!="35d248101b211d6248ad4e6b8c1d441fe81236da87afb9f3e9ea51a049e9f179": raise RuntimeError("STOP_CODEX_IDENTITY")
    outer=cmd(["docker","--context","orbstack","image","inspect",OUTER,"--format","{{.Id}} {{.Architecture}}"])
    inner=cmd(["docker","--context","orbstack","image","inspect",INNER,"--format","{{.Id}} {{.Architecture}}"])
    if outer!=OUTER+" arm64" or inner!=INNER+" arm64": raise RuntimeError("STOP_IMAGE_IDENTITY")
    docker=cmd(["docker","--context","orbstack","version","--format","{{.Server.Version}} {{.Server.Os}}/{{.Server.Arch}}"])
    if docker!="29.4.0 linux/arm64": raise RuntimeError("STOP_DOCKER_SERVER:"+docker)
    mirror=RUN/"host-model-mirror"; (mirror/"workspace").mkdir(parents=True); (RUN/"ipc").mkdir(); OUT.mkdir(parents=True)
    shutil.copyfile(ROOT/"research/live_control/plain_form_points_schema_v1.json",mirror/"schema.json")
    shutil.copyfile(ROOT/"research/live_control/plain_form_points_responder_v1.txt",mirror/"instructions.txt")
    shutil.copyfile(V27,mirror/"runner.py")
    closure=[ROOT,ROOT/"research/live_control",V2,ROOT/"research/observation_tiles",ROOT/"research/observation_gating",ROOT/"research/real_apps_v1",ROOT/"runtime"]
    manifest={"status":"FROZEN_BEFORE_FORMAL_TASK","issue":2849,"seed":284929,"main_commit":main_sha,
      "task_scope":"task-1/layout-A/cold/plain","model_call_limit":1,"no_retry":True,"authority_granted":False,
      "source_files":sources,"source_file_count":len(sources),"predecessor_source_closure_count":len(prior["source_files"]),
      "outer_image":outer,"nested_image":inner,"docker_server":docker,"host_model_cli":cli,
      "PYTHONPATH":[str(p) for p in closure],"host_mirror":str(mirror),"ipc":str(RUN/"ipc"),
      "outer_network":"none","nested_network":"none","candidate_runner_sha256":sha(mirror/"runner.py"),
      "schema_sha256":sha(mirror/"schema.json"),"instructions_sha256":sha(mirror/"instructions.txt")}
    (OUT/"pre-call-source-manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"status":manifest["status"],"seed":284929,"main":main_sha,"source_count":len(sources),"outer":outer,"nested":inner,"docker":docker,"codex":cli["version"]},sort_keys=True))
def sha_bytes(data): return hashlib.sha256(data).hexdigest()
if __name__=="__main__": main()
