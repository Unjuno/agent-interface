#!/usr/bin/env python3
import argparse, hashlib, json, os, pathlib, subprocess, sys, time

DEADLINE_MS=120
FRESHNESS_MS=400
SCHEDULES={
    "EARLY_SHORT": (20,20),
    "NEAR_SHORT": (90,10),
    "NEAR_LONG": (90,60),
    "EARLY_LONG": (20,140),
}
POLICIES=("PROPOSAL_READY_DEADLINE","PRE_DISPATCH_DEADLINE")

def sha256(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()

def sleep_until(ns):
    while True:
        now=time.monotonic_ns()
        rem=ns-now
        if rem<=0: return
        time.sleep(min(rem/1e9,0.002))

def run_case(outdir, policy, sched, rep, mode):
    ready_ms, queue_ms=SCHEDULES[sched]
    cid=f"{mode}-{rep}-{policy}-{sched}"
    cdir=pathlib.Path(outdir)/cid
    cdir.mkdir(parents=True, exist_ok=False)
    app=subprocess.Popen([sys.executable,"-B","app_worker.py"],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
    ready_line=app.stdout.readline()
    ready=json.loads(ready_line)
    if ready.get("type")!="READY": raise RuntimeError("app not ready")
    start=time.monotonic_ns()
    deadline=start+DEADLINE_MS*1_000_000
    freshness=start+FRESHNESS_MS*1_000_000
    ready_target=start+ready_ms*1_000_000
    sleep_until(ready_target)
    proposal_ready=time.monotonic_ns()
    proposal_valid=(proposal_ready<=deadline and proposal_ready<=freshness)
    queue_target=proposal_ready+queue_ms*1_000_000
    sleep_until(queue_target)
    predispatch=time.monotonic_ns()
    if policy=="PROPOSAL_READY_DEADLINE":
        admitted=proposal_valid
        reason="proposal_ready_valid" if admitted else "proposal_ready_late"
    else:
        admitted=proposal_valid and predispatch<=deadline and predispatch<=freshness
        reason="predispatch_valid" if admitted else "predispatch_late"
    app_effect=None
    if admitted:
        msg={"type":"DISPATCH","case_id":cid,"start_ns":start,"deadline_ns":deadline,"payload":"EFFECT_1"}
        app.stdin.write(json.dumps(msg)+"\n"); app.stdin.flush(); app.stdin.close()
        effect_line=app.stdout.readline()
        if effect_line:
            app_effect=json.loads(effect_line)
    else:
        app.stdin.close()
    stderr=app.stderr.read()
    rc=app.wait(timeout=3)
    row={
        "case_id":cid,"mode":mode,"rep":rep,"policy":policy,"schedule":sched,
        "ready_target_ms":ready_ms,"queue_ms":queue_ms,"deadline_ms":DEADLINE_MS,"freshness_ms":FRESHNESS_MS,
        "start_ns":start,"proposal_ready_ns":proposal_ready,"predispatch_ns":predispatch,
        "proposal_ready_elapsed_ms":(proposal_ready-start)/1e6,
        "predispatch_elapsed_ms":(predispatch-start)/1e6,
        "proposal_valid":proposal_valid,"admitted":admitted,"reason":reason,
        "authority":False,"app_ready":ready,"app_effect":app_effect,"app_exit":rc,"app_stderr":stderr,
        "source_hashes":{"run.py":sha256("run.py"),"app_worker.py":sha256("app_worker.py")},
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
    print(json.dumps({"rows":len(rows),"out":str(root),"mode":a.mode},sort_keys=True))

if __name__=='__main__': main()
