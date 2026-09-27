from __future__ import annotations
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]; HERE=Path(__file__).resolve().parent; RUN=HERE/"evidence/seed-284928"
V27=ROOT/"research/integration/issue_2849_task1_orbstack_runner_replay_v27"; V26=ROOT/"research/integration/issue_2849_task1_orbstack_formal_v26/evidence/task1-seed-284926"
OUTER="sha256:436172d89b145c6a9f9a57e655422c9558b3b0235347dd77607e9d61bcfa6393"; INNER="sha256:5cc4d237e6af4548147ddfffc35413faf2487fd585f6a0216221f153f61cf073"
SOCKET=Path("/Users/taka/.orbstack/run/docker.sock")
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    if RUN.exists(): raise RuntimeError("STOP_EVIDENCE_PATH_EXISTS")
    response=V26/"ipc/d8b2c076c08f48229b18484e2ca4a419.response.jsonl"; mirror=V26/"host-model-mirror"
    outer_id=subprocess.check_output(["docker","--context","orbstack","image","inspect",OUTER,"--format","{{.Id}} {{.Architecture}}"],text=True,timeout=20).strip()
    inner_id=subprocess.check_output(["docker","--context","orbstack","image","inspect",INNER,"--format","{{.Id}} {{.Architecture}}"],text=True,timeout=20).strip()
    if outer_id!=OUTER+" arm64" or inner_id!=INNER+" arm64": raise RuntimeError("STOP_IMAGE_IDENTITY")
    (RUN/"ipc").mkdir(parents=True)
    sources=[HERE/"README.md",HERE/"harness_v28.py",HERE/"probe_v28.py",HERE/"audit_v28.py",V27/"runner_v27.py"]
    frozen={"issue":2849,"seed":284928,"preregistration_comment":5752189295,
      "main_commit":subprocess.check_output(["git","rev-parse","origin/main"],cwd=ROOT,text=True).strip(),
      "outer_image":outer_id,"nested_image":inner_id,"source_hashes":{str(p.relative_to(ROOT)):sha(p) for p in sources},
      "response_sha256":sha(response),"screenshot_sha256":sha(mirror/"image.png"),"schema_sha256":sha(mirror/"schema.json"),
      "instructions_sha256":sha(mirror/"instructions.txt"),"prompt_sha256":sha(V26/"task-run/model-calls/plain/task-1/anchor/prompt.txt"),
      "task_started":False,"host_model_calls":0,"authority_granted":False,"max_outer":1,"max_nested":1}
    (RUN/"frozen-inputs.json").write_text(json.dumps(frozen,indent=2,sort_keys=True)+"\n")
    py=[ROOT,ROOT/"research/live_control",ROOT/"runtime",ROOT/"research/observation_tiles",ROOT/"research/observation_gating",ROOT/"research/real_apps_v1",ROOT/"research/integration/issue_2849_task1_orbstack_smoke_v2"]
    env={"ISSUE_2849_REPO":str(ROOT),"ISSUE_2849_V28_RUN":str(RUN),"DOCKER_HOST":"unix:///var/run/docker.sock","PYTHONPATH":":".join(map(str,py)),"PYTHONDONTWRITEBYTECODE":"1",
      "AGENT_INTERFACE_DOCKER_RUNNER":str(V27/"runner_v27.py"),"AGENT_INTERFACE_DOCKER_SCHEMA":str(mirror/"schema.json"),"AGENT_INTERFACE_DOCKER_INSTRUCTIONS":str(mirror/"instructions.txt"),
      "AGENT_INTERFACE_DOCKER_IMAGE":INNER,"AGENT_INTERFACE_DOCKER_IPC":str(RUN/"ipc"),"DOCKER":"docker"}
    cmd=["docker","--context","orbstack","run","--rm","--network","none","--mount",f"type=bind,src={ROOT},dst={ROOT}","--mount",f"type=bind,src={SOCKET},dst=/var/run/docker.sock","--entrypoint","python3"]
    for k,v in env.items(): cmd += ["-e",k+"="+v]
    cmd += [OUTER,str(HERE/"harness_v28.py")]
    proc=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=150,check=False)
    (RUN/"outer-result.json").write_text(json.dumps({"seed":284928,"outer_invocations":1,"outer_returncode":proc.returncode,"stdout":proc.stdout[-4000:],"stderr":proc.stderr[-4000:],"authority_granted":False},indent=2,sort_keys=True)+"\n")
    result_path=RUN/"replay-result.json"
    if result_path.exists():
      result=json.loads(result_path.read_text()); result["checks"]["outer_returned_zero"]=proc.returncode==0
      result["status"]="PASS_RESPONSE_REPLAY" if all(result["checks"].values()) else "STOP_RESPONSE_REPLAY"
      result_path.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n");status=result["status"]
    else: status="STOP_OUTER_NO_REPLAY_RESULT"
    files=sorted(p for p in RUN.rglob("*") if p.is_file() and p.name!="SHA256SUMS")
    (RUN/"SHA256SUMS").write_text("".join(f"{sha(p)}  {p.relative_to(RUN)}\n" for p in files))
    return 0 if status=="PASS_RESPONSE_REPLAY" else 1
if __name__=="__main__": raise SystemExit(main())
