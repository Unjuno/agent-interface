#!/usr/bin/python3
from __future__ import annotations
import argparse,json,time
from pathlib import Path
from uno_common import document

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--pipe',required=True); ap.add_argument('--url',required=True); ap.add_argument('--arm',required=True,choices=['compare_set','recheck_set','controllers_lock_set']); ap.add_argument('--barrier',type=Path,required=True); ap.add_argument('--expected',default='book'); ap.add_argument('--desired',default='bookkeeperoffice'); a=ap.parse_args()
    c=document(a.pipe,a.url); locked=False; t0=time.monotonic_ns()
    if a.arm=='controllers_lock_set': c.lockControllers(); locked=True
    initial=str(c.Text.String)
    if initial!=a.expected: raise RuntimeError(f'initial mismatch {initial!r}')
    final_check=None
    if a.arm=='recheck_set':
        final_check=str(c.Text.String)
        if final_check!=a.expected: raise RuntimeError(f'final recheck mismatch {final_check!r}')
    a.barrier.mkdir(parents=True,exist_ok=True)
    (a.barrier/'guard.json').write_text(json.dumps({'arm':a.arm,'url':str(c.URL),'uid':str(c.RuntimeUID),'initial':initial,'final_check':final_check,'locked':locked,'guard_ns':time.monotonic_ns()})+'\n')
    deadline=time.monotonic()+10
    while not (a.barrier/'continue').exists():
        if time.monotonic()>deadline: raise RuntimeError('continue timeout')
        time.sleep(.001)
    prewrite=str(c.Text.String); write_start=time.monotonic_ns(); c.Text.String=a.desired; write_end=time.monotonic_ns(); post=str(c.Text.String)
    if locked: c.unlockControllers()
    print(json.dumps({'arm':a.arm,'initial':initial,'final_check':final_check,'prewrite':prewrite,'post':post,'locked':locked,'write_start_ns':write_start,'write_end_ns':write_end,'elapsed_ns':time.monotonic_ns()-t0},ensure_ascii=True))
    return 0
if __name__=='__main__': raise SystemExit(main())
