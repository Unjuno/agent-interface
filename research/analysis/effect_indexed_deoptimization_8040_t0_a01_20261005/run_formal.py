"""One-shot sequential runner; candidate once, auditor once only after exit 0."""
from __future__ import annotations
import hashlib, json, os, platform, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parent
ALLOCATION = "UNJUNO-8040-EFFECT-INDEXED-DEOPT-T0-A01-20261005"
def digest(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""): h.update(block)
    return h.hexdigest()
def now() -> str: return datetime.now(timezone.utc).isoformat()
def snapshot() -> dict:
    st=os.statvfs(ROOT)
    return {"host":platform.platform(),"machine":platform.machine(),"python":sys.version,"logical_cpus":os.cpu_count(),"load_average":list(os.getloadavg()),"available_disk_bytes":st.f_bavail*st.f_frsize,"container":"none; host substitution","network_enforcement":"none"}
def main() -> int:
    frozen=json.loads((ROOT/"FROZEN.json").read_text())
    mismatches=[n for n,h in frozen["files"].items() if not (ROOT/n).is_file() or digest(ROOT/n)!=h]
    if mismatches: raise SystemExit(f"frozen source mismatch: {mismatches}")
    marker=ROOT/"formal_started.json"
    start={"allocation":ALLOCATION,"driver_invocations":1,"candidate_invocations_before":0,"auditor_invocations_before":0,"started_at_utc":now(),"retry_policy":"zero retries; exclusive-create marker","frozen_sha256":digest(ROOT/"FROZEN.json"),"execution":"native host, low priority, one sequential process"}
    fd=os.open(marker,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    with os.fdopen(fd,"w") as f: json.dump(start,f,indent=2,sort_keys=True); f.write("\n")
    before=snapshot(); begin=time.monotonic()
    env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1"}
    ccmd=[sys.executable,"-B","candidate.py","--input","public_trace.json","--output","candidate_output.json"]
    c=subprocess.run(ccmd,cwd=ROOT,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,check=False,env=env)
    (ROOT/"candidate.stdout.txt").write_text(c.stdout); (ROOT/"candidate.stderr.txt").write_text(c.stderr)
    acmd=None; a=None
    if c.returncode==0:
        acmd=[sys.executable,"-B","audit.py","--input","public_trace.json","--truth","truth_sidecar.json","--candidate","candidate_output.json","--output","audit.json"]
        a=subprocess.run(acmd,cwd=ROOT,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,check=False,env=env)
        (ROOT/"auditor.stdout.txt").write_text(a.stdout); (ROOT/"auditor.stderr.txt").write_text(a.stderr)
    else:
        (ROOT/"auditor.stdout.txt").write_text("NOT_INVOKED\n"); (ROOT/"auditor.stderr.txt").write_text("NOT_INVOKED\n")
    disposition="STOP_CANDIDATE_NONZERO"; audit_disposition="NOT_RUN"
    if a is not None and a.returncode==0:
        audit_disposition=json.loads((ROOT/"audit.json").read_text())["disposition"]
        disposition=audit_disposition
    files=["candidate_output.json","audit.json","candidate.stdout.txt","candidate.stderr.txt","auditor.stdout.txt","auditor.stderr.txt"]
    terminal={"allocation":ALLOCATION,"disposition":disposition,"audit_disposition":audit_disposition,"started_at_utc":start["started_at_utc"],"finished_at_utc":now(),"elapsed_seconds":time.monotonic()-begin,"driver_invocations":1,"candidate_invocations":1,"candidate_exit":c.returncode,"candidate_command":ccmd,"auditor_invocations":1 if a is not None else 0,"auditor_exit":a.returncode if a is not None else None,"auditor_command":acmd,"retries":0,"environment_before":before,"environment_after":snapshot(),"frozen_sha256":digest(ROOT/"FROZEN.json"),"output_sha256":{n:digest(ROOT/n) for n in files if (ROOT/n).is_file()},"container":"none; host substitution","network":"no network calls by code; not OS-isolated"}
    (ROOT/"terminal.json").write_text(json.dumps(terminal,indent=2,sort_keys=True)+"\n")
    print(json.dumps(terminal,sort_keys=True))
    return 0 if disposition=="PASS_METHOD_SCOPED" else 1
if __name__=="__main__": raise SystemExit(main())
