#!/usr/bin/env python3
import json, os, statistics, subprocess, sys, time
from pathlib import Path

PERIOD_NS=2_000_000
BLOCK_NS=600_000_000
PAIRS=20
SAMPLES=BLOCK_NS//PERIOD_NS
THRESH_RATIO=2.0
THRESH_MAX_NS=1_000_000
THRESH_BLOCKS=10

def pct(xs,p):
    ys=sorted(xs); k=(len(ys)-1)*p; lo=int(k); hi=min(lo+1,len(ys)-1); f=k-lo
    return ys[lo]*(1-f)+ys[hi]*f

def pin(cpu):
    os.sched_setaffinity(0,{cpu})

def hog(cpu):
    pin(cpu)
    x=0x12345678
    while True:
        x=(1664525*x+1013904223)&0xffffffff
        if x==0xdeadbeef: print(x)

def run_block(cpu, contention):
    child=None
    if contention:
        child=subprocess.Popen([sys.executable,__file__,'hog',str(cpu)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(0.03)
    try:
        pin(cpu)
        due=time.monotonic_ns()+10_000_000
        wakes=[]
        proc0=time.process_time_ns(); thread0=time.thread_time_ns(); wall0=time.monotonic_ns()
        for _ in range(SAMPLES):
            rem=due-time.monotonic_ns()
            if rem>0: time.sleep(rem/1e9)
            wake=time.monotonic_ns()
            wakes.append((due,wake,wake-due))
            due += PERIOD_NS
        wall1=time.monotonic_ns(); thread1=time.thread_time_ns(); proc1=time.process_time_ns()
        l=[max(0,r[2]) for r in wakes]
        missed=sum(1 for x in l if x>=PERIOD_NS)
        return {'n':len(l),'p50_late_ns':pct(l,.50),'p95_late_ns':pct(l,.95),'p99_late_ns':pct(l,.99),'max_late_ns':max(l),'missed_nominal_slots':missed,'wall_ns':wall1-wall0,'thread_cpu_ns':thread1-thread0,'process_cpu_ns':proc1-proc0,'samples':wakes}
    finally:
        if child is not None:
            child.terminate()
            try: child.wait(timeout=1)
            except subprocess.TimeoutExpired: child.kill(); child.wait()

def measure(out):
    allowed=sorted(os.sched_getaffinity(0));
    if not allowed: raise RuntimeError('no affinity')
    cpu=allowed[0]
    blocks=[]
    for i in range(PAIRS):
        order=['idle','contended'] if i%2==0 else ['contended','idle']
        rec={'pair':i,'order':order,'arms':{}}
        for arm in order:
            rec['arms'][arm]=run_block(cpu, arm=='contended')
        blocks.append(rec)
    ratios=[]; cmax=[]
    for b in blocks:
        im=b['arms']['idle']['max_late_ns']; cm=b['arms']['contended']['max_late_ns']
        ratios.append(cm/max(im,1)); cmax.append(cm)
    med_ratio=statistics.median(ratios); med_c=statistics.median(cmax); over=sum(x>=THRESH_MAX_NS for x in cmax)
    decision='CONTENTION_TAIL_REPRODUCED_SCOPED' if med_ratio>=THRESH_RATIO and med_c>=THRESH_MAX_NS and over>=THRESH_BLOCKS else 'HOLD_CONTENTION_ATTRIBUTION'
    payload={'schema':'quiet_watch_scheduler_contention_v1_result','constants':{'period_ns':PERIOD_NS,'block_ns':BLOCK_NS,'pairs':PAIRS,'samples_per_block':SAMPLES,'threshold_ratio':THRESH_RATIO,'threshold_max_ns':THRESH_MAX_NS,'threshold_blocks':THRESH_BLOCKS},'environment':{'python':sys.version,'allowed_affinity_initial':allowed,'selected_cpu':cpu,'platform':sys.platform},'blocks':blocks,'summary':{'median_paired_max_lateness_ratio':med_ratio,'contended_median_max_lateness_ns':med_c,'contended_blocks_max_ge_1ms':over,'ratios':ratios,'decision':decision}}
    Path(out).write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n')
    print(json.dumps(payload['summary'],indent=2))

def main():
    if len(sys.argv)>=2 and sys.argv[1]=='hog': hog(int(sys.argv[2]))
    elif len(sys.argv)>=3 and sys.argv[1]=='measure': measure(sys.argv[2])
    else: raise SystemExit('usage: run.py measure OUT | run.py hog CPU')
if __name__=='__main__': main()
