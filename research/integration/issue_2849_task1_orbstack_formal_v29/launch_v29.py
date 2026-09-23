from __future__ import annotations
import hashlib,json,os,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]; HERE=Path(__file__).resolve().parent; RUN=HERE/"evidence/task1-seed-284929"; OUT=RUN/"task-run"
OUTER="sha256:436172d89b145c6a9f9a57e655422c9558b3b0235347dd77607e9d61bcfa6393"; INNER="sha256:5cc4d237e6af4548147ddfffc35413faf2487fd585f6a0216221f153f61cf073"
SOCKET=Path("/Users/taka/.orbstack/run/docker.sock")
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    pre=json.loads((OUT/"pre-call-source-manifest.json").read_text())
    if pre.get("seed")!=284929 or pre.get("status")!="FROZEN_BEFORE_FORMAL_TASK": raise RuntimeError("STOP_BAD_FREEZE")
    for row in pre["source_files"]:
        p=ROOT/row["path"]
        if not p.is_file() or sha(p)!=row["sha256"]: raise RuntimeError("STOP_SOURCE_CHANGED:"+row["path"])
    if sorted(p.name for p in OUT.iterdir())!=["pre-call-source-manifest.json"] or any((RUN/"ipc").iterdir()): raise RuntimeError("STOP_OUTPUT_NOT_FRESH")
    if not SOCKET.exists(): raise RuntimeError("STOP_SOCKET_MISSING")
    socket_check=subprocess.run(["docker","--context","orbstack","run","--rm","--network","none","--mount",f"type=bind,src={SOCKET},dst=/var/run/docker.sock","-e","DOCKER_HOST=unix:///var/run/docker.sock","--entrypoint","docker",OUTER,"version","--format","{{.Server.Version}} {{.Server.Os}}/{{.Server.Arch}}"],capture_output=True,text=True,timeout=45)
    if socket_check.returncode or socket_check.stdout.strip()!="29.4.0 linux/arm64": raise RuntimeError("STOP_SOCKET_PREFLIGHT:"+socket_check.stdout+socket_check.stderr)
    mirror=RUN/"host-model-mirror"; py=":".join(pre["PYTHONPATH"])
    env={"ISSUE_2849_REPO":str(ROOT),"ISSUE_2849_RUN_ROOT":str(RUN),"ISSUE_2849_RUN_DIR":str(OUT),"ISSUE_2849_SEED":"284929",
      "AGENT_INTERFACE_MODEL_BACKEND":"module","AGENT_INTERFACE_MODEL_CALL_MODULE":"docker_model_call_backend_v1",
      "AGENT_INTERFACE_DOCKER_RUNNER":str(mirror/"runner.py"),"AGENT_INTERFACE_DOCKER_SCHEMA":str(mirror/"schema.json"),
      "AGENT_INTERFACE_DOCKER_INSTRUCTIONS":str(mirror/"instructions.txt"),"AGENT_INTERFACE_DOCKER_IMAGE":INNER,"AGENT_INTERFACE_DOCKER_IPC":str(RUN/"ipc"),
      "DOCKER_HOST":"unix:///var/run/docker.sock","PYTHONPATH":py,"PYTHONDONTWRITEBYTECODE":"1"}
    broker_env=dict(os.environ); broker_env.update({"CODEX_EXE":"/opt/homebrew/bin/codex","HOST_MODEL_BROKER_TIMEOUT_S":"90"})
    broker_cmd=["python3",str(ROOT/"runtime/host_model_ipc_broker_v1.py"),"--ipc",str(RUN/"ipc"),"--repo",str(mirror),"--once"]
    outer_cmd=["docker","--context","orbstack","run","--rm","--network","none","--mount",f"type=bind,src={ROOT},dst={ROOT}","--mount",f"type=bind,src={SOCKET},dst=/var/run/docker.sock","--entrypoint","python3"]
    for k,v in env.items(): outer_cmd += ["-e",k+"="+v]
    outer_cmd += [OUTER,str(HERE/"run_task1_v29.py")]
    (RUN/"launch-command.json").write_text(json.dumps({"outer":outer_cmd,"broker":broker_cmd,"socket_preflight":{"returncode":socket_check.returncode,"stdout":socket_check.stdout.strip()},"max_model_calls":1,"no_retry":True,"authority_granted":False},indent=2)+"\n")
    broker=subprocess.Popen(broker_cmd,cwd=ROOT,env=broker_env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True); started=time.time_ns()
    try: proc=subprocess.run(outer_cmd,cwd=ROOT,capture_output=True,text=True,timeout=600); status="OUTER_RETURNED"; rc=proc.returncode; stdout=proc.stdout; stderr=proc.stderr
    except subprocess.TimeoutExpired as exc:
        status="STOP_OUTER_TIMEOUT_NO_RETRY"; rc=None; stdout=exc.stdout or ""; stderr=exc.stderr or ""
        if isinstance(stdout,bytes): stdout=stdout.decode(errors="replace")
        if isinstance(stderr,bytes): stderr=stderr.decode(errors="replace")
    (RUN/"outer.stdout.txt").write_text(stdout); (RUN/"outer.stderr.txt").write_text(stderr)
    try: bo,be=broker.communicate(timeout=3)
    except subprocess.TimeoutExpired: broker.terminate(); bo,be=broker.communicate(timeout=5)
    (RUN/"broker.stdout.txt").write_text(bo); (RUN/"broker.stderr.txt").write_text(be)
    req=list((RUN/"ipc").glob("*.request.json")); rsp=list((RUN/"ipc").glob("*.response.jsonl")); receipts=list((RUN/"ipc").glob("*.broker.json"))
    result={"seed":284929,"status":status,"started_ns":started,"outer_returncode":rc,"broker_returncode":broker.returncode,"counts":{"requests":len(req),"responses":len(rsp),"broker_receipts":len(receipts)},"max_host_model_calls":1,"authority_granted":False}
    (RUN/"launch-result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    return 0 if status=="OUTER_RETURNED" and rc==0 and len(req)==len(rsp)==len(receipts)==1 else 1
if __name__=="__main__": raise SystemExit(main())
