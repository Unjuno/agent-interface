from __future__ import annotations
import hashlib,json,os,runpy,shutil,subprocess,sys
from pathlib import Path
REPO=Path(os.environ["ISSUE_2849_REPO"]).resolve(); V2=REPO/"research/integration/issue_2849_task1_orbstack_smoke_v2"
RUN=Path(os.environ["ISSUE_2849_RUN_ROOT"]).resolve(); OUT=Path(os.environ["ISSUE_2849_RUN_DIR"]).resolve(); MIRROR=Path(os.environ["AGENT_INTERFACE_DOCKER_SCHEMA"]).resolve().parent
if int(os.environ.get("ISSUE_2849_SEED","0"))!=284929: raise RuntimeError("STOP_TASK_SEED_MISMATCH")
pre=json.loads((OUT/"pre-call-source-manifest.json").read_text())
if pre.get("status")!="FROZEN_BEFORE_FORMAL_TASK" or pre.get("seed")!=284929: raise RuntimeError("STOP_BAD_FREEZE")
if os.environ.get("DOCKER_HOST")!="unix:///var/run/docker.sock": raise RuntimeError("STOP_SOCKET_ENV")
if str(REPO) not in os.environ.get("PYTHONPATH","").split(":"): raise RuntimeError("STOP_CHILD_REPO_ROOT_MISSING")
docker=subprocess.check_output(["docker","version","--format","{{.Server.Version}} {{.Server.Os}}/{{.Server.Arch}}"],text=True,timeout=20).strip()
if docker!="29.4.0 linux/arm64": raise RuntimeError("STOP_NESTED_DOCKER:"+docker)
for root in (REPO,REPO/"research/live_control",V2,REPO/"research/observation_tiles",REPO/"research/observation_gating",REPO/"research/real_apps_v1",REPO/"runtime"): sys.path.insert(0,str(root))
from model_call_backend_v1 import resolve
from docker_model_call_backend_v1 import call as selected_call
def forbidden(*_a,**_k): raise AssertionError("legacy backend invoked")
resolved=resolve(forbidden)
if (resolved.__module__,resolved.__name__)!=("docker_model_call_backend_v1","call"): raise RuntimeError("STOP_SELECTED_BACKEND")
calls=0
def mirror_call(root,prompt,image,contract,workspace):
    global calls
    calls+=1
    if calls!=1: raise RuntimeError("STOP_MODEL_CALL_LIMIT_NO_RETRY")
    source=Path(image).resolve(); mirror_image=MIRROR/"image.png"
    if not source.is_file(): raise FileNotFoundError("STOP_SCREENSHOT_MISSING")
    digest=hashlib.sha256(source.read_bytes()).hexdigest(); shutil.copyfile(source,mirror_image)
    if hashlib.sha256(mirror_image.read_bytes()).hexdigest()!=digest: raise RuntimeError("STOP_SCREENSHOT_HASH_MISMATCH")
    (RUN/"model-image-bind.json").write_text(json.dumps({"image_sha256":digest,"source":str(source),"mirror":str(mirror_image),"authority_granted":False},indent=2)+"\n")
    return resolved(root,prompt,mirror_image,contract,MIRROR/"workspace")
namespace=runpy.run_path(str(V2/"run_task1_smoke.py"),run_name="issue_2849_task1_v29")
g=namespace["main"].__globals__
if g.get("docker_model_call") is not selected_call: raise RuntimeError("STOP_BASE_CALLBACK")
g["docker_model_call"]=mirror_call
if g.get("docker_model_call") is not mirror_call: raise RuntimeError("STOP_CALLBACK_INJECTION")
rc=g["main"]()
(RUN/"outer-runtime-receipt.json").write_text(json.dumps({"status":"OUTER_RUN_RETURNED","seed":284929,"main_return":rc,"calls":calls,"docker_version":docker,"selected_backend":[resolved.__module__,resolved.__name__],"authority_granted":False},indent=2)+"\n")
raise SystemExit(rc)
