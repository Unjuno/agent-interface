from __future__ import annotations
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]; HERE=Path(__file__).resolve().parent
OUT=HERE/"evidence/offline-replay-v1"; V29=ROOT/"research/integration/issue_2849_task1_orbstack_formal_v29/evidence/task1-seed-284929"
IMAGE="sha256:436172d89b145c6a9f9a57e655422c9558b3b0235347dd77607e9d61bcfa6393"
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    if OUT.exists(): raise RuntimeError("STOP_EVIDENCE_PATH_EXISTS")
    frozen=V29/"posthoc-SHA256SUMS"
    if not frozen.is_file(): raise RuntimeError("STOP_V29_SUPPLEMENTAL_MANIFEST_MISSING")
    for line in frozen.read_text().splitlines():
        digest,rel=line.split("  ",1); path=V29/rel
        if not path.is_file() or sha(path)!=digest: raise RuntimeError("STOP_V29_EVIDENCE_HASH:"+rel)
    original=json.loads((V29/"posthoc-independent-audit.json").read_text())
    if original.get("accepted_formal_outcome")!="FAIL_TASK1_SCOPED": raise RuntimeError("STOP_V29_OUTCOME_CHANGED")
    image=subprocess.check_output(["docker","--context","orbstack","image","inspect",IMAGE,"--format","{{.Id}} {{.Architecture}}"],text=True).strip()
    if image!=IMAGE+" arm64": raise RuntimeError("STOP_OUTER_IMAGE_IDENTITY")
    sources=[HERE/n for n in ("README.md","reconcile_v1.py","harness_v1.py","probe_v1.py","audit_v1.py")]
    sources.append(ROOT/"research/live_control/run_integrated_efficiency_live_v1.py")
    source_hashes={str(p.relative_to(ROOT)):sha(p) for p in sources}
    OUT.mkdir(parents=True)
    prereg={"issue":3798,"parent_issue":2849,"allocation":"offline-replay-v1","predecessor_seed":284929,
      "main_commit":subprocess.check_output(["git","rev-parse","origin/main"],cwd=ROOT,text=True).strip(),
      "outer_image":image,"network":"none","repo_mount":"read-only","task_started":False,"model_calls":0,"gui_actions":0,"ipc_calls":0,
      "source_hashes":source_hashes,"v29_supplemental_manifest_sha256":sha(frozen),
      "v29_formal_outcome":"FAIL_TASK1_SCOPED","no_predecessor_mutation":True}
    (OUT/"preregistration.json").write_text(json.dumps(prereg,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"status":"FROZEN_OFFLINE_REPLAY","source_count":len(source_hashes),"image":image,"main":prereg["main_commit"],"v29_manifest_sha256":prereg["v29_supplemental_manifest_sha256"]},sort_keys=True))
if __name__=="__main__": main()
