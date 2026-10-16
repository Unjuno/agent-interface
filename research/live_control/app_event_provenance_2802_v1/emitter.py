from __future__ import annotations
import json, os, sys, time
from pathlib import Path

CLOCKS={
    'MONOTONIC': time.CLOCK_MONOTONIC,
    'BOOTTIME': getattr(time,'CLOCK_BOOTTIME', time.CLOCK_MONOTONIC),
}

def now(domain):
    return time.clock_gettime_ns(CLOCKS[domain])

def emit(label, source_id, seq, domain):
    row={'label':label,'source_id':source_id,'seq':seq,'clock_domain':domain,'t_ns':now(domain),'pid':os.getpid()}
    print(json.dumps(row,sort_keys=True),flush=True)
    return row

def main():
    cfg=json.loads(sys.stdin.readline())
    state=Path(cfg['state_path'])
    state.write_text(json.dumps({'state':'READY','pid':os.getpid()},sort_keys=True))
    s=cfg['scenario']
    if s=='SAME_DOMAIN_CONTIGUOUS':
        emit('A','app',1,'MONOTONIC'); time.sleep(0.002); state.write_text(json.dumps({'state':'DONE'},sort_keys=True)); emit('B','app',2,'MONOTONIC')
    elif s=='CROSS_DOMAIN':
        emit('A','app',1,'MONOTONIC'); time.sleep(0.002); state.write_text(json.dumps({'state':'DONE'},sort_keys=True)); emit('B','app',2,'BOOTTIME')
    elif s=='GAPPED_SEQUENCE':
        emit('A','app',1,'MONOTONIC'); time.sleep(0.002); state.write_text(json.dumps({'state':'DONE'},sort_keys=True)); emit('B','app',3,'MONOTONIC')
    elif s=='REGRESSED_SEQUENCE':
        emit('A','app',2,'MONOTONIC'); time.sleep(0.002); state.write_text(json.dumps({'state':'DONE'},sort_keys=True)); emit('B','app',1,'MONOTONIC')
    elif s=='CROSS_SOURCE':
        emit('A','app-a',1,'MONOTONIC'); time.sleep(0.002); state.write_text(json.dumps({'state':'DONE'},sort_keys=True)); emit('B','app-b',2,'MONOTONIC')
    elif s=='LATE_B':
        emit('A','app',1,'MONOTONIC'); time.sleep(cfg['late_sleep_s']); state.write_text(json.dumps({'state':'DONE'},sort_keys=True)); emit('B','app',2,'MONOTONIC')
    else:
        raise SystemExit('bad scenario')

if __name__=='__main__': main()
