"""Bounded one-shot formal supervisor; terminal receipt is an actual wait result."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parent
if __name__=="__main__":
    out=ROOT/"formal01"
    out.mkdir(exist_ok=False)
    start={"utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"formal_invocations":1}
    (out/"START.json").write_text(json.dumps(start,sort_keys=True))
    freeze=json.loads((ROOT/"FREEZE.json").read_text())
    errors=[p for p,h in freeze["sha256"].items() if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h]
    if errors:
        (out/"STOP.json").write_text(json.dumps({"status":"STOP_SOURCE","paths":errors}))
        raise SystemExit(2)
    command=[sys.executable,"-S","-B",str(ROOT/"run.py"),str(out)]
    t=time.monotonic_ns()
    with (out/"stdout.txt").open("xb") as stdout,(out/"stderr.txt").open("xb") as stderr:
        proc=subprocess.Popen(command,cwd=ROOT,stdout=stdout,stderr=stderr)
        timeout=False
        try: code=proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            timeout=True
            proc.kill()
            code=proc.wait()
    receipt={"argv":command,"pid":proc.pid,"returncode":code,"timeout":timeout,
             "elapsed_ns":time.monotonic_ns()-t,"utc_end":datetime.datetime.now(datetime.timezone.utc).isoformat(),
             "status":"COMPLETE" if code==0 and not timeout else "STOP_EXECUTION"}
    (out/"EXECUTION.json").write_text(json.dumps(receipt,sort_keys=True,indent=2)+"\n")
    print(json.dumps(receipt,sort_keys=True))
    raise SystemExit(0 if receipt["status"]=="COMPLETE" else 2)
