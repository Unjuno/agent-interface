"""Versioned orchestration-only repair: four bounded, single-consumption batches.

Original probe.py, fence.py, fixture.py, and native-01 evidence stay unchanged.
Each batch owns a fresh private desktop. A killed/failed claim cannot be resumed.
Local flock is not a distributed exactly-once guarantee.
"""
from __future__ import annotations
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import time
from Xlib import X, XK, display
from Xlib.ext import xtest
from private_desktop import desktop
from probe import run_case, save, load, digest

HERE=Path(__file__).resolve().parent


def validate_next(root: Path, plan: dict, batch: int) -> list[tuple[int, dict]]:
    if type(batch) is not int or not 0 <= batch < 4:
        raise ValueError('batch must be 0..3')
    if root.name != plan['allocation']:
        raise ValueError('allocation name mismatch')
    if (root/'failure.json').exists():raise ValueError('failed allocation cannot resume')
    for prior in range(batch):
        result=load(root/f'batch-{prior:02d}/complete.json')
        if result.get('pass') is not True:raise ValueError('prior batch incomplete')
    if (root/f'batch-{batch:02d}').exists():raise FileExistsError('batch already consumed')
    return list(enumerate(plan['schedule']))[batch*6:(batch+1)*6]


def run(root: Path,batch: int) -> None:
    plan=load(HERE/'plan-v2.json')
    for name,sha in plan['sources'].items():
        if digest(HERE/name)!=sha:raise ValueError('source hash mismatch '+name)
    if batch==0:
        root.mkdir(parents=True,exist_ok=False)
        save(root/'plan.json',plan)
    if load(root/'plan.json')!=plan:raise ValueError('allocation plan changed')
    with (root/'allocation.lock').open('a') as lock:
        fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        cases=validate_next(root,plan,batch)
        claim=root/f'batch-{batch:02d}';claim.mkdir()
        save(claim/'claim.json',dict(pid=os.getpid(),batch=batch,started_ns=time.perf_counter_ns()))
        cpu=next(x.split(':',1)[1].strip() for x in Path('/proc/cpuinfo').read_text().splitlines() if x.startswith('model name'))
        save(claim/'environment.json',dict(cpu=cpu,affinity=sorted(os.sched_getaffinity(0)),
            cpu_clock='not pinned',python=platform.python_version(),kernel=platform.release(),
            xterm=subprocess.check_output(['xterm','-version'],text=True).strip(),
            clock=time.get_clock_info('perf_counter').implementation,
            clock_resolution_s=time.get_clock_info('perf_counter').resolution,
            batch_cases=6,display='private Xvfb/Openbox; one display per batch',
            hold_ms=25,retry_ms=100,window_ms=500,poll_ms=3,model_calls=0,
            measurement_network_calls=0,production_executor_used=False))
        results=[]
        try:
            with desktop(claim) as env:
                conn=display.Display(env['DISPLAY'])
                code=conn.keysym_to_keycode(XK.string_to_keysym('Return'))
                try:
                    for index,case in cases:
                        result=run_case(root/f'case-{index:02d}',case,env,conn,code)
                        results.append(result)
                        print(json.dumps(dict(index=index,**case,inputs=len(result['input']),
                            effects=result['effect_count'],outcome=result['controller_outcome'],passed=result['pass'])),flush=True)
                        if not result['pass']:raise RuntimeError('first failed case; no retry')
                finally:
                    xtest.fake_input(conn,X.KeyRelease,code);conn.sync();conn.close()
            save(claim/'complete.json',dict(pass_=True,**{'pass':True},case_indices=[i for i,_ in cases],ended_ns=time.perf_counter_ns()))
            if batch==3:
                all_results=[load(root/f'case-{i:02d}/result.json') for i in range(len(plan['schedule']))]
                save(root/'summary.json',dict(schema='pending-effect-batched-calibration-v2',
                    allocation=root.name,completed=len(all_results),**{'pass':all(r['pass'] for r in all_results)},
                    rows=[dict(case=r['case'],inputs=len(r['input']),effects=r['effect_count'],
                               outcome=r['controller_outcome'],passed=r['pass']) for r in all_results]))
        except BaseException as exc:
            save(root/'failure.json',dict(batch=batch,error=repr(exc),completed_in_batch=len(results)))
            raise


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--batch',type=int,required=True)
    a=p.parse_args();run(a.out,a.batch)
