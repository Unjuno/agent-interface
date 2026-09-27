#!/usr/bin/env python3
import argparse, hashlib, json, pathlib, subprocess, sys, time

DEADLINE_MS=120
FRESHNESS_MS=400
POLICIES=("PRE_DISPATCH_ONLY","POSTHOC_EFFECT_CHECK","APP_COMMIT_DEADLINE")
SCHEDULES={
    "EARLY_SHORT": (20,10,20),
    "NEAR_SHORT": (60,10,20),
    "EARLY_LONG": (20,10,110),
    "NEAR_LONG": (60,10,80),
}

def sha256(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()

def sleep_until(ns):
    while True:
        now=time.monotonic_ns(); rem=ns-now
        if rem<=0: return
        time.sleep(min(rem/1e9,0.002))

def run_case(root,policy,schedule,rep,mode):
    ready_ms,queue_ms,processing_ms=SCHEDULES[schedule]
    cid=f"{mode}-{rep}-{policy}-{schedule}"
    cdir=pathlib.Path(root)/cid; cdir.mkdir(parents=True,exist_ok=False)
    app=subprocess.Popen([sys.executable,"-B","app_worker.py"],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
    ready=json.loads(app.stdout.readline())
    if ready.get("type")!="READY": raise RuntimeError("app not ready")
    start=time.monotonic_ns(); deadline=start+DEADLINE_MS*1_000_000; freshness=start+FRESHNESS_MS*1_000_000
    sleep_until(start+ready_ms*1_000_000); proposal=time.monotonic_ns()
    sleep_until(proposal+queue_ms*1_000_000); predispatch=time.monotonic_ns()
    dispatch_valid=(proposal<=deadline and predispatch<=deadline and predispatch<=freshness)
    if not dispatch_valid: raise RuntimeError(f"construction/formal dispatch unexpectedly late: {cid}")
    msg={"type":"DISPATCH","case_id":cid,"policy":policy,"processing_ms":processing_ms,"start_ns":start,"deadline_ns":deadline}
    app.stdin.write(json.dumps(msg)+"\n"); app.stdin.flush(); app.stdin.close()
    line=app.stdout.readline(); receipt=json.loads(line) if line else None
    stderr=app.stderr.read(); rc=app.wait(timeout=3)
    posthoc=None
    if policy=="POSTHOC_EFFECT_CHECK" and receipt and receipt.get("effect_committed"):
        posthoc="ON_TIME" if receipt["within_deadline"] else "LATE"
    row={
      "case_id":cid,"mode":mode,"rep":rep,"policy":policy,"schedule":schedule,
      "ready_ms":ready_ms,"queue_ms":queue_ms,"processing_ms":processing_ms,
      "deadline_ms":DEADLINE_MS,"freshness_ms":FRESHNESS_MS,
      "start_ns":start,"proposal_ready_ns":proposal,"predispatch_ns":predispatch,
      "proposal_ready_elapsed_ms":(proposal-start)/1e6,"predispatch_elapsed_ms":(predispatch-start)/1e6,
      "dispatch_valid":dispatch_valid,"authority":False,"app_ready":ready,"receipt":receipt,"posthoc":posthoc,
      "app_exit":rc,"app_stderr":stderr,
      "source_hashes":{"run.py":sha256("run.py"),"app_worker.py":sha256("app_worker.py")}
    }
    (cdir/"row.json").write_text(json.dumps(row,indent=2,sort_keys=True)+"\n")
    return row

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--out",required=True); ap.add_argument("--mode",choices=["construction","formal"],required=True); ap.add_argument("--reps",type=int,default=1)
    a=ap.parse_args(); root=pathlib.Path(a.out); root.mkdir(parents=True,exist_ok=False)
    rows=[]
    for rep in range(a.reps):
      for sched in SCHEDULES:
       for policy in POLICIES:
        rows.append(run_case(root,policy,sched,rep,a.mode))
    (root/"ROWS.json").write_text(json.dumps(rows,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"rows":len(rows),"mode":a.mode,"out":str(root)},sort_keys=True))

if __name__=='__main__': main()
