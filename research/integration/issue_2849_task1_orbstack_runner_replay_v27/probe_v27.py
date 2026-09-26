from __future__ import annotations
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]; HERE=Path(__file__).resolve().parent; RUN=HERE/"evidence/seed-284927"
OUTER="sha256:436172d89b145c6a9f9a57e655422c9558b3b0235347dd77607e9d61bcfa6393"
INNER="sha256:5cc4d237e6af4548147ddfffc35413faf2487fd585f6a0216221f153f61cf073"
SOCKET=Path("/Users/taka/.orbstack/run/docker.sock")
V26=ROOT/"research/integration/issue_2849_task1_orbstack_formal_v26/evidence/task1-seed-284926"
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    if RUN.exists(): raise RuntimeError("STOP_EVIDENCE_PATH_EXISTS")
    response=V26/"ipc/d8b2c076c08f48229b18484e2ca4a419.response.jsonl"
    image=V26/"host-model-mirror/image.png"; schema=V26/"host-model-mirror/schema.json"
    instructions=V26/"host-model-mirror/instructions.txt"; prompt=V26/"task-run/model-calls/plain/task-1/anchor/prompt.txt"
    outer_id=subprocess.check_output(["docker","--context","orbstack","image","inspect",OUTER,"--format","{{.Id}} {{.Architecture}}"],text=True,timeout=20).strip()
    inner_id=subprocess.check_output(["docker","--context","orbstack","image","inspect",INNER,"--format","{{.Id}} {{.Architecture}}"],text=True,timeout=20).strip()
    if outer_id!=OUTER+" arm64" or inner_id!=INNER+" arm64": raise RuntimeError("STOP_IMAGE_IDENTITY")
    (RUN/"ipc").mkdir(parents=True)
    pythonpath=[ROOT/"research/live_control",ROOT/"runtime",ROOT/"research/observation_tiles",ROOT/"research/observation_gating",ROOT/"research/real_apps_v1",ROOT/"research/integration/issue_2849_task1_orbstack_smoke_v2"]
    local=[HERE/"README.md",HERE/"runner_v27.py",HERE/"harness_v27.py",HERE/"probe_v27.py",HERE/"audit_v27.py"]
    frozen={"issue":2849,"seed":284927,"preregistration_comment":5752154722,
      "main_commit":subprocess.check_output(["git","rev-parse","origin/main"],cwd=ROOT,text=True).strip(),
      "outer_image":outer_id,"nested_image":inner_id,"local_sources":{str(p.relative_to(ROOT)):sha(p) for p in local},
      "predecessor_response_sha256":sha(response),"screenshot_sha256":sha(image),"schema_sha256":sha(schema),
      "instructions_sha256":sha(instructions),"prompt_sha256":sha(prompt),"authority_granted":False,
      "task_started":False,"model_calls":0,"maximum_outer_invocations":1,"maximum_nested_invocations":1}
    (RUN/"frozen-inputs.json").write_text(json.dumps(frozen,indent=2,sort_keys=True)+"\n")
    env={"ISSUE_2849_REPO":str(ROOT),"ISSUE_2849_V27_RUN":str(RUN),"DOCKER_HOST":"unix:///var/run/docker.sock",
      "PYTHONPATH":":".join(str(p) for p in pythonpath),"PYTHONDONTWRITEBYTECODE":"1",
      "AGENT_INTERFACE_DOCKER_RUNNER":str(HERE/"runner_v27.py"),"AGENT_INTERFACE_DOCKER_SCHEMA":str(schema),
      "AGENT_INTERFACE_DOCKER_INSTRUCTIONS":str(instructions),"AGENT_INTERFACE_DOCKER_IMAGE":INNER,
      "AGENT_INTERFACE_DOCKER_IPC":str(RUN/"ipc"),"DOCKER":"docker"}
    command=["docker","--context","orbstack","run","--rm","--network","none","--mount",f"type=bind,src={ROOT},dst={ROOT}",
      "--mount",f"type=bind,src={SOCKET},dst=/var/run/docker.sock","--entrypoint","python3"]
    for key,value in env.items(): command += ["-e",key+"="+value]
    command += [OUTER,str(HERE/"harness_v27.py")]
    result=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=150,check=False)
    (RUN/"outer-result.json").write_text(json.dumps({"outer_returncode":result.returncode,"outer_stdout":result.stdout[-4000:],
      "outer_stderr":result.stderr[-4000:],"command":command,"seed":284927,"outer_invocations":1,"authority_granted":False},indent=2,sort_keys=True)+"\n")
    replay_path=RUN/"replay-result.json"
    if replay_path.exists():
      replay=json.loads(replay_path.read_text()); replay["checks"]["outer_returned_zero"]=result.returncode==0
      replay["status"]="PASS_RESPONSE_REPLAY" if all(replay["checks"].values()) else "STOP_RESPONSE_REPLAY"
      replay_path.write_text(json.dumps(replay,indent=2,sort_keys=True)+"\n"); status=replay["status"]
    else: status="STOP_OUTER_NO_REPLAY_RECEIPT"
    files=sorted(p for p in RUN.rglob("*") if p.is_file() and p.name!="SHA256SUMS")
    (RUN/"SHA256SUMS").write_text("".join(f"{sha(p)}  {p.relative_to(RUN)}\n" for p in files))
    return 0 if status=="PASS_RESPONSE_REPLAY" else 1
if __name__=="__main__": raise SystemExit(main())
