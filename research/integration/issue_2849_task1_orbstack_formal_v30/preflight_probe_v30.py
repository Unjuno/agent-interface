from __future__ import annotations
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]; HERE=Path(__file__).resolve().parent; OUT=HERE/"evidence/preflight-v1"
IMAGE="sha256:436172d89b145c6a9f9a57e655422c9558b3b0235347dd77607e9d61bcfa6393"
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    pre=json.loads((OUT/"preregistration.json").read_text())
    for rel,digest in pre["source_hashes"].items():
        if sha(ROOT/rel)!=digest: raise RuntimeError("STOP_SOURCE_CHANGED:"+rel)
    if sha(HERE/"run_task1_v30.py")!=pre["source_hashes"][str((HERE/"run_task1_v30.py").relative_to(ROOT))]: raise RuntimeError("STOP_FORMAL_RUNNER_HASH")
    cmd=["docker","--context","orbstack","run","--rm","--network","none","--mount",f"type=bind,src={ROOT},dst=/repo,readonly","--mount",f"type=bind,src={OUT},dst=/out","--entrypoint","python3",IMAGE,"/repo/research/integration/issue_2849_task1_orbstack_formal_v30/preflight_v30.py"]
    p=subprocess.run(cmd,capture_output=True,text=True,timeout=90,check=False)
    receipt={"image":pre["outer_image"],"network":"none","repository_read_only":True,"returncode":p.returncode,"stdout":p.stdout[-3000:],"stderr":p.stderr[-3000:],"model_calls":0,"task_started":False,"gui_actions":0,"ipc_calls":0}
    (OUT/"container-result.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    return p.returncode
if __name__=="__main__": raise SystemExit(main())
