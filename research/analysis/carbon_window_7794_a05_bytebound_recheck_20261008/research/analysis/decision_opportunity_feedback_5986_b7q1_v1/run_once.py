import hashlib
import json
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


ROOT=Path(__file__).parent
ALLOCATION="DECISION-OPPORTUNITY-5986-T0-20261002-01"
OUT=ROOT/"outputs"/ALLOCATION
FIXTURE=ROOT/"fixture.json"
CAND=OUT/"candidate.json"
AUDIT=OUT/"audit.json"


def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def call(args, stdout, stderr):
    start=datetime.now(timezone.utc).isoformat(); tick=time.monotonic()
    p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,check=False)
    elapsed=time.monotonic()-tick
    stdout.write_text(p.stdout,encoding="utf-8"); stderr.write_text(p.stderr,encoding="utf-8")
    return {"argv":args,"started_utc":start,"exit_code":p.returncode,"elapsed_seconds":elapsed,
            "stdout_sha256":digest(stdout),"stderr_sha256":digest(stderr)}


def main():
    if OUT.exists(): raise SystemExit("STOP_OUTPUT_COLLISION")
    OUT.mkdir(parents=True)
    names=("fixture.json","candidate.py","audit.py","test_construction.py","run_once.py","PROTOCOL.md","FREEZE.json")
    run={"allocation_id":ALLOCATION,"owner":"01a0b990-3d17-72f1-a908-9a2072104ce5 local Windows Codex task",
         "main_sha":"3adec9cdc2cff5ef68f19acd55c5823fcaad26df","branch":"research/decision-opportunity-feedback-5986-t0-20261002-b7q1",
         "started_utc":datetime.now(timezone.utc).isoformat(),"python":sys.version,"platform":platform.platform(),
         "source_hashes":{n:digest(ROOT/n) for n in names},"commands":[]}
    first=call([sys.executable,"candidate.py",str(FIXTURE),str(CAND)],OUT/"candidate.stdout.txt",OUT/"candidate.stderr.txt")
    run["commands"].append(first)
    if first["exit_code"]==0:
        second=call([sys.executable,"audit.py",str(FIXTURE),str(CAND),str(AUDIT)],OUT/"audit.stdout.txt",OUT/"audit.stderr.txt")
        run["commands"].append(second)
    run["ended_utc"]=datetime.now(timezone.utc).isoformat()
    run["candidate_sha256"]=digest(CAND) if CAND.exists() else None
    run["audit_sha256"]=digest(AUDIT) if AUDIT.exists() else None
    run["disposition"]="METHOD_PASS_SCOPED" if len(run["commands"])==2 and all(x["exit_code"]==0 for x in run["commands"]) else "FAIL_OR_INCOMPLETE_FIRST_OUTCOME"
    (OUT/"RUN.json").write_text(json.dumps(run,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"allocation_id":ALLOCATION,"commands":run["commands"],"disposition":run["disposition"]},sort_keys=True))
    if run["disposition"]!="METHOD_PASS_SCOPED": raise SystemExit(1)


if __name__=="__main__": main()
