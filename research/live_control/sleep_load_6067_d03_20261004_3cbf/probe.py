"""D03 actual pure-sleep/imposed-load acquisition; CLI is consumed once."""
import hashlib
import json
import os
from pathlib import Path
import select
import subprocess
import sys
import time
from core import parse_cpu,validate_cell,validate_rows,decision
HERE=Path(__file__).resolve().parent
PLAN=json.loads((HERE/"plan.json").read_text())

def optional(path):
    try:return {"available":True,"raw":Path(path).read_text(),"error":None}
    except OSError as e:return {"available":False,"raw":None,"error":str(e)}

def snapshot():
    begin=time.monotonic_ns()
    raw=Path("/sys/fs/cgroup/cpu.stat").read_text()
    sched=optional("/proc/self/schedstat")
    enabled=optional("/proc/sys/kernel/sched_schedstats")
    cpu=time.process_time_ns()
    return {"begin_ns":begin,"end_ns":time.monotonic_ns(),"cpu_raw":raw,"cpu":parse_cpu(raw),"process_cpu_ns":cpu,"schedstat":sched,"schedstats_enabled":enabled}

def measure(due,pid,snapshotter=snapshot,clock=time.monotonic_ns,sleep=time.sleep,cpucounter=time.process_time_ns,index=0):
    pre=snapshotter()
    start=clock();cpu0=cpucounter();sleepstart=clock();requested=max(0,due-sleepstart)
    if requested:sleep(requested/1e9)
    returned=clock();cpu1=cpucounter();post=snapshotter()
    return {"index":index,"pid":pid,"due_ns":due,"start_ns":start,"sleep_start_ns":sleepstart,"requested_ns":requested,"return_ns":returned,"cpu_start_ns":cpu0,"cpu_end_ns":cpu1,"pre":pre,"post":post}

def burn(case):
    begin=time.monotonic_ns();cpu=time.process_time_ns()
    print(json.dumps({"type":"ready","pid":os.getpid(),"ppid":os.getppid(),"case":case,"allocation":PLAN["allocation"],"time_ns":begin}),flush=True)
    iterations=0;value=1;reason="bounded-expiry"
    while time.monotonic_ns()-begin<4_000_000_000:
        for _ in range(4000): value=(value*1664525+1013904223)&0xffffffff
        iterations+=4000
        if select.select([sys.stdin],[],[],0)[0]:
            reason="parent-stop" if sys.stdin.readline()=="stop\n" else "bad-stop"
            break
    print(json.dumps({"type":"finish","pid":os.getpid(),"time_ns":time.monotonic_ns(),"iterations":iterations,"cpu_ns":time.process_time_ns()-cpu,"reason":reason}),flush=True)
    return 0 if reason=="parent-stop" else 2

def start_child(case):
    child=subprocess.Popen([sys.executable,"-B",str(HERE/"probe.py"),"--burn",case],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    try:
        if not select.select([child.stdout],[],[],2)[0]:raise ValueError("child readiness timeout")
        line=child.stdout.readline();ready=json.loads(line)
        if ready.get("pid")!=child.pid or ready.get("ppid")!=os.getpid() or ready.get("case")!=case or ready.get("allocation")!=PLAN["allocation"] or ready.get("type")!="ready":raise ValueError("child readiness authority")
        return child,ready
    except Exception:
        child.kill();out,err=child.communicate(timeout=2)
        raise ValueError("failed readiness; terminal="+str(child.returncode)+" stdout="+out+" stderr="+err)

def stop_child(child,ready):
    forced=False
    try:out,err=child.communicate("stop\n",timeout=2)
    except subprocess.TimeoutExpired:
        forced=True;child.kill();out,err=child.communicate(timeout=2)
    try:finish=json.loads(out)
    except Exception:finish={"type":"invalid","raw":out}
    return {"pid":child.pid,"ready":ready,"finish":finish,"stderr":err,"exit_code":child.returncode,"forced":forced}

def source_hashes():
    freeze=json.loads((HERE/"FREEZE.json").read_text())
    hashes={k:hashlib.sha256((HERE/k).read_bytes()).hexdigest() for k in freeze["source_sha256"]}
    if hashes!=freeze["source_sha256"]:raise ValueError("frozen source changed")
    return hashes

def collect_rows(start,pid,plan,measurefn=measure):
    rows=[]
    try:
        for i in range(plan['events']):
            rows.append(measurefn(start+plan['initial_ns']+i*plan['period_ns'],pid,index=i))
            validate_rows(rows,pid,start,rows[-1]['post']['end_ns'],plan)
    except Exception as e:return rows,repr(e)
    return rows,None

def cleanup_children(started,stopper=stop_child):
    receipts=[]
    for child,ready in started:
        try:receipt=stopper(child,ready)
        except Exception as e:
            receipt={'pid':child.pid,'ready':ready,'forced':True,'error':repr(e)}
            try:
                child.kill();out,err=child.communicate(timeout=2)
                receipt.update(stdout=out,stderr=err,exit_code=child.returncode)
            except Exception as cleanup_error:receipt['cleanup_error']=repr(cleanup_error)
        receipts.append(receipt)
    return receipts

def run(out):
    out.mkdir(exist_ok=False)
    hashes=source_hashes()
    limits={k:Path("/sys/fs/cgroup/"+k).read_text().strip() for k in ("cpu.max","memory.max","memory.swap.max","pids.max")}
    expected={"cpu.max":"100000 100000","memory.max":"536870912","memory.swap.max":"0","pids.max":"64"}
    if limits!=expected or os.getuid()!=501:raise ValueError("actual resource gate")
    runtime={"limits":limits,"uid":os.getuid(),"pid":os.getpid(),"source_sha256":hashes}
    (out/"runtime.json").write_text(json.dumps(runtime,sort_keys=True)+"\n")
    metrics=[];status="COMPLETE";error=None
    for spec in PLAN["cases"]:
        c={**{k:spec[k] for k in ("id","pair","arm")},"pid":os.getpid(),"rows":[],"children":[],"status":"STOP","start_ns":0,"end_ns":0}
        started=[]
        try:
            for _ in range(spec["burners"]):started.append(start_child(spec["id"]))
            time.sleep(PLAN["settle_ns"]/1e9)
            c["start_ns"]=time.monotonic_ns()
            c['rows'],row_error=collect_rows(c['start_ns'],os.getpid(),PLAN)
            if row_error:raise ValueError(row_error)
            c["status"]="COMPLETE"
        except Exception as e:c["error"]=repr(e);status="STOP"
        finally:
            c["children"]=cleanup_children(started)
            c["end_ns"]=time.monotonic_ns()
        try:metric=validate_cell(c,spec,PLAN)
        except Exception as e:c["status"]="STOP";c["validation_error"]=repr(e);status="STOP"
        (out/(spec["id"]+".json")).write_text(json.dumps(c,sort_keys=True)+"\n")
        print(json.dumps({"cell":spec["id"],"status":c["status"],"rows":len(c["rows"])}),flush=True)
        if status=="STOP":error=c.get("validation_error",c.get("error"));break
        metrics.append(metric)
    try:source_unchanged=source_hashes()==hashes
    except Exception as e:source_unchanged=False;error=repr(e);status='STOP'
    result={"allocation":PLAN["allocation"],"status":status,"cells":len(metrics),"error":error,"decision":decision(metrics) if status=="COMPLETE" else None,"source_unchanged":source_unchanged}
    (out/"result.json").write_text(json.dumps(result,sort_keys=True)+"\n")
    print(json.dumps(result),flush=True)
    return 0 if status=="COMPLETE" else 2

if __name__=="__main__":
    if len(sys.argv)==3 and sys.argv[1]=="--burn":sys.exit(burn(sys.argv[2]))
    if len(sys.argv)==2:sys.exit(run(Path(sys.argv[1])))
    raise SystemExit("usage: probe.py OUT | --burn CASE")
