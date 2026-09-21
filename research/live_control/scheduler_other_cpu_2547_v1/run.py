#!/usr/bin/env python3
"""Issue 3934: bounded, single-allocation Linux scheduling experiment."""
import ctypes
import hashlib
import itertools
import json
import os
from pathlib import Path
import platform
import select
import signal
import statistics
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
PERIOD = 2_000_000
COUNT = 300
ARMS = ('IDLE', 'SAME_CORE', 'OTHER_CORE')
ORDERS = list(itertools.permutations(ARMS)) * 5
LIBC = ctypes.CDLL(None)
LIBC.sched_getcpu.restype = ctypes.c_int


def write_new(path, value):
    with Path(path).open('x', encoding='utf-8') as f:
        json.dump(value, f, sort_keys=True, separators=(',', ':'))
        f.write('\n')
        f.flush()
        os.fsync(f.fileno())


def ident():
    return dict(pid=os.getpid(), tid=__import__('threading').get_native_id(),
                affinity=sorted(os.sched_getaffinity(0)), cpu=LIBC.sched_getcpu(),
                scheduler=os.sched_getscheduler(0), nice=os.getpriority(os.PRIO_PROCESS, 0))


def environment():
    allowed = sorted(os.sched_getaffinity(0))
    topology = {}
    for c in allowed:
        p = Path(f'/sys/devices/system/cpu/cpu{c}/topology')
        topology[str(c)] = {k: (p / k).read_text().strip() for k in
                           ('core_id', 'physical_package_id', 'thread_siblings_list')}
    return dict(python=sys.version, executable=sys.executable,
                executable_sha256=hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest(),
                platform=platform.platform(), allowed=allowed, topology=topology,
                clock=vars(time.get_clock_info('monotonic')), switch_interval=sys.getswitchinterval(),
                scheduler=os.sched_getscheduler(0), nice=os.getpriority(os.PRIO_PROCESS, 0),
                engine='provided_execution_container', docker_image_identity=None)


def hog(cpu):
    os.sched_setaffinity(0, {cpu})
    stopped = [False, False]
    def stop(signum, frame):
        stopped[0] = True
        stopped[1] = signum == signal.SIGALRM
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGALRM, stop)
    signal.setitimer(signal.ITIMER_REAL, 4)
    ready = dict(kind='ready', identity=ident(), monotonic_ns=time.monotonic_ns(),
                 process_ns=time.process_time_ns())
    print(json.dumps(ready, separators=(',', ':')), flush=True)
    x = 0x12345678
    while not stopped[0]:
        x = (1664525*x+1013904223) & 0xffffffff
        # Same LCG as #316. Readiness/termination instrumentation is disclosed.
    end = dict(kind='stopped', identity=ident(), monotonic_ns=time.monotonic_ns(),
               process_ns=time.process_time_ns(), timed_out=stopped[1], value=x)
    print(json.dumps(end, separators=(',', ':')), flush=True)
    return 2 if stopped[1] else 0


def start_child(cpu):
    p = subprocess.Popen([sys.executable, '-B', str(ROOT/'run.py'), 'hog', str(cpu)],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        if not select.select([p.stdout], [], [], 2)[0]:
            raise TimeoutError('child readiness')
        ready = json.loads(p.stdout.readline())
        if ready['identity']['affinity'] != [cpu] or ready['identity']['cpu'] != cpu:
            raise RuntimeError('child affinity')
        observed = sorted(os.sched_getaffinity(p.pid))
        if observed != [cpu]:
            raise RuntimeError('parent-observed child affinity')
        # Retain the inherited 30 ms premeasurement settle; both load arms equal.
        time.sleep(.03)
        return p, ready, observed
    except BaseException:
        p.terminate()
        try:
            p.communicate(timeout=2)
        except subprocess.TimeoutExpired:
            p.kill(); p.communicate()
        raise


def finish_child(p, ready, observed):
    p.terminate()
    try:
        out, err = p.communicate(timeout=2)
    except subprocess.TimeoutExpired:
        p.kill()
        out, err = p.communicate()
        raise RuntimeError('child termination timeout: '+repr((out, err)))
    terminal = json.loads(out)
    if p.returncode != 0 or err or terminal['timed_out']:
        raise RuntimeError('child failed: '+repr((p.returncode, out, err)))
    return dict(pid=p.pid, ready=ready, observed_affinity=observed,
                terminal=terminal, returncode=p.returncode, stderr=err, reaped=True)


def percentile(values, q):
    ordered = sorted(values)
    t = (len(ordered)-1)*q
    a = int(t); b = min(a+1, len(ordered)-1)
    return ordered[a]+(ordered[b]-ordered[a])*(t-a)


def stats(samples):
    values = [max(0, r[2]) for r in samples]
    return dict(n=len(values), p50_ns=percentile(values,.5), p95_ns=percentile(values,.95),
                p99_ns=percentile(values,.99), max_ns=max(values),
                late_deadlines_ge_period=sum(x >= PERIOD for x in values))


def block(triplet, position, arm):
    os.sched_setaffinity(0, {0})
    child = None
    ready = observed = None
    if arm != 'IDLE':
        child, ready, observed = start_child(0 if arm == 'SAME_CORE' else 1)
    result = dict(triplet=triplet, position=position, arm=arm, before=ident(),
                  child_alive_before=(child.poll() is None if child else False))
    try:
        due = time.monotonic_ns()+10_000_000
        samples = []
        proc0=time.process_time_ns(); thread0=time.thread_time_ns(); wall0=time.monotonic_ns()
        for _ in range(COUNT):
            rem=due-time.monotonic_ns()
            if rem>0: time.sleep(rem/1e9)
            wake=time.monotonic_ns()
            samples.append([due,wake,wake-due])
            due += PERIOD
        wall1=time.monotonic_ns(); thread1=time.thread_time_ns(); proc1=time.process_time_ns()
        result.update(samples=samples, after=ident(), wall=[wall0,wall1],
                      process=[proc0,proc1], thread=[thread0,thread1], stats=stats(samples),
                      child_alive_after=(child.poll() is None if child else False))
    finally:
        result['child'] = finish_child(child, ready, observed) if child else None
    return result


def candidate_summary(blocks):
    ratios=[]; distances=[]; sm=[]
    for i in range(30):
        group={b['arm']:b['stats']['max_ns'] for b in blocks if b['triplet']==i}
        idle, same, other = (group[a] for a in ARMS)
        ratios.append(same/max(idle,1)); sm.append(same)
        distances.append(abs(other-idle)/max(abs(same-idle),1))
    metrics=dict(median_same_idle_ratio=statistics.median(ratios),
                 median_same_max_ns=statistics.median(sm),
                 same_blocks_ge_1ms=sum(v>=1_000_000 for v in sm),
                 median_other_idle_relative_distance=statistics.median(distances))
    gates=[metrics['median_same_idle_ratio']>=2,metrics['median_same_max_ns']>=1_000_000,
           metrics['same_blocks_ge_1ms']>=15, metrics['median_other_idle_relative_distance']<=.5]
    return dict(metrics=metrics,gates=gates,decision=('PASS_SAME_CORE_ATTRIBUTION_SCOPED'
                if all(gates) else 'HOLD_CONTENTION_SOURCE_UNRESOLVED'))


def measure(out):
    freeze=json.loads((ROOT/'FREEZE.json').read_text())
    for name, digest in freeze['sha256'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest:
            raise RuntimeError('STOP_SOURCE_MISMATCH: '+name)
    if environment()!=json.loads((ROOT/'environment.json').read_text()):
        raise RuntimeError('STOP_ENVIRONMENT_MISMATCH')
    out=Path(out); out.mkdir(exist_ok=False)
    original=sorted(os.sched_getaffinity(0))
    start=time.monotonic_ns()
    write_new(out/'START.json', dict(allocation='scheduler-other-cpu-20260922-01',
              monotonic_ns=start, pid=os.getpid(), freeze_sha256=hashlib.sha256((ROOT/'FREEZE.json').read_bytes()).hexdigest()))
    blocks=[]
    try:
        for triplet, order in enumerate(ORDERS):
            for position, arm in enumerate(order):
                row=block(triplet,position,arm)
                write_new(out/f'block-{len(blocks):02d}.json',row)
                blocks.append(row)
            print(json.dumps({'completed_triplets':triplet+1,'blocks':len(blocks)}),flush=True)
        write_new(out/'RESULT.json',candidate_summary(blocks))
        returncode=0
    except BaseException as exc:
        write_new(out/'STOP.json',dict(kind=type(exc).__name__,detail=str(exc),completed_blocks=len(blocks)))
        returncode=1
    finally:
        os.sched_setaffinity(0,set(original))
        write_new(out/'END.json',dict(monotonic_ns=time.monotonic_ns(),completed_blocks=len(blocks),
                   restored_affinity=sorted(os.sched_getaffinity(0)), returncode=locals().get('returncode',1)))
    return returncode


if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1]=='hog':
        sys.exit(hog(int(sys.argv[2])))
    elif len(sys.argv)==3 and sys.argv[1]=='measure':
        sys.exit(measure(sys.argv[2]))
    else:
        raise SystemExit('usage: run.py hog CPU | run.py measure FRESH_OUTPUT')
