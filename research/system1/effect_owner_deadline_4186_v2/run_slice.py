#!/usr/bin/env python3
import argparse, hashlib, json, pathlib, subprocess, sys, time
DEADLINE_MS=120; FRESHNESS_MS=400
POLICIES=("APP_CHECK_ONLY","SINK_POSTHOC_CHECK","SINK_PRECOMMIT_DEADLINE")
SCHEDULES={"EARLY_SHORT":(20,10,20),"NEAR_SHORT":(60,10,20),"EARLY_LONG":(20,10,110),"NEAR_LONG":(60,10,80)}
def sha256(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def sleep_until(ns):
    while True:
        rem=ns-time.monotonic_ns()
        if rem<=0:return
        time.sleep(min(rem/1e9,0.002))
def run_case(root,policy,schedule,rep,mode):
    ready_ms,queue_ms,processing_ms=SCHEDULES[schedule]
    cid=f"{mode}-{rep}-{policy}-{schedule}"; cdir=pathlib.Path(root)/cid; cdir.mkdir(parents=True,exist_ok=False)
    effect_path=cdir/"effect.json"
    app=subprocess.Popen([sys.executable,"-B","app_worker.py",str(effect_path)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
    ready=json.loads(app.stdout.readline())
    if ready.get("type")!="APP_READY": raise RuntimeError("app not ready")
    start=time.monotonic_ns(); deadline=start+DEADLINE_MS*1_000_000; freshness=start+FRESHNESS_MS*1_000_000
    sleep_until(start+ready_ms*1_000_000); proposal=time.monotonic_ns()
    sleep_until(proposal+queue_ms*1_000_000); predispatch=time.monotonic_ns()
    if not (proposal<=deadline and predispatch<=deadline and predispatch<=freshness): raise RuntimeError("unexpected late dispatch")
    msg={"case_id":cid,"policy":policy,"processing_ms":processing_ms,"deadline_ns":deadline}
    app.stdin.write(json.dumps(msg)+"\n"); app.stdin.flush(); app.stdin.close()
    line=app.stdout.readline(); receipt=json.loads(line) if line else None
    app_stderr=app.stderr.read(); app_rc=app.wait(timeout=4)
    effect=json.loads(effect_path.read_text()) if effect_path.exists() else None
    row={"case_id":cid,"mode":mode,"rep":rep,"policy":policy,"schedule":schedule,
         "ready_ms":ready_ms,"queue_ms":queue_ms,"processing_ms":processing_ms,"deadline_ms":DEADLINE_MS,"freshness_ms":FRESHNESS_MS,
         "start_ns":start,"proposal_ready_ns":proposal,"predispatch_ns":predispatch,
         "proposal_ready_elapsed_ms":(proposal-start)/1e6,"predispatch_elapsed_ms":(predispatch-start)/1e6,
         "authority":False,"app_ready":ready,"app_receipt":receipt,"app_exit":app_rc,"app_stderr":app_stderr,"effect_file":effect,
         "source_hashes":{x:sha256(x) for x in ("run_slice.py","app_worker.py","sink_worker.py")}}
    (cdir/"row.json").write_text(json.dumps(row,indent=2,sort_keys=True)+"\n"); return row
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--out",required=True); ap.add_argument("--mode",choices=["construction","formal"],required=True); ap.add_argument("--rep",type=int,choices=[0,1,2],required=True); ap.add_argument("--schedule",choices=list(SCHEDULES),required=True); a=ap.parse_args()
    root=pathlib.Path(a.out); root.mkdir(parents=True,exist_ok=False); rows=[run_case(root,p,a.schedule,a.rep,a.mode) for p in POLICIES]
    (root/"ROWS.json").write_text(json.dumps(rows,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"rows":3,"mode":a.mode,"rep":a.rep,"schedule":a.schedule,"out":str(root)},sort_keys=True))
if __name__=='__main__': main()
