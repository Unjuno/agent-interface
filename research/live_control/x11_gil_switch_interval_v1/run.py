#!/usr/bin/env python3
import argparse, base64, ctypes, hashlib, json, lzma, os, platform, select, statistics, subprocess, sys, threading, time, traceback
from pathlib import Path

HERE=Path(__file__).resolve().parent
TASK='X11-GIL-SWITCH-INTERVAL-20260916-001'
BASE='b104db1b17fa717eecefca0209d243ca35332524'
PERIOD_NS=2_000_000
N=32
PAIRS=6
ARMS=('gil5ms','gil1ms')
INTERVALS={'gil5ms':0.005,'gil1ms':0.001}
COUNTS=(0,511,512,513,1023,1024)
SOURCE_FILES=('native.c','run.py','audit.py','test_audit.py','build.py')

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,o): Path(p).write_text(json.dumps(o,sort_keys=True,separators=(',',':'))+'\n')
def sources(): return {n:sha(HERE/n) for n in SOURCE_FILES}
def schedule():
    out=[]
    for i in range(PAIRS):
        order=ARMS if i%2==0 else tuple(reversed(ARMS))
        for arm in order:
            out.append({'pair':i,'arm':arm,'count':COUNTS[i],'order':len(out)})
    return out

def topology(c):
    p=Path(f'/sys/devices/system/cpu/cpu{c}/topology')
    return {k:(p/k).read_text().strip() for k in ('physical_package_id','core_id','thread_siblings_list')}
def cpus():
    allowed=sorted(os.sched_getaffinity(0)); obs=allowed[0]; t=topology(obs)
    rest=[c for c in allowed if topology(c)['physical_package_id']==t['physical_package_id'] and topology(c)['core_id']!=t['core_id']]
    if len(rest)<2: raise RuntimeError('three guest cores required')
    return {'observer':obs,'competitor':rest[0],'server':rest[1],'allowed':allowed,'topology':{str(c):topology(c) for c in allowed}}
def ticks(tid):
    p=Path(f'/proc/{os.getpid()}/task/{tid}/stat')
    xs=p.read_text().rsplit(')',1)[1].split(); return int(xs[11])+int(xs[12])

def busy(cpu,stop,ready,record):
    os.sched_setaffinity(0,{cpu})
    tid=threading.get_native_id(); record['ready']={'tid':tid,'affinity':sorted(os.sched_getaffinity(0))}; ready.set()
    start=time.thread_time_ns(); x=0x12345678; loops=0
    try:
        while not stop.is_set():
            x=(1664525*x+1013904223)&0xffffffff; loops+=1
    finally:
        record['final']={'cpu_ns':time.thread_time_ns()-start,'iterations':loops,'checksum':x,'affinity':sorted(os.sched_getaffinity(0))}

def library():
    lib=ctypes.CDLL(str(HERE/'native.so'))
    lib.q_init.restype=ctypes.c_int
    lib.q_open.argtypes=[ctypes.c_char_p];lib.q_open.restype=ctypes.c_void_p
    lib.q_close.argtypes=[ctypes.c_void_p]
    lib.q_read.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p];lib.q_read.restype=ctypes.c_int
    lib.q_paint.argtypes=[ctypes.c_void_p,ctypes.c_int];lib.q_paint.restype=ctypes.c_int
    if not lib.q_init(): raise RuntimeError('XInitThreads failed')
    return lib

def run_case(lib,h,case,cs,n):
    old_interval=sys.getswitchinterval(); target=INTERVALS[case['arm']]; sys.setswitchinterval(target)
    if abs(sys.getswitchinterval()-target)>1e-9: raise RuntimeError('switch interval mismatch')
    if lib.q_paint(h,case['count']): raise RuntimeError('paint failed')
    stop=threading.Event(); ready=threading.Event(); load={'errors':[]}
    th=threading.Thread(target=lambda: busy(cs['competitor'],stop,ready,load),daemon=True); th.start()
    if not ready.wait(3): raise RuntimeError('competitor startup timeout')
    time.sleep(.03)
    tid=load['ready']['tid']; load['before']={'ticks':ticks(tid),'affinity':sorted(os.sched_getaffinity(tid)),'alive':th.is_alive()}
    buf=ctypes.create_string_buffer(4096); tr=(ctypes.c_uint64*6)()
    rec={'case':case,'rows':[],'pixels':{},'switch_interval':sys.getswitchinterval(),'observer_affinity':sorted(os.sched_getaffinity(0)),'load':load}
    origin=time.monotonic_ns(); due=origin+10_000_000
    try:
        for _ in range(n):
            rem=due-time.monotonic_ns()
            if rem>0: time.sleep(rem/1e9)
            before=time.monotonic_ns(); status=lib.q_read(h,buf,4096,tr); returned=time.monotonic_ns(); raw=buf.raw; copied=time.monotonic_ns()
            if status: raise RuntimeError(f'q_read {status}')
            dg=hashlib.sha256(raw).hexdigest(); rec['pixels'].setdefault(dg,base64.b64encode(raw).decode())
            rec['rows'].append({'due_ns':due-origin,'python_before_ns':before-origin,'c_enter_ns':tr[0]-origin,'x_before_ns':tr[1]-origin,'x_after_ns':tr[2]-origin,'c_exit_ns':tr[3]-origin,'python_return_ns':returned-origin,'bytes_ready_ns':copied-origin,'x_thread_cpu_ns':tr[5]-tr[4],'pixel_digest':dg})
            due+=PERIOD_NS; now=time.monotonic_ns()
            if due<now-PERIOD_NS: due+=((now-due)//PERIOD_NS+1)*PERIOD_NS
        load['after']={'ticks':ticks(tid),'affinity':sorted(os.sched_getaffinity(tid)),'alive':th.is_alive()}
        rec['rows_sha256']=hashlib.sha256(json.dumps(rec['rows'],sort_keys=True,separators=(',',':')).encode()).hexdigest()
    finally:
        stop.set(); th.join(2); load['cleaned']=not th.is_alive(); sys.setswitchinterval(old_interval)
    return rec

def summary(records):
    cases=[]
    for rec in records:
        posts=[r['python_return_ns']-r['c_exit_ns'] for r in rec['rows']]
        xs=[r['x_after_ns']-r['x_before_ns'] for r in rec['rows']]
        total=[r['bytes_ready_ns']-r['python_before_ns'] for r in rec['rows']]
        cases.append({'pair':rec['case']['pair'],'arm':rec['case']['arm'],'post_native_median_ns':statistics.median(posts),'x_internal_median_ns':statistics.median(xs),'total_median_ns':statistics.median(total)})
    pairs=[]; passed=0
    for i in range(PAIRS):
        b=next(x for x in cases if x['pair']==i and x['arm']=='gil5ms'); c=next(x for x in cases if x['pair']==i and x['arm']=='gil1ms')
        ratio=c['post_native_median_ns']/max(b['post_native_median_ns'],1)
        ok=c['post_native_median_ns']<=2_000_000 and ratio<=0.40
        passed+=ok; pairs.append({'pair':i,'baseline_post_native_median_ns':b['post_native_median_ns'],'candidate_post_native_median_ns':c['post_native_median_ns'],'ratio':ratio,'passes_pair_gate':bool(ok)})
    decision='GIL_INTERVAL_TRACKING_SCOPED' if passed>=4 else 'HOLD_GIL_INTERVAL_ATTRIBUTION'
    return {'case_summaries':cases,'pairs':pairs,'pairs_passing':passed,'decision':decision}

def construction(lib,h,cs):
    buf=ctypes.create_string_buffer(4096); tr=(ctypes.c_uint64*6)(); rows=[]
    for n in (0,1,511,512,513,1023,1024):
        assert lib.q_paint(h,n)==0; before=time.monotonic_ns(); assert lib.q_read(h,buf,4096,tr)==0; after=time.monotonic_ns()
        raw=buf.raw; count=sum(raw[j:j+3]==b'\x32\x32\xdc' for j in range(0,4096,4)); assert count==n and before<=tr[0]<=tr[1]<=tr[2]<=tr[3]<=after
        rows.append({'expected':n,'count':count,'digest':hashlib.sha256(raw).hexdigest()})
    pre=[]
    for arm in ARMS:
        rec=run_case(lib,h,{'pair':-1,'arm':arm,'count':512,'order':len(pre)},cs,4); pre.append(rec)
    return {'static':rows,'preflight_cases':len(pre),'preflight_integrity':all(r['load']['cleaned'] and len(r['rows'])==4 for r in pre)}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=('construction','formal'));ap.add_argument('--out',required=True);args=ap.parse_args()
    out=Path(args.out).resolve();out.mkdir(parents=True,exist_ok=False);cs=cpus(); plan=json.loads((HERE/'prereg.json').read_text()) if (HERE/'prereg.json').exists() else None
    if args.mode=='formal':
        if sources()!=plan['sources'] or sha(HERE/'native.so')!=plan['binary_sha256'] or cs!=plan['cpus'] or schedule()!=plan['schedule']: raise RuntimeError('frozen provenance mismatch')
        with (HERE/'CONSUMED').open('x') as f:f.write(TASK+'\n')
    result={'task':TASK,'mode':args.mode,'base':BASE,'sources':sources(),'binary_sha256':sha(HERE/'native.so'),'records':[],'errors':[],'environment':{'python':sys.version,'platform':platform.platform(),'gil_enabled':sys._is_gil_enabled(),'initial_switch_interval':sys.getswitchinterval(),'cpus':cs,'scheduler':os.sched_getscheduler(0)}}
    server=None;h=None;log=None
    try:
        r,w=os.pipe();log=(out/'xvfb.log').open('w');server=subprocess.Popen(['taskset','-c',str(cs['server']),'Xvfb','-displayfd',str(w),'-screen','0','160x120x24','-nolisten','tcp','-ac'],pass_fds=(w,),stdout=log,stderr=log);os.close(w)
        if not select.select([r],[],[],5)[0]:raise RuntimeError('Xvfb startup timeout')
        name=':'+os.read(r,64).decode().strip();os.close(r);os.sched_setaffinity(0,{cs['observer']});lib=library();h=lib.q_open(name.encode());
        if not h: raise RuntimeError('display unavailable')
        result['server']={'display':name,'affinity':sorted(os.sched_getaffinity(server.pid))}
        if args.mode=='construction': result['construction']=construction(lib,h,cs)
        else:
            for case in schedule():
                rec=run_case(lib,h,case,cs,N);result['records'].append(rec);dump(out/'raw.json',result)
            result['summary']=summary(result['records'])
    except BaseException: result['errors'].append(traceback.format_exc()); raise
    finally:
        if h:lib.q_close(h)
        if server:
            server.terminate();
            try:server.wait(timeout=3)
            except subprocess.TimeoutExpired:server.kill();server.wait()
            result.setdefault('server',{}).update(exitcode=server.returncode,reaped=True)
        os.sched_setaffinity(0,set(cs['allowed']));dump(out/'raw.json',result);(out/'raw.json.xz').write_bytes(lzma.compress((out/'raw.json').read_bytes(),preset=9))
        if log:log.close()
    if args.mode=='formal': print(json.dumps(result['summary'],indent=2))
if __name__=='__main__':main()
