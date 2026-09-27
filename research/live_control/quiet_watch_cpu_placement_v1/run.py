#!/usr/bin/env python3
"""Isolated CPU-placement experiment. No GUI, input, networking or priority changes."""
import hashlib, itertools, json, os, platform, select, subprocess, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parent

def encode(x):
    return (json.dumps(x, sort_keys=True, separators=(',', ':')) + '\n').encode()

def text(path):
    try: return Path(path).read_text().strip()
    except OSError: return None

def topology(cpu):
    p = f'/sys/devices/system/cpu/cpu{cpu}/topology/'
    return {k: text(p+k) for k in ('physical_package_id','core_id','thread_siblings_list')}

def cgroup():
    return {k: text('/sys/fs/cgroup/'+k) for k in ('cpu.max','cpu.stat','cpuset.cpus.effective')}

def ticks(pid):
    fields = Path(f'/proc/{pid}/stat').read_text().rsplit(') ', 1)[1].split()
    return int(fields[11]) + int(fields[12])

def hog(cpu):
    os.sched_setaffinity(0, {cpu})
    print(json.dumps({'pid':os.getpid(),'affinity':sorted(os.sched_getaffinity(0)),
                      'policy':os.sched_getscheduler(0),'nice':os.getpriority(os.PRIO_PROCESS,0)}), flush=True)
    x = 0x12345678
    while True:
        x = (1664525*x+1013904223) & 0xffffffff

def source_hashes():
    f = json.loads((ROOT/'freeze.json').read_text())
    for name, digest in f['sha256'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest() != digest:
            raise RuntimeError('source hash mismatch: '+name)
    return f['sha256']

def block(plan, arm, cpu, other, index):
    child = None
    r = {'index':index,'arm':arm,'parent_affinity_before':sorted(os.sched_getaffinity(0)),
         'cgroup_before':cgroup(),'child':None}
    try:
        if arm != 'idle':
            dest = cpu if arm == 'same' else other
            child = subprocess.Popen([sys.executable,str(ROOT/'run.py'),'hog',str(dest)],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if not select.select([child.stdout], [], [], 5)[0]:
                raise RuntimeError('child readiness timeout')
            r['child'] = {'ready':json.loads(child.stdout.readline()),'requested_cpu':dest}
        time.sleep(plan['settle_ns']/1e9)
        if child:
            r['child']['alive_before'] = child.poll() is None
            r['child']['affinity_before'] = sorted(os.sched_getaffinity(child.pid))
            r['child']['ticks_before'] = ticks(child.pid)
            if not r['child']['alive_before']: raise RuntimeError('child exited before block')
        start = time.monotonic_ns()
        p0 = time.process_time_ns(); c0 = time.thread_time_ns()
        due = start + plan['start_delay_ns']
        samples = []
        for _ in range(plan['samples_per_block']):
            rem = due-time.monotonic_ns()
            if rem > 0: time.sleep(rem/1e9)
            wake = time.monotonic_ns()
            samples.append([due,wake,wake-due])
            due += plan['period_ns']
        c1 = time.thread_time_ns(); p1 = time.process_time_ns()
        r.update(start_ns=start,end_ns=time.monotonic_ns(),samples=samples,
                 thread_cpu_ns=c1-c0,process_cpu_ns=p1-p0)
        if child:
            r['child']['alive_after'] = child.poll() is None
            r['child']['affinity_after'] = sorted(os.sched_getaffinity(child.pid))
            r['child']['ticks_after'] = ticks(child.pid)
        r['parent_affinity_after'] = sorted(os.sched_getaffinity(0))
        r['cgroup_after'] = cgroup()
    finally:
        if child:
            child.terminate()
            try: child.wait(timeout=2)
            except subprocess.TimeoutExpired: child.kill(); child.wait(timeout=2)
            if r['child'] is not None: r['child']['exit_code'] = child.returncode
            child.stdout.close(); child.stderr.close()
    return r

def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'hog':
        return hog(int(sys.argv[2]))
    if len(sys.argv) != 3 or sys.argv[1] not in ('preflight','measure'):
        raise SystemExit('usage: run.py preflight|measure OUT_DIRECTORY')
    mode = sys.argv[1]; out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
    with (out/'allocation.used').open('x') as f: f.write(mode+'\n')
    plan = json.loads((ROOT/'plan.json').read_text()); hashes = source_hashes()
    allowed = sorted(os.sched_getaffinity(0)); cpu = allowed[0]
    topo = {str(c):topology(c) for c in allowed}
    others = [c for c in allowed if topo[str(c)]['core_id'] != topo[str(cpu)]['core_id']
              and topo[str(c)]['physical_package_id'] == topo[str(cpu)]['physical_package_id']]
    if not others: raise RuntimeError('no guest-reported different core')
    other = min(others)
    env = {'python':sys.version,'platform':platform.platform(),'initial_affinity':allowed,
           'observer_cpu':cpu,'other_cpu':other,'topology':topo,'cpuinfo':text('/proc/cpuinfo'),
           'policy':os.sched_getscheduler(0),'nice':os.getpriority(os.PRIO_PROCESS,0),
           'clock':vars(time.get_clock_info('monotonic')),'clock_ticks_per_second':os.sysconf('SC_CLK_TCK'),
           'cgroup':cgroup(),'host_physical_placement':'UNKNOWN'}
    payload = {'schema':'cpu_placement_v1','task':plan['task'],'mode':mode,'source_sha256':hashes,
               'environment':env,'blocks':[]}
    os.sched_setaffinity(0, {cpu})
    orders = plan['orders'] if mode == 'measure' else [plan['orders'][0]]
    try:
        with (out/'blocks.jsonl').open('xb') as journal:
            for triplet, order in enumerate(orders):
                for arm in order:
                    r = block(plan,arm,cpu,other,len(payload['blocks'])); r['triplet'] = triplet
                    payload['blocks'].append(r); journal.write(encode(r)); journal.flush(); os.fsync(journal.fileno())
    except BaseException as e:
        payload['error'] = type(e).__name__+': '+str(e)
        (out/'partial.json').write_bytes(encode(payload)); raise
    finally:
        os.sched_setaffinity(0,set(allowed))
    (out/'raw.json').write_bytes(encode(payload))
    print(json.dumps({'mode':mode,'blocks':len(payload['blocks']),'sha256':hashlib.sha256(encode(payload)).hexdigest()}))

if __name__ == '__main__': main()
