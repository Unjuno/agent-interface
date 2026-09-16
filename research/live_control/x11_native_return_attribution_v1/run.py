#!/usr/bin/env python3
"""One finite read-only X11 native-return diagnostic; no task input."""
import argparse, base64, ctypes, hashlib, itertools, json, lzma, os, platform
import select, signal, subprocess, sys, threading, time, traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASK = 'X11-NATIVE-RETURN-ATTRIBUTION-20260916-001'
BASE = '0a6012d189d2b4228d6f01462efc257e8d5e29dd'
PERIOD = 2_000_000
N = 32
ARMS = ('idle', 'process', 'thread')
SOURCE_FILES = ('native.c', 'run.py', 'audit.py', 'test_audit.py', 'build.py')

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p, obj): Path(p).write_text(json.dumps(obj, sort_keys=True, separators=(',', ':'))+'\n')
def sources(): return {n: sha(HERE/n) for n in SOURCE_FILES}
def schedule():
    return [dict(pair=i, arm=a, count=(0,511,512,513,1023,1024)[i], order=3*i+j)
            for i, arms in enumerate(itertools.permutations(ARMS)) for j, a in enumerate(arms)]
def topology(c):
    p=Path(f'/sys/devices/system/cpu/cpu{c}/topology')
    return {k:(p/k).read_text().strip() for k in ('physical_package_id','core_id','thread_siblings_list')}
def cpus():
    allowed=sorted(os.sched_getaffinity(0)); first=allowed[0]; t=topology(first)
    rest=[c for c in allowed if topology(c)['physical_package_id']==t['physical_package_id'] and topology(c)['core_id']!=t['core_id']]
    if len(rest)<2: raise RuntimeError('three guest cores required')
    return dict(observer=first, competitor=rest[0], server=rest[1], allowed=allowed,
                topology={str(c):topology(c) for c in allowed})
def ticks(tid):
    fields=Path(f'/proc/{os.getpid()}/task/{tid}/stat')
    if not fields.exists(): fields=Path(f'/proc/{tid}/stat')
    xs=fields.read_text().rsplit(')',1)[1].split()
    return int(xs[11])+int(xs[12])
def cgroup():
    return {n:Path('/sys/fs/cgroup',n).read_text() for n in ('cpu.max','cpu.stat') if Path('/sys/fs/cgroup',n).exists()}

def busy(cpu, stop, announce):
    os.sched_setaffinity(0,{cpu})
    announce(dict(pid=os.getpid(),tid=threading.get_native_id(),affinity=sorted(os.sched_getaffinity(0))))
    start=time.thread_time_ns(); x=0x12345678; loops=0
    while not stop.is_set():
        x=(1664525*x+1013904223)&0xffffffff; loops+=1
    return dict(cpu_ns=time.thread_time_ns()-start, iterations=loops, checksum=x,
                affinity=sorted(os.sched_getaffinity(0)))

class Competitor:
    def __init__(self, arm, cpu):
        self.arm=arm; self.record=None; self.p=None; self.th=None; self.stop=threading.Event()
        if arm=='idle': return
        self.record={'cpu':cpu,'errors':[]}
        if arm=='thread':
            ready=threading.Event()
            def announce(x): self.record['ready']=x; ready.set()
            def target():
                try: self.record['final']=busy(cpu,self.stop,announce)
                except BaseException: self.record['errors'].append(traceback.format_exc()); ready.set()
            self.th=threading.Thread(target=target,daemon=True); self.th.start()
            if not ready.wait(3) or self.record['errors']: raise RuntimeError('thread startup failed')
        else:
            self.p=subprocess.Popen([sys.executable,str(HERE/'run.py'),'hog',str(cpu)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            if not select.select([self.p.stdout],[],[],3)[0]: self.close(); raise RuntimeError('process startup failed')
            self.record['ready']=json.loads(self.p.stdout.readline())
        time.sleep(.03)
    def mark(self, name):
        if self.record is not None:
            tid=self.record['ready']['tid']
            self.record[name]=dict(ticks=ticks(tid),affinity=sorted(os.sched_getaffinity(tid)),
                alive=self.th.is_alive() if self.th else self.p.poll() is None,at_ns=time.monotonic_ns())
    def close(self):
        if self.th:
            self.stop.set(); self.th.join(2)
            self.record['cleaned']=not self.th.is_alive()
        if self.p:
            self.p.terminate()
            try: out,err=self.p.communicate(timeout=2); forced=False
            except subprocess.TimeoutExpired: self.p.kill(); out,err=self.p.communicate(); forced=True
            lines=out.strip().splitlines()
            self.record.update(final=json.loads(lines[-1]) if lines else None,stderr=err,
                               exitcode=self.p.returncode,forced=forced,cleaned=self.p.poll() is not None)
            self.p=None

def library():
    lib=ctypes.CDLL(str(HERE/'native.so'))
    lib.q_init.restype=ctypes.c_int
    lib.q_open.argtypes=[ctypes.c_char_p]; lib.q_open.restype=ctypes.c_void_p
    lib.q_close.argtypes=[ctypes.c_void_p]; lib.q_close.restype=None
    lib.q_read.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p]; lib.q_read.restype=ctypes.c_int
    lib.q_paint.argtypes=[ctypes.c_void_p,ctypes.c_int]; lib.q_paint.restype=ctypes.c_int
    lib.q_pause.argtypes=[ctypes.c_void_p]; lib.q_pause.restype=ctypes.c_int
    if not lib.q_init(): raise RuntimeError('XInitThreads failed')
    return lib

def run_case(lib,h,case,cs,n):
    if lib.q_paint(h,case['count']): raise RuntimeError('fixture paint failed')
    buf=ctypes.create_string_buffer(4096); tr=(ctypes.c_uint64*6)()
    load=Competitor(case['arm'],cs['competitor'])
    rec=dict(case=case, origin_ns=time.monotonic_ns(),rows=[],pixels={},affinity=sorted(os.sched_getaffinity(0)),observer_pid=os.getpid())
    # Row fields: due, Python-before, C-enter, X-before, X-after, C-exit,
    # Python-return, bytes-ready, X-thread-CPU-delta, pixel-digest.
    origin=rec['origin_ns']; due=origin+10_000_000
    try:
        load.mark('before'); c0=time.thread_time_ns()
        for _ in range(n):
            rem=due-time.monotonic_ns()
            if rem>0: time.sleep(rem/1e9)
            before=time.monotonic_ns(); status=lib.q_read(h,buf,4096,tr)
            returned=time.monotonic_ns(); raw=buf.raw; copied=time.monotonic_ns()
            if status: raise RuntimeError(f'capture failed {status}')
            dg=hashlib.sha256(raw).hexdigest(); rec['pixels'].setdefault(dg,base64.b64encode(raw).decode())
            rec['rows'].append([due-origin,before-origin,tr[0]-origin,tr[1]-origin,tr[2]-origin,
                tr[3]-origin,returned-origin,copied-origin,tr[5]-tr[4],dg])
            due+=PERIOD
            nnow=time.monotonic_ns()
            rec['rows'][-1].append(nnow-origin)
            if due<nnow-PERIOD: due+=((nnow-due)//PERIOD+1)*PERIOD
        rec['observer_cpu_ns']=time.thread_time_ns()-c0
        load.mark('after');rec['end_ns']=time.monotonic_ns()
    finally:
        load.close(); rec['load']=load.record
    return rec

def construction(lib,h):
    buf=ctypes.create_string_buffer(4096);t=(ctypes.c_uint64*6)(); rs=[]
    for n in (0,1,511,512,513,1023,1024):
        assert lib.q_paint(h,n)==0
        before=time.monotonic_ns();assert lib.q_read(h,buf,4096,t)==0;after=time.monotonic_ns()
        raw=buf.raw
        count=sum(raw[j:j+3]==b'\x32\x32\xdc' for j in range(0,4096,4))
        assert count==n and before<=t[0]<=t[1]<=t[2]<=t[3]<=after
        rs.append(dict(expected=n,count=count,raw_b64=base64.b64encode(raw).decode(),times=[before,*t[:4],after]))
    checks=[lib.q_read(None,buf,4096,t)==-1,lib.q_read(h,buf,4095,t)==-1,lib.q_read(h,buf,4096,None)==-1]
    assert all(checks)
    s=time.monotonic_ns(); assert lib.q_pause(t)==0; e=time.monotonic_ns()
    assert s<=t[0]<=t[1]<=e and t[1]-t[0]>=2_000_000
    return dict(static=rs,guards=checks,pause=[s,t[0],t[1],e])

def main():
    if len(sys.argv)>1 and sys.argv[1]=='hog':
        stop=threading.Event();signal.signal(signal.SIGTERM,lambda *_:stop.set())
        print(json.dumps(busy(int(sys.argv[2]),stop,lambda x:print(json.dumps(x),flush=True))),flush=True); return
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=('construction','formal'));ap.add_argument('--out',required=True);args=ap.parse_args()
    out=Path(args.out).resolve();out.mkdir(parents=True,exist_ok=False);cs=cpus()
    plan=json.loads((HERE/'prereg.json').read_text())
    if sources()!=plan['sources'] or sha(HERE/'native.so')!=plan['binary_sha256'] or cs!=plan['cpus'] or schedule()!=plan['schedule']:raise RuntimeError('frozen provenance mismatch')
    if args.mode=='formal':
        with (HERE/'CONSUMED').open('x') as f:f.write(TASK+'\n')
    result=dict(task=TASK,mode=args.mode,base=BASE,plan_sha256=sha(HERE/'prereg.json'),sources=sources(),binary_sha256=sha(HERE/'native.so'),records=[],errors=[],environment=dict(
        python=sys.version,platform=platform.platform(),gil=sys._is_gil_enabled(),switch_interval=sys.getswitchinterval(),
        cpus=cs,cpuinfo=Path('/proc/cpuinfo').read_text().split('\n\n')[0],
        clocks={n:vars(time.get_clock_info(n)) for n in ('monotonic','thread_time')},scheduler=os.sched_getscheduler(0),
        packages=subprocess.check_output(['dpkg-query','-W','xvfb','libx11-6'],text=True)),cgroup_before=cgroup())
    server=None;h=None
    try:
        r,w=os.pipe();log=(out/'xvfb.log').open('w')
        server=subprocess.Popen(['taskset','-c',str(cs['server']),'Xvfb','-displayfd',str(w),'-screen','0','160x120x24','-nolisten','tcp','-ac'],pass_fds=(w,),stdout=log,stderr=log);os.close(w)
        if not select.select([r],[],[],5)[0]:raise RuntimeError('Xvfb startup timeout')
        name=':'+os.read(r,64).decode().strip();os.close(r)
        os.sched_setaffinity(0,{cs['observer']});lib=library();h=lib.q_open(name.encode())
        if not h:raise RuntimeError('display unavailable')
        result['server']=dict(affinity=sorted(os.sched_getaffinity(server.pid)),display=name)
        if args.mode=='construction':result['construction']=construction(lib,h)
        cases=schedule() if args.mode=='formal' else schedule()[:3]
        from audit import check_case
        for case in cases:
            rec=run_case(lib,h,case,cs,N if args.mode=='formal' else 4)
            result['records'].append(rec);dump(out/'raw.json',result)
            check_case(rec,cs,N if args.mode=='formal' else 4)
            print(case,'integrity pass',flush=True)
        result['server']['alive_after']=server.poll() is None
        result['server']['affinity_after']=sorted(os.sched_getaffinity(server.pid))
    except BaseException:result['errors'].append(traceback.format_exc());raise
    finally:
        if h:lib.q_close(h)
        if server:
            server.terminate()
            try:server.wait(timeout=3)
            except subprocess.TimeoutExpired:server.kill();server.wait()
            result.setdefault('server',{}).update(exitcode=server.returncode,reaped=server.poll() is not None)
        os.sched_setaffinity(0,set(cs['allowed']));result['sources_after']=sources();result['cgroup_after']=cgroup()
        dump(out/'raw.json',result);(out/'raw.json.xz').write_bytes(lzma.compress((out/'raw.json').read_bytes()))
if __name__=='__main__':main()
