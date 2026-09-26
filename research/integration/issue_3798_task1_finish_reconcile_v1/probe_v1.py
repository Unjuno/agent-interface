from __future__ import annotations
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]; HERE=Path(__file__).resolve().parent
OUT=HERE/"evidence/offline-replay-v1"; V29=ROOT/"research/integration/issue_2849_task1_orbstack_formal_v29/evidence/task1-seed-284929"
IMAGE="sha256:436172d89b145c6a9f9a57e655422c9558b3b0235347dd77607e9d61bcfa6393"
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    frozen=json.loads((OUT/"preregistration.json").read_text())
    for rel,digest in frozen["source_hashes"].items():
        p=ROOT/rel
        if not p.is_file() or sha(p)!=digest: raise RuntimeError("STOP_FROZEN_SOURCE_CHANGED:"+rel)
    image=subprocess.check_output(["docker","--context","orbstack","image","inspect",IMAGE,"--format","{{.Id}} {{.Architecture}}"],text=True).strip()
    if image!=IMAGE+" arm64" or image!=frozen["outer_image"]: raise RuntimeError("STOP_IMAGE_IDENTITY")
    if OUT.exists() is False: raise RuntimeError("STOP_OUTPUT_MISSING")
    cmd=["docker","--context","orbstack","run","--rm","--network","none","--mount",f"type=bind,src={ROOT},dst=/repo,readonly","--mount",f"type=bind,src={OUT},dst=/out","--entrypoint","python3",IMAGE,"/repo/research/integration/issue_3798_task1_finish_reconcile_v1/harness_v1.py"]
    proc=subprocess.run(cmd,capture_output=True,text=True,timeout=90,check=False)
    record={"issue":3798,"seed":284929,"outer_image":image,"network":"none","read_only_repo":True,"returncode":proc.returncode,"stdout":proc.stdout[-3000:],"stderr":proc.stderr[-3000:],"authority_granted":False}
    (OUT/"container-result.json").write_text(json.dumps(record,indent=2,sort_keys=True)+"\n")
    return proc.returncode
if __name__=="__main__": raise SystemExit(main())
