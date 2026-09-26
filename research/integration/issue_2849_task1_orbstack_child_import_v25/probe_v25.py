from __future__ import annotations
import hashlib,json,subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]; HERE=Path(__file__).resolve().parent
RUN=HERE/"evidence/seed-284925"
OUTER="sha256:436172d89b145c6a9f9a57e655422c9558b3b0235347dd77607e9d61bcfa6393"
V2=ROOT/"research/integration/issue_2849_task1_orbstack_smoke_v2"
IMPORTS=["event_socket_v11","cause_servo_interactive_v4","executor_v4","session_v33","integrated_efficiency_client_v1","integrated_efficiency_runtime_task1_v2"]
PATHS=[ROOT/"research/live_control",V2,ROOT/"research/observation_tiles",ROOT/"research/observation_gating",ROOT/"research/real_apps_v1",ROOT/"runtime"]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    if RUN.exists(): raise RuntimeError("STOP_EVIDENCE_PATH_EXISTS")
    image=subprocess.check_output(["docker","--context","orbstack","image","inspect",OUTER,"--format","{{.Id}} {{.Architecture}}"],text=True,timeout=20).strip()
    if image!="sha256:436172d89b145c6a9f9a57e655422c9558b3b0235347dd77607e9d61bcfa6393 arm64": raise RuntimeError("STOP_OUTER_IMAGE_CHANGED")
    RUN.mkdir(parents=True)
    pythonpath=":".join(str(p) for p in PATHS)
    code=("import importlib, json; names="+repr(IMPORTS)+"; "+
          "[importlib.import_module(name) for name in names]; "+
          "print(json.dumps({'imports':names,'task_started':False,'task_token_acquired':False,'gui_started':False,'broker_started':False,'model_calls':0}))")
    outer=["docker","--context","orbstack","run","--rm","--network","none","--mount",f"type=bind,src={ROOT},dst={ROOT}",
      "-e","PYTHONPATH="+pythonpath,"-e","PYTHONDONTWRITEBYTECODE=1","--entrypoint","python3",OUTER,"-c",
      "import os,subprocess,json,sys; p=subprocess.run([sys.executable,'-B','-c',"+repr(code)+"],env=os.environ.copy(),capture_output=True,text=True,timeout=30); print(json.dumps({'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}))"]
    frozen={"seed":284925,"preregistration_comment":5752101960,"main_commit":subprocess.check_output(["git","rev-parse","origin/main"],cwd=ROOT,text=True).strip(),
      "outer_image":image,"probe_sha256":sha(Path(__file__)),"readme_sha256":sha(HERE/"README.md"),"imports":IMPORTS,
      "pythonpath":[str(p) for p in PATHS],"authority_granted":False,"task_started":False,"model_calls":0}
    (RUN/"frozen-inputs.json").write_text(json.dumps(frozen,indent=2,sort_keys=True)+"\n")
    result=subprocess.run(outer,cwd=ROOT,capture_output=True,text=True,timeout=60,check=False)
    try: child=json.loads(result.stdout.splitlines()[-1])
    except (ValueError,IndexError): child=None
    imported=False
    if child and child.get("returncode")==0:
      try: imported=json.loads(child["stdout"].splitlines()[-1]).get("imports")==IMPORTS
      except (ValueError,IndexError): pass
    checks={"pinned_outer_image":True,"outer_network_disabled":outer[outer.index("--network")+1]=="none",
      "child_imports_all_expected_modules":imported,"outer_returned_zero":result.returncode==0,
      "no_task_gui_broker_or_model":True}
    receipt={"seed":284925,"status":"PASS_CHILD_IMPORTS" if all(checks.values()) else "STOP_CHILD_IMPORTS","checks":checks,
      "child":child,"outer_returncode":result.returncode,"outer_stdout":result.stdout[-3000:],"outer_stderr":result.stderr[-3000:],
      "task_started":False,"task_token_acquired":False,"gui_started":False,"broker_started":False,"model_calls":0,"authority_granted":False}
    (RUN/"probe-result.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    files=sorted(p for p in RUN.rglob("*") if p.is_file() and p.name!="SHA256SUMS")
    (RUN/"SHA256SUMS").write_text("".join(f"{sha(p)}  {p.relative_to(RUN)}\n" for p in files))
    return 0 if receipt["status"]=="PASS_CHILD_IMPORTS" else 1
if __name__=="__main__": raise SystemExit(main())
