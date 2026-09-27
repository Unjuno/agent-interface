from __future__ import annotations
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]; HERE=Path(__file__).resolve().parent
OUT=HERE/"evidence/preflight-v1"; V29=ROOT/"research/integration/issue_2849_task1_orbstack_formal_v29/evidence/task1-seed-284929"
IMAGE="sha256:436172d89b145c6a9f9a57e655422c9558b3b0235347dd77607e9d61bcfa6393"
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    if OUT.exists(): raise RuntimeError("STOP_PREFLIGHT_PATH_EXISTS")
    manifest=V29/"posthoc-SHA256SUMS"
    for line in manifest.read_text().splitlines():
        digest,rel=line.split("  ",1); path=V29/rel
        if not path.is_file() or sha(path)!=digest: raise RuntimeError("STOP_V29_HASH:"+rel)
    image=subprocess.check_output(["docker","--context","orbstack","image","inspect",IMAGE,"--format","{{.Id}} {{.Architecture}}"],text=True).strip()
    if image!=IMAGE+" arm64": raise RuntimeError("STOP_IMAGE_IDENTITY")
    files=[HERE/n for n in ("README.md","scope_reconcile_v30.py","preflight_v30.py","preflight_probe_v30.py","preflight_audit_v30.py","run_task1_v30.py")]
    hashes={str(p.relative_to(ROOT)):sha(p) for p in files}
    OUT.mkdir(parents=True)
    prereg={"issue":2849,"successor_issue":3798,"allocation":"v30-preflight-v1","seed":284930,
      "main_commit":subprocess.check_output(["git","rev-parse","origin/main"],cwd=ROOT,text=True).strip(),"outer_image":image,
      "network":"none","repository_mount":"read-only","model_calls":0,"task_started":False,"gui_actions":0,"ipc_calls":0,
      "source_hashes":hashes,"v29_manifest_sha256":sha(manifest),"no_predecessor_mutation":True}
    (OUT/"preregistration.json").write_text(json.dumps(prereg,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"status":"FROZEN_PREFLIGHT","source_count":len(hashes),"image":image,"v29_manifest":prereg["v29_manifest_sha256"]},sort_keys=True))
if __name__=="__main__": main()
