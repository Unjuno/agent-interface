#!/usr/bin/env python3
"""One-shot isolated candidate then independent A09 raw-only auditor."""
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
A09 = ROOT.parents[0] / "looming_yield_5905_image_only_t0_9_a09_20261005"
BASE = "cd3a410a930e5f1e29a22cee36d9a149fbc106c7"
IMAGE = "python@sha256:c3e521df8b2b498a7a682e7e18676771cb80c6b75b8699af886b2d554ce40151"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def common():
    return ["docker", "run", "--pull=never", "--rm", "--network=none", "--read-only",
            "--tmpfs", "/tmp:rw,noexec,nosuid,size=32m", "--cap-drop=ALL",
            "--security-opt=no-new-privileges", "--cpus=1", "--memory=1g"]


def ro(src,dst): return ["--mount", f"type=bind,src={src},dst={dst},readonly"]
def rw(src,dst): return ["--mount", f"type=bind,src={src},dst={dst}"]


def invoke(cmd, out, err):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
        out.write_text(p.stdout); err.write_text(p.stderr)
        return p.returncode
    except subprocess.TimeoutExpired as e:
        out.write_text(e.stdout or ""); err.write_text(e.stderr or "")
        return 124


def main():
    frozen = json.loads((ROOT/"FROZEN.json").read_text())
    latest = subprocess.check_output(["git","rev-parse","origin/main"],cwd=ROOT,text=True).strip()
    base = subprocess.check_output(["git","merge-base","HEAD","origin/main"],cwd=ROOT,text=True).strip()
    if frozen["base_commit"] != BASE or latest != BASE or base != BASE:
        raise SystemExit(f"STOP_MAIN_CHANGED frozen={frozen['base_commit']} latest={latest} merge_base={base}")
    for path, expected in frozen["source_sha256"].items():
        if sha(ROOT/path) != expected: raise SystemExit("STOP_FROZEN_SOURCE_CHANGED:"+path)
    for key, expected in (("candidate_reference","caf4a7078edde9164a17ab70d9f59ad868536dc841a33c8840f5784399690465"),
                          ("auditor_reference","7ed3a6ebe66994261f56750df75d0ed162c7b0b6d8dfd4596fdc67aa4d771e3d")):
        item=frozen[key]
        rel=item["path"].split("/")[-1]
        if sha(A09/rel) != expected or item["sha256"] != expected:
            raise SystemExit("STOP_REFERENCE_SOURCE_CHANGED:"+key)
    image = subprocess.check_output(["docker","image","inspect",IMAGE,"--format","{{.Id}} {{.Os}}/{{.Architecture}}"],text=True).strip()
    if not image.startswith(IMAGE.split("@",1)[1]+" linux/arm64"):
        raise SystemExit("STOP_IMAGE_IDENTITY:"+image)
    results=ROOT/"results"
    if results.exists() and any(x.is_file() for x in results.rglob("*")):
        raise SystemExit("STOP_RESULT_DIRECTORY_NOT_EMPTY")
    cand_out=results/"candidate-out"; audit_out=results/"audit-out"
    cand_out.mkdir(parents=True,exist_ok=True); audit_out.mkdir(parents=True,exist_ok=True)
    cand_path=cand_out/"candidate.json"
    cand_cmd=(common()+ro(A09/"candidate.py","/src/candidate.py")+
              ro(ROOT/"bundle/observations","/input")+rw(cand_out,"/output")+
              ["-w","/work",IMAGE,"python","-B","/src/candidate.py","/input"])
    receipt={"allocation":frozen["allocation"],"started_at_utc":datetime.now(timezone.utc).isoformat(),
             "candidate_container_attempts":1,"candidate_invocations":1,"auditor_invocations":0,"retries":0,
             "candidate_command":cand_cmd,"auditor_command":None,"candidate_exit":None,"auditor_exit":None,
             "state":"CANDIDATE_RUNNING"}
    (ROOT/"FORMAL_STARTED.json").write_text(json.dumps(receipt,sort_keys=True,indent=2)+"\n")
    rc=invoke(cand_cmd,results/"candidate.stdout.txt",results/"candidate.stderr.txt")
    receipt["candidate_exit"]=rc
    if rc or not cand_path.is_file():
        receipt["state"]="STOP_CANDIDATE_FAILED"
        (ROOT/"RUN_RECORD.json").write_text(json.dumps(receipt,sort_keys=True,indent=2)+"\n")
        raise SystemExit(receipt["state"])
    receipt["state"]="CANDIDATE_COMPLETE"
    (ROOT/"FORMAL_STARTED.json").write_text(json.dumps(receipt,sort_keys=True,indent=2)+"\n")
    audit_file=audit_out/"audit.json"
    audit_cmd=(common()+ro(A09/"audit.py","/src/audit.py")+ro(ROOT/"bundle","/bundle")+
               ro(cand_path,"/candidate/candidate.json")+rw(audit_out,"/output")+
               ["-w","/work",IMAGE,"python","-B","/src/audit.py","/bundle",
                "/candidate/candidate.json","/output/audit.json"])
    receipt.update({"auditor_command":audit_cmd,"auditor_invocations":1,"state":"AUDITOR_RUNNING"})
    (ROOT/"FORMAL_STARTED.json").write_text(json.dumps(receipt,sort_keys=True,indent=2)+"\n")
    rc=invoke(audit_cmd,results/"auditor.stdout.txt",results/"auditor.stderr.txt")
    receipt.update({"auditor_exit":rc,"candidate_output_sha256":sha(cand_path),
                    "audit_sha256":sha(audit_file) if audit_file.exists() else None,
                    "state":"COMPLETE" if rc==0 else "FAIL_OR_STOP_AUDITOR"})
    for name in ("FORMAL_STARTED.json","RUN_RECORD.json"):
        (ROOT/name).write_text(json.dumps(receipt,sort_keys=True,indent=2)+"\n")
    if rc: raise SystemExit(receipt["state"])


if __name__ == "__main__": main()
