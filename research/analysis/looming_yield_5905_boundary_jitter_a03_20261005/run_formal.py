#!/usr/bin/env python3
import hashlib, json, subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).parent.resolve(); A09=ROOT.parent/"looming_yield_5905_image_only_t0_9_a09_20261005"
BASE="f44c5f5724ed2ba1d44cab9a8b3f88f5179c014c"
IMAGE="python@sha256:c3e521df8b2b498a7a682e7e18676771cb80c6b75b8699af886b2d554ce40151"

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def common(): return ["docker","run","--pull=never","--rm","--network=none","--read-only","--tmpfs","/tmp:rw,noexec,nosuid,size=32m","--cap-drop=ALL","--security-opt=no-new-privileges","--cpus=1","--memory=1g"]
def ro(src,dst): return ["--mount",f"type=bind,src={src},dst={dst},readonly"]
def rw(src,dst): return ["--mount",f"type=bind,src={src},dst={dst}"]
def invoke(cmd,out,err):
    try:
        p=subprocess.run(cmd,capture_output=True,text=True,timeout=900); out.write_text(p.stdout); err.write_text(p.stderr); return p.returncode
    except subprocess.TimeoutExpired as e:
        out.write_text(e.stdout or ""); err.write_text(e.stderr or ""); return 124

def main():
    f=json.loads((ROOT/"FROZEN.json").read_text())
    latest=subprocess.check_output(["git","rev-parse","origin/main"],cwd=ROOT,text=True).strip()
    base=subprocess.check_output(["git","merge-base","HEAD","origin/main"],cwd=ROOT,text=True).strip()
    if f["base_commit"]!=BASE or latest!=BASE or base!=BASE: raise SystemExit(f"STOP_MAIN_CHANGED frozen={f['base_commit']} latest={latest} merge_base={base}")
    for n,h in f["source_sha256"].items():
        if sha(ROOT/n)!=h: raise SystemExit("STOP_FROZEN_SOURCE_CHANGED:"+n)
    for n,h in (("candidate.py","caf4a7078edde9164a17ab70d9f59ad868536dc841a33c8840f5784399690465"),("audit.py","7ed3a6ebe66994261f56750df75d0ed162c7b0b6d8dfd4596fdc67aa4d771e3d")):
        if sha(A09/n)!=h: raise SystemExit("STOP_REFERENCE_CHANGED:"+n)
    image=subprocess.check_output(["docker","image","inspect",IMAGE,"--format","{{.Id}} {{.Os}}/{{.Architecture}}"],text=True).strip()
    if not image.startswith(IMAGE.split("@",1)[1]+" linux/arm64"): raise SystemExit("STOP_IMAGE_IDENTITY:"+image)
    results=ROOT/"results"
    if results.exists() and any(p.is_file() for p in results.rglob("*")): raise SystemExit("STOP_RESULTS_NOT_EMPTY")
    co=results/"candidate-out"; ao=results/"audit-out"; co.mkdir(parents=True,exist_ok=True); ao.mkdir(parents=True,exist_ok=True)
    cp=co/"candidate.json"
    cc=(common()+ro(A09/"candidate.py","/src/candidate.py")+ro(ROOT/"bundle/observations","/input")+rw(co,"/output")+["-w","/work",IMAGE,"python","-B","/src/candidate.py","/input"])
    r={"allocation":f["allocation"],"started_at_utc":datetime.now(timezone.utc).isoformat(),"candidate_invocations":1,"auditor_invocations":0,"retries":0,"candidate_command":cc,"auditor_command":None,"candidate_exit":None,"auditor_exit":None,"state":"CANDIDATE_RUNNING"}
    (ROOT/"FORMAL_STARTED.json").write_text(json.dumps(r,sort_keys=True,indent=2)+"\n")
    rc=invoke(cc,results/"candidate.stdout.txt",results/"candidate.stderr.txt"); r["candidate_exit"]=rc
    if rc or not cp.exists():
        r["state"]="STOP_CANDIDATE_FAILED"; (ROOT/"RUN_RECORD.json").write_text(json.dumps(r,sort_keys=True,indent=2)+"\n"); raise SystemExit(r["state"])
    r["state"]="CANDIDATE_COMPLETE"; (ROOT/"FORMAL_STARTED.json").write_text(json.dumps(r,sort_keys=True,indent=2)+"\n")
    ap=ao/"audit.json"
    ac=(common()+ro(A09/"audit.py","/src/audit.py")+ro(ROOT/"bundle","/bundle")+ro(cp,"/candidate/candidate.json")+rw(ao,"/output")+["-w","/work",IMAGE,"python","-B","/src/audit.py","/bundle","/candidate/candidate.json","/output/audit.json"])
    r.update({"auditor_command":ac,"auditor_invocations":1,"state":"AUDITOR_RUNNING"}); (ROOT/"FORMAL_STARTED.json").write_text(json.dumps(r,sort_keys=True,indent=2)+"\n")
    rc=invoke(ac,results/"auditor.stdout.txt",results/"auditor.stderr.txt")
    r.update({"auditor_exit":rc,"candidate_sha256":sha(cp),"audit_sha256":sha(ap) if ap.exists() else None,"state":"COMPLETE" if rc==0 else "FAIL_OR_STOP_AUDITOR"})
    for n in ("FORMAL_STARTED.json","RUN_RECORD.json"): (ROOT/n).write_text(json.dumps(r,sort_keys=True,indent=2)+"\n")
    if rc: raise SystemExit(r["state"])

if __name__=="__main__": main()
