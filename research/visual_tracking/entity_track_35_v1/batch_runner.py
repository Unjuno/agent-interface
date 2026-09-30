#!/usr/bin/env python3
"""Execution-envelope-only wrapper for allocation 02; imports frozen study semantics unchanged."""
import json, sys, time
from pathlib import Path
import study
BATCHES=4
BATCH_SIZE=12

def check_partition():
    sched=study.schedule(); parts=[sched[i*BATCH_SIZE:(i+1)*BATCH_SIZE] for i in range(BATCHES)]
    return {'cases':len(sched),'batches':[len(p) for p in parts],'flatten_exact':sum(parts,[])==sched}

def run(batch_index,out):
    if batch_index not in range(BATCHES): raise SystemExit('bad batch')
    out=Path(out); out.mkdir(exist_ok=False)
    sched=study.schedule(); start=batch_index*BATCH_SIZE; owned=sched[start:start+BATCH_SIZE]
    xp,disp=study.start_xvfb(); rows=[]; rc=1
    (out/'START.json').write_text(json.dumps({'allocation':'entity-track-live-20260922-02','batch':batch_index,'global_start':start,'planned':len(owned),'started_ns':time.monotonic_ns()},sort_keys=True)+'\n')
    try:
        for off,(scenario,policy,rep) in enumerate(owned):
            idx=start+off
            row=study.run_case(disp,scenario,policy,rep,idx); rows.append(row)
            (out/f'case-{idx:02d}.json').write_text(json.dumps(row,sort_keys=True,separators=(',',':'))+'\n')
        rc=0
    except BaseException as e:
        (out/'STOP.json').write_text(json.dumps({'type':type(e).__name__,'detail':repr(e),'complete':len(rows)},sort_keys=True)+'\n')
    finally:
        xe=study.finish_xvfb(xp)
        (out/'END.json').write_text(json.dumps({'returncode':rc,'batch':batch_index,'cases':len(rows),'xvfb':xe,'ended_ns':time.monotonic_ns()},sort_keys=True)+'\n')
    return rc
if __name__=='__main__':
    if len(sys.argv)==2 and sys.argv[1]=='--check': print(json.dumps(check_partition(),sort_keys=True)); raise SystemExit(0)
    if len(sys.argv)!=3: raise SystemExit('batch_runner.py BATCH_INDEX OUT')
    raise SystemExit(run(int(sys.argv[1]),sys.argv[2]))
