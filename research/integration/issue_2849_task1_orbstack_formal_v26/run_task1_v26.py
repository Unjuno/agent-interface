from __future__ import annotations
import hashlib,json,os,runpy,shutil,subprocess,sys
from pathlib import Path
REPO=Path(os.environ["ISSUE_2849_REPO"]).resolve(); V2=REPO/"research/integration/issue_2849_task1_orbstack_smoke_v2"
RUN=Path(os.environ["ISSUE_2849_RUN_ROOT"]).resolve(); OUT=Path(os.environ["ISSUE_2849_RUN_DIR"]).resolve(); MIRROR=Path(os.environ["AGENT_INTERFACE_DOCKER_SCHEMA"]).resolve().parent
SEED=int(os.environ["ISSUE_2849_SEED"])
if SEED!=284926: raise RuntimeError("STOP_TASK_SEED_MISMATCH")
if not (OUT/"pre-call-source-manifest.json").is_file() or not (MIRROR/"workspace").is_dir(): raise RuntimeError("STOP_SOURCE_OR_MIRROR_MISSING")
if os.environ.get("DOCKER_HOST")!="unix:///var/run/docker.sock": raise RuntimeError("STOP_SOCKET_ENV")
if not os.environ.get("PYTHONPATH") or str(REPO/"research/live_control") not in os.environ["PYTHONPATH"].split(":"): raise RuntimeError("STOP_CHILD_PYTHONPATH")
docker_version=subprocess.check_output(["docker","version","--format","{{.Server.Version}} {{.Server.Os}}/{{.Server.Arch}}"],text=True,timeout=20).strip()
if docker_version!="29.4.0 linux/arm64": raise RuntimeError("STOP_NESTED_DOCKER:"+docker_version)
for root in (V2,REPO,REPO/"research/live_control",REPO/"research/observation_tiles",REPO/"research/observation_gating",REPO/"research/real_apps_v1",REPO/"runtime"): sys.path.insert(0,str(root))
from model_call_backend_v1 import resolve
from docker_model_call_backend_v1 import call as selected_call
def forbidden(*_a,**_k): raise AssertionError("legacy backend invoked")
resolved=resolve(forbidden)
if (resolved.__module__,resolved.__name__)!=("docker_model_call_backend_v1","call"): raise RuntimeError("STOP_SELECTED_BACKEND")
CALLS=0
def mirror_call(root,prompt,image,contract,workspace):
    global CALLS
    CALLS+=1
    if CALLS!=1: raise RuntimeError("STOP_MODEL_CALL_LIMIT_NO_RETRY")
    source=Path(image).resolve()
    if not source.is_file(): raise FileNotFoundError("STOP_SCREENSHOT_MISSING")
    digest=hashlib.sha256(source.read_bytes()).hexdigest(); destination=MIRROR/"image.png"; shutil.copyfile(source,destination)
    if hashlib.sha256(destination.read_bytes()).hexdigest()!=digest: raise RuntimeError("STOP_SCREENSHOT_HASH_MISMATCH")
    (RUN/"model-image-bind.json").write_text(json.dumps({"image_sha256":digest,"source":str(source),"mirror":str(destination),"authority_granted":False},indent=2)+"\n")
    return resolved(root,prompt,destination,contract,MIRROR/"workspace")
namespace=runpy.run_path(str(V2/"run_task1_smoke.py"),run_name="issue_2849_task1_v26")
main_globals=namespace["main"].__globals__
if main_globals.get("docker_model_call") is not selected_call: raise RuntimeError("STOP_BASE_CALLBACK")
main_globals["docker_model_call"]=mirror_call
if main_globals.get("docker_model_call") is not mirror_call: raise RuntimeError("STOP_CALLBACK_INJECTION")
result=main_globals["main"]()
(RUN/"outer-runtime-receipt.json").write_text(json.dumps({"status":"OUTER_RUN_RETURNED","seed":SEED,"main_return":result,"calls":CALLS,"docker_version":docker_version,"selected_backend":[resolved.__module__,resolved.__name__],"authority_granted":False},indent=2)+"\n")
