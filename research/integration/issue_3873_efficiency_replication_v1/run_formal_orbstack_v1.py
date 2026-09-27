"""Run the frozen finite allocation in OrbStack; host invokes this launcher."""
from __future__ import annotations
import hashlib, json, os, shutil, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OUT = HERE / "evidence/formal-seed-284937/run-01"
OUTER_IMAGE = "sha256:436172d89b145c6a9f9a57e655422c9558b3b0235347dd77607e9d61bcfa6393"
MODEL_IMAGE = "sha256:5cc4d237e6af4548147ddfffc35413faf2487fd585f6a0216221f153f61cf073"
RUNNER = HERE / "container_host_model_ipc_runner_v3.py"
BROKER = ROOT / "runtime/host_model_ipc_broker_v1.py"
CODEX = "/opt/homebrew/bin/codex"
SOCKET = Path("/Users/taka/.orbstack/run/docker.sock")

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p, x): Path(p).write_text(json.dumps(x, indent=2, sort_keys=True)+"\n")

def main():
    if OUT.exists(): raise SystemExit("STOP_OUTPUT_ALREADY_EXISTS")
    if not SOCKET.exists(): raise SystemExit("STOP_ORBSTACK_SOCKET_MISSING")
    lock=json.loads((HERE/"formal-source-lock.json").read_text())
    source_commit=subprocess.run(["git","-C",str(ROOT),"rev-parse","HEAD"],capture_output=True,
        text=True,check=True,timeout=10).stdout.strip()
    merge_base=subprocess.run(["git","-C",str(ROOT),"merge-base",source_commit,lock["base_commit"]],
        capture_output=True,text=True,check=True,timeout=10).stdout.strip()
    if merge_base!=lock["base_commit"]: raise SystemExit("STOP_BASE_COMMIT:"+source_commit+":"+merge_base)
    if OUTER_IMAGE!=lock["outer_image"]: raise SystemExit("STOP_OUTER_IMAGE_LOCK")
    if MODEL_IMAGE!=lock["model_runner_image"]: raise SystemExit("STOP_MODEL_IMAGE_LOCK")
    if sha(CODEX)!=lock["host_codex_cli"]["sha256"]: raise SystemExit("STOP_HOST_CODEX_HASH")
    version=subprocess.run([CODEX,"--version"],capture_output=True,text=True,check=True,timeout=15).stdout.strip()
    if lock["host_codex_cli"]["version"] not in version: raise SystemExit("STOP_HOST_CODEX_VERSION")
    daemon=subprocess.run(["docker","--context","orbstack","version","--format","{{.Server.Version}} {{.Server.Os}}/{{.Server.Arch}}"],
        capture_output=True,text=True,check=True,timeout=20).stdout.strip()
    if daemon!="29.4.0 linux/arm64": raise SystemExit("STOP_ORBSTACK_DAEMON_IDENTITY:"+daemon)
    for image,expected in (("issue-2849-task1-runtime:v3-20260921",OUTER_IMAGE),
                           ("issue2849-py312-pytest-jsonschema:v1",MODEL_IMAGE)):
        actual=subprocess.run(["docker","--context","orbstack","image","inspect",image,"--format","{{.Id}}"],
            capture_output=True,text=True,check=True,timeout=20).stdout.strip()
        if actual!=expected: raise SystemExit("STOP_IMAGE_ID:"+image+":"+actual)
    for name,digest in lock["harness_sources"].items():
        if sha(HERE/name)!=digest: raise SystemExit("STOP_HARNESS_SOURCE_HASH:"+name)
    for name,digest in lock["protocol_sources"].items():
        if sha(ROOT/"research/live_control"/name)!=digest: raise SystemExit("STOP_PROTOCOL_SOURCE_HASH:"+name)
    for name,digest in lock["support_sources"].items():
        if sha(ROOT/name)!=digest: raise SystemExit("STOP_SUPPORT_SOURCE_HASH:"+name)
    for name,digest in lock["environment_sources"].items():
        if sha(ROOT/name)!=digest: raise SystemExit("STOP_ENVIRONMENT_SOURCE_HASH:"+name)
    if sha(HERE/"construction-audit.py")!=lock["construction_audit"]["source_sha256"]:
        raise SystemExit("STOP_CONSTRUCTION_AUDITOR_SOURCE_HASH")
    closure_command=["docker","--context","orbstack","run","--rm","--pull=never","--network","none",
        "--read-only","--cpus=2","--memory=4g","--pids-limit=128",
        "--tmpfs","/tmp:rw,noexec,nosuid,size=128m","-v",f"{ROOT}:/repo:ro","-w","/repo",
        "--entrypoint","python3",OUTER_IMAGE,
        str(Path("/repo")/(HERE.relative_to(ROOT)/"test_import_closure_v1.py"))]
    closure=subprocess.run(closure_command,capture_output=True,text=True,timeout=60)
    if closure.returncode!=0 or "PASS_FORMAL_IMPORT_CLOSURE_NO_MODEL_CALLS" not in closure.stdout:
        write(HERE/"evidence/formal-launch-precall-stop-01.json",{
            "status":"STOP_PRECALL_IMPORT_CLOSURE_LAUNCH","returncode":closure.returncode,
            "stdout":closure.stdout,"stderr":closure.stderr,"formal_output_created":False,
            "host_model_calls":0,"retry_of_formal_allocation":False})
        raise SystemExit("STOP_FORMAL_IMPORT_CLOSURE:"+closure.stdout+closure.stderr)
    smoke=json.loads((HERE/"evidence/runner-smoke-v1/independent-audit.json").read_text())
    if smoke.get("status")!="PASS_RUNNER_COMMAND_SMOKE" or smoke.get("host_model_calls")!=0 or smoke.get("fake_ipc_requests")!=1:
        raise SystemExit("STOP_MODEL_RUNNER_COMMAND_SMOKE")
    smoke_hashes=lock["smoke_evidence"]["files"]
    for relative,digest in smoke_hashes.items():
        if sha(HERE/relative)!=digest: raise SystemExit("STOP_SMOKE_EVIDENCE_HASH:"+relative)
    startup=json.loads((HERE/"evidence/runtime-startup-smoke-v5/independent-audit.json").read_text())
    if startup.get("status")!="PASS_RUNTIME_STARTUP_NO_MODEL" or startup.get("host_model_calls")!=0 or startup.get("runtime_exit_code")!=0:
        raise SystemExit("STOP_RUNTIME_STARTUP_SMOKE")
    for relative,digest in lock["runtime_startup_smoke"]["files"].items():
        if sha(HERE/relative)!=digest: raise SystemExit("STOP_RUNTIME_STARTUP_EVIDENCE_HASH:"+relative)
    construction=json.loads((HERE/"evidence/construction-audit.json").read_text())
    if construction.get("status")!="PASS_CONSTRUCTION_LOCK" or construction.get("model_calls")!=0:
        raise SystemExit("STOP_CONSTRUCTION_AUDIT")
    if sha(HERE/"evidence/construction-audit.json")!=lock["construction_audit"]["result_sha256"]:
        raise SystemExit("STOP_CONSTRUCTION_AUDIT_HASH")
    OUT.mkdir(parents=True)
    (OUT / "logs").mkdir()
    write(OUT/"environment-gate.json",{"host_codex_sha256":sha(CODEX),"host_codex_version":version,
        "orbstack_daemon":daemon,"outer_image_id":OUTER_IMAGE,"model_runner_image_id":MODEL_IMAGE,
        "formal_import_closure":closure.stdout.strip(),"main_base_commit":lock["base_commit"],
        "source_commit":source_commit,"pre_calls_pass":True,"started_ns":time.time_ns()})
    formal_out=OUT/"formal-output";formal_out.mkdir()
    write(formal_out/"preregistration.json", {"schema":"integrated_efficiency_preregistration_v1",
        "status":"frozen_before_live_calls","study":"issue-3873-efficiency-replication-01",
        "seed":284937,"arm_order":["plain","ephemeral","persistent"],
        "task_calls":{"plain":6,"ephemeral":6,"persistent":2},
        "no_image_schema_preflights":3,"maximum_host_model_calls":17,"retry":False,
        "model":"gpt-5.6-luna","effort":"low","coordinate_click_actions_authorized":True,
        "host_OS_Gui_authority":False,"sources":lock["protocol_sources"],
        "scope":"one finite same-model allocation on deterministic local Chromium fixture; no production, population, human-speed, or general reliability claim"})
    env = {"ISSUE3824_OUT": str(OUT), "ISSUE3824_REPO": str(ROOT),
        "ISSUE3824_LIVE_SOURCE": str(ROOT / "research/live_control"),
        "ISSUE3824_RUNNER": str(RUNNER), "ISSUE3824_MODEL_IMAGE": MODEL_IMAGE,
        "ISSUE3824_RUNNER_IMAGE": MODEL_IMAGE, "ISSUE3824_OUTER_IMAGE": OUTER_IMAGE,
        "ISSUE3824_CODEX_EXE": CODEX,
        "HOST_MODEL_BROKER_TIMEOUT_S": "120", "DOCKER_HOST": "unix:///var/run/docker.sock",
        "AGENT_INTERFACE_MODEL_BACKEND": "module",
        "AGENT_INTERFACE_MODEL_CALL_MODULE": "issue3864_model_backend_v1"}
    command = ["docker", "--context", "orbstack", "run", "--rm", "--network", "none",
        "--shm-size=1g", "-v", f"{ROOT}:{ROOT}", "-v", f"{SOCKET}:/var/run/docker.sock",
        "--entrypoint", "python3"]
    for key, value in env.items(): command += ["-e", f"{key}={value}"]
    command += [OUTER_IMAGE, str(HERE / "run_formal_inner_v1.py")]
    write(OUT / "outer-command.json", {"command": command, "seed": 284937,
        "maximum_host_cli_calls": 17, "outer_network": "none", "retry": False,
        "authority_granted": False, "started_ns": time.time_ns()})
    outer = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    broker_results=[]; started=time.monotonic(); seen=set(); stop=None
    try:
        while outer.poll() is None:
            requests = sorted(OUT.glob("ipc/request-*/*.request.json"))
            for request_file in requests:
                folder=request_file.parent
                if folder in seen: continue
                seen.add(folder)
                if len(seen)>17:
                    stop="STOP_17_CALL_LIMIT";outer.terminate();break
                repo=OUT / "broker-mirrors" / folder.name
                broker_cmd=[sys.executable, str(BROKER), "--ipc", str(folder), "--repo", str(repo), "--once"]
                broker_env=os.environ.copy();broker_env.update(CODEX_EXE=CODEX, HOST_MODEL_BROKER_TIMEOUT_S="120")
                result=subprocess.run(broker_cmd, env=broker_env, capture_output=True, text=True, timeout=140)
                (OUT/"logs"/(folder.name+".broker.stdout.txt")).write_text(result.stdout)
                (OUT/"logs"/(folder.name+".broker.stderr.txt")).write_text(result.stderr)
                broker_results.append({"request_dir":str(folder),"returncode":result.returncode,
                    "request_count":len(list(folder.glob("*.request.json"))),
                    "response_count":len(list(folder.glob("*.response.jsonl"))),
                    "receipt_count":len(list(folder.glob("*.broker.json")))})
                if result.returncode != 0:
                    stop="STOP_BROKER_FAILURE";outer.terminate();break
            if stop: break
            if time.monotonic()-started>3600:
                stop="STOP_OUTER_WALL_TIMEOUT_NO_RETRY";outer.terminate();break
            time.sleep(.05)
        try: stdout,stderr=outer.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            outer.kill();stdout,stderr=outer.communicate()
            stop=stop or "STOP_OUTER_TERMINATION_TIMEOUT"
    except Exception as exc:
        stop=stop or ("STOP_LAUNCHER:"+type(exc).__name__)
        outer.terminate();stdout,stderr=outer.communicate(timeout=10)
    (OUT/"logs/outer.stdout.txt").write_text(stdout)
    (OUT/"logs/outer.stderr.txt").write_text(stderr)
    total_requests=len(list(OUT.glob("ipc/request-*/*.request.json")))
    total_responses=len(list(OUT.glob("ipc/request-*/*.response.jsonl")))
    total_receipts=len(list(OUT.glob("ipc/request-*/*.broker.json")))
    status="RETURNED" if stop is None and outer.returncode==0 else (stop or "STOP_OUTER_NONZERO")
    write(OUT/"launcher-result.json", {"status":status,"outer_returncode":outer.returncode,
        "broker_invocations":len(broker_results),"broker_results":broker_results,
        "request_count":total_requests,"response_count":total_responses,
        "broker_receipt_count":total_receipts,"maximum_host_cli_calls":17,
        "retry_count":0,"authority_granted":False,"ended_ns":time.time_ns()})
    if status=="RETURNED":
        audit=subprocess.run([sys.executable,str(HERE/"audit_formal_orbstack_v1.py"),str(OUT)],
            cwd=ROOT,capture_output=True,text=True,check=False,timeout=60)
        (OUT/"logs/independent-audit.stdout.txt").write_text(audit.stdout)
        (OUT/"logs/independent-audit.stderr.txt").write_text(audit.stderr)
        if audit.returncode!=0: status="HOLD_INDEPENDENT_AUDIT_FAILURE"
    result_path=OUT/"launcher-result.json"
    result=json.loads(result_path.read_text());result["status"]=status
    write(result_path,result)
    return 0 if status=="RETURNED" else 1

if __name__=="__main__": raise SystemExit(main())
