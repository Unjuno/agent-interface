#!/usr/bin/env python3
from __future__ import annotations
import argparse, base64, ctypes, hashlib, json, os, pathlib, platform, subprocess, sys, threading, time, zlib
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parent
NATIVE = ROOT / "native.so"
SWITCH_S = 0.005
CADENCE_NS = 2_000_000
WINDOW_NS = 120_000_000
PULSE_NS = 5_000_000
TARGET = 1024
ARMS = ("INLINE_IDLE", "INLINE_THREAD", "PROCESS_IDLE", "PROCESS_THREAD")
OFFSETS_MS = (50, 52, 54, 56, 58, 50, 52, 54, 56, 58)


def jdump(v: Any) -> str:
    return json.dumps(v, sort_keys=True, separators=(",", ":"), allow_nan=False)


def sha256(path: pathlib.Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1<<20), b''): h.update(b)
    return h.hexdigest()


def load_native():
    lib=ctypes.CDLL(str(NATIVE))
    lib.q_init.restype=ctypes.c_int
    lib.q_open.argtypes=[ctypes.c_char_p]; lib.q_open.restype=ctypes.c_void_p
    lib.q_close.argtypes=[ctypes.c_void_p]
    lib.q_read.argtypes=[ctypes.c_void_p,ctypes.POINTER(ctypes.c_ubyte),ctypes.c_size_t,ctypes.POINTER(ctypes.c_uint64)]
    lib.q_read.restype=ctypes.c_int
    lib.q_paint.argtypes=[ctypes.c_void_p,ctypes.c_int]; lib.q_paint.restype=ctypes.c_int
    lib.q_pause.argtypes=[ctypes.POINTER(ctypes.c_uint64)]; lib.q_pause.restype=ctypes.c_int
    lib.q_init()
    return lib


def open_display(lib, display: str):
    d=lib.q_open(display.encode())
    if not d: raise RuntimeError(f"XOpenDisplay failed {display}")
    return d


def count_target(raw: bytes) -> int:
    if len(raw)!=4096: raise ValueError("roi length")
    return sum(1 for i in range(0,4096,4) if (int.from_bytes(raw[i:i+4],'little') & 0xffffff)==0xdc3232)


def compress_roi(raw: bytes) -> str:
    return base64.b64encode(zlib.compress(raw,9)).decode('ascii')


def capture(lib,d,case,due,seq):
    buf=(ctypes.c_ubyte*4096)(); t=(ctypes.c_uint64*6)()
    before=time.monotonic_ns(); rc=lib.q_read(d,buf,4096,t); returned=time.monotonic_ns()
    if rc!=0: raise RuntimeError(f"q_read {rc}")
    raw=bytes(buf)
    rec={"kind":"sample","case":case,"seq":seq,"due_ns":due,"py_before_ns":before,
         "c_ns":[int(x) for x in t],"py_return_ns":returned,
         "target_pixels":count_target(raw),"roi_zlib_b64":compress_roi(raw)}
    wire=(jdump(rec)+"\n").encode()
    return rec,wire


def sleep_until(target_ns:int):
    while True:
        now=time.monotonic_ns(); remain=target_ns-now
        if remain<=0:return
        if remain>800_000: time.sleep((remain-400_000)/1e9)
        else:
            while time.monotonic_ns()<target_ns: pass
            return


def sample_loop(lib,d,case,epoch_ns,emit):
    seq=0; skipped=0; last_due=epoch_ns; end=epoch_ns+WINDOW_NS
    while True:
        due=epoch_ns+seq*CADENCE_NS
        if due>=end: break
        now=time.monotonic_ns()
        if now>=due+CADENCE_NS:
            miss=(now-due)//CADENCE_NS
            skipped+=int(miss); seq+=int(miss); continue
        sleep_until(due)
        rec,wire=capture(lib,d,case,due,seq)
        emit(rec,wire)
        last_due=due; seq+=1
    return {"scheduled_slots":WINDOW_NS//CADENCE_NS,"emitted":seq-skipped,"skipped":skipped,"last_due_ns":last_due}


def set_aff(cpu:int):
    os.sched_setaffinity(0,{cpu})
    return sorted(os.sched_getaffinity(0))


def load_worker(ready:threading.Event, stop:threading.Event, out:dict):
    out["tid"]=threading.get_native_id(); out["affinity"]=set_aff(1); out["start_ns"]=time.monotonic_ns(); out["cpu_start_ns"]=time.thread_time_ns(); ready.set()
    x=0x12345678; loops=0
    while not stop.is_set():
        for _ in range(20000): x=((x*1664525+1013904223)&0xffffffff) ^ (x>>7)
        loops+=1
    out["cpu_end_ns"]=time.thread_time_ns(); out["end_ns"]=time.monotonic_ns(); out["loops"]=loops; out["checksum"]=x; out["final_affinity"]=sorted(os.sched_getaffinity(0))


def start_load(enabled:bool):
    if not enabled: return None,None,None
    ready=threading.Event(); stop=threading.Event(); out={}; t=threading.Thread(target=load_worker,args=(ready,stop,out),daemon=True); t.start()
    if not ready.wait(2): raise RuntimeError("load not ready")
    return t,stop,out


def stop_load(t,stop,out):
    if t is None:return None
    stop.set(); t.join(2)
    if t.is_alive(): raise RuntimeError("load join")
    return out


def child_ready(proc,kind):
    line=proc.stdout.readline()
    if not line: raise RuntimeError(f"{kind} no ready")
    row=json.loads(line)
    if row.get('kind')!='ready': raise RuntimeError(f"{kind} bad ready {row}")
    return row,line.decode()


def send_start(proc,payload):
    proc.stdin.write((jdump(payload)+"\n").encode()); proc.stdin.flush(); proc.stdin.close()


def run_case(spec, display:str):
    sys.setswitchinterval(SWITCH_S); set_aff(0)
    loaded=spec['arm'].endswith('THREAD')
    process=spec['arm'].startswith('PROCESS')
    fixture=subprocess.Popen([sys.executable,'-B',str(ROOT/'study.py'),'fixture','--display',display],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    f_ready,f_ready_wire=child_ready(fixture,'fixture')
    observer=None; o_ready=None; o_ready_wire=None
    if process:
        observer=subprocess.Popen([sys.executable,'-B',str(ROOT/'study.py'),'observer','--display',display],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        o_ready,o_ready_wire=child_ready(observer,'observer')
    lt,ls,lo=start_load(loaded)
    epoch=time.monotonic_ns()+25_000_000
    start={"case":spec['case'],"epoch_ns":epoch,"offset_ns":spec['offset_ms']*1_000_000,"pulse_ns":PULSE_NS}
    send_start(fixture,start)
    records=[]; wires=[]; received=[]; loop_info=None
    if process:
        send_start(observer,{"case":spec['case'],"epoch_ns":epoch})
        while True:
            line=observer.stdout.readline()
            if not line: raise RuntimeError("observer EOF before done")
            rcv=time.monotonic_ns(); row=json.loads(line)
            if row.get('kind')=='done': loop_info=row; break
            if row.get('kind')!='sample': raise RuntimeError(f"observer row {row}")
            row['received_ns']=rcv; records.append(row); received.append(rcv); wires.append(line.decode())
        oerr=observer.stderr.read().decode(); observer.wait(timeout=3); oexit=observer.returncode
    else:
        lib=load_native(); d=open_display(lib,display)
        def emit(rec,wire):
            rcv=time.monotonic_ns(); row=json.loads(wire); row['received_ns']=rcv; records.append(row); received.append(rcv); wires.append(wire.decode())
        loop_info=sample_loop(lib,d,spec['case'],epoch,emit); lib.q_close(d); oerr=""; oexit=None
    fline=fixture.stdout.readline(); ferr=fixture.stderr.read().decode(); fixture.wait(timeout=3); fexit=fixture.returncode
    if not fline: raise RuntimeError("fixture missing result")
    fixture_result=json.loads(fline)
    load_result=stop_load(lt,ls,lo)
    lib=load_native(); d=open_display(lib,display); final,_=capture(lib,d,spec['case'],time.monotonic_ns(),-1); lib.q_close(d)
    targets=[r for r in records if r['target_pixels']==TARGET]
    return {"case":spec['case'],"block":spec['block'],"arm":spec['arm'],"offset_ms":spec['offset_ms'],"epoch_ns":epoch,
            "consumer":{"pid":os.getpid(),"tid":threading.get_native_id(),"affinity":sorted(os.sched_getaffinity(0)),"switch_s":sys.getswitchinterval()},
            "load":load_result,"fixture_ready":f_ready,"fixture_ready_wire":f_ready_wire,"fixture":fixture_result,"fixture_exit":fexit,"fixture_stderr":ferr,
            "observer_ready":o_ready,"observer_ready_wire":o_ready_wire,"observer_exit":oexit,"observer_stderr":oerr,"loop":loop_info,
            "records":records,"wires":wires,"capture_count":len(targets),
            "age_qualified_count":sum(1 for r in targets if r['received_ns']-r['c_ns'][1] <= 5_000_000),
            "target_ages_ns":[r['received_ns']-r['c_ns'][1] for r in targets],"final":final}


def plan_cases():
    cases=[]
    for b,off in enumerate(OFFSETS_MS):
        order=list(ARMS[b%4:]+ARMS[:b%4])
        if b>=5: order=list(reversed(order))
        for j,arm in enumerate(order): cases.append({"case":f"b{b:02d}-{j}-{arm}","block":b,"arm":arm,"offset_ms":off})
    return cases


def start_xvfb(display:str):
    num=int(display[1:]); sock=pathlib.Path(f"/tmp/.X11-unix/X{num}")
    if sock.exists(): raise RuntimeError("display socket already exists")
    proc=subprocess.Popen(['taskset','-c','2','/usr/bin/Xvfb',display,'-screen','0','320x240x24','-nolisten','tcp','-noreset'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    deadline=time.monotonic()+3
    while time.monotonic()<deadline:
        if sock.exists(): return proc,sock
        if proc.poll() is not None: raise RuntimeError(proc.stderr.read().decode())
        time.sleep(.01)
    proc.terminate(); raise RuntimeError("Xvfb startup timeout")


def stop_xvfb(proc,sock):
    proc.terminate()
    try: proc.wait(3)
    except subprocess.TimeoutExpired: proc.kill(); proc.wait(2)
    out=proc.stdout.read().decode(); err=proc.stderr.read().decode()
    deadline=time.monotonic()+1
    while sock.exists() and time.monotonic()<deadline: time.sleep(.01)
    return {"exit":proc.returncode,"stdout":out,"stderr":err,"socket_absent":not sock.exists()}


def cmd_fixture(args):
    set_aff(3); lib=load_native(); d=open_display(lib,args.display)
    print(jdump({"kind":"ready","pid":os.getpid(),"tid":threading.get_native_id(),"affinity":sorted(os.sched_getaffinity(0))}),flush=True)
    spec=json.loads(sys.stdin.buffer.readline()); draw_due=spec['epoch_ns']+spec['offset_ns']; sleep_until(draw_due)
    draw_req=time.monotonic_ns(); rc1=lib.q_paint(d,TARGET); draw_done=time.monotonic_ns(); clear_due=draw_done+spec['pulse_ns']; sleep_until(clear_due)
    clear_req=time.monotonic_ns(); rc2=lib.q_paint(d,0); clear_done=time.monotonic_ns(); lib.q_close(d)
    print(jdump({"kind":"fixture_done","pid":os.getpid(),"affinity":sorted(os.sched_getaffinity(0)),"draw_due_ns":draw_due,"draw_request_ns":draw_req,"draw_complete_ns":draw_done,"clear_due_ns":clear_due,"clear_request_ns":clear_req,"clear_complete_ns":clear_done,"draw_rc":rc1,"clear_rc":rc2}),flush=True)


def cmd_observer(args):
    sys.setswitchinterval(SWITCH_S); set_aff(0); lib=load_native(); d=open_display(lib,args.display)
    print(jdump({"kind":"ready","pid":os.getpid(),"tid":threading.get_native_id(),"affinity":sorted(os.sched_getaffinity(0)),"switch_s":sys.getswitchinterval()}),flush=True)
    spec=json.loads(sys.stdin.buffer.readline())
    def emit(rec,wire): sys.stdout.buffer.write(wire); sys.stdout.buffer.flush()
    info=sample_loop(lib,d,spec['case'],spec['epoch_ns'],emit); lib.q_close(d)
    print(jdump({"kind":"done","pid":os.getpid(),"affinity":sorted(os.sched_getaffinity(0)),**info}),flush=True)


def environment():
    def file_hash(p):
        p=pathlib.Path(p); return sha256(p) if p.exists() else None
    return {"python":sys.version,"platform":platform.platform(),"switch_s":SWITCH_S,"eligible_affinity":sorted(os.sched_getaffinity(0)),
            "cpu_max":pathlib.Path('/sys/fs/cgroup/cpu.max').read_text().strip() if pathlib.Path('/sys/fs/cgroup/cpu.max').exists() else None,
            "memory_max":pathlib.Path('/sys/fs/cgroup/memory.max').read_text().strip() if pathlib.Path('/sys/fs/cgroup/memory.max').exists() else None,
            "binary_hashes":{"python":file_hash(sys.executable),"Xvfb":file_hash('/usr/bin/Xvfb'),"libX11":file_hash('/lib/x86_64-linux-gnu/libX11.so.6')},
            "native_sha256":sha256(NATIVE)}


def cmd_construction(args):
    out=pathlib.Path(args.out); out.mkdir(parents=True,exist_ok=False); display=':239'; xvfb,sock=start_xvfb(display)
    try:
        lib=load_native(); d=open_display(lib,display); rows=[]
        for n in (0,511,512,1024):
            if lib.q_paint(d,n)!=0: raise RuntimeError('paint')
            rec,_=capture(lib,d,'construction',time.monotonic_ns(),n); rows.append({"expected":n,"actual":rec['target_pixels'],"sample":rec})
        t=(ctypes.c_uint64*2)(); py0=time.monotonic_ns(); rc=lib.q_pause(t); py1=time.monotonic_ns(); lib.q_paint(d,0); lib.q_close(d)
        if rc or not(py0<=t[0]<=t[1]<=py1): raise RuntimeError('clock enclosure')
        # Static pipe path: six clear samples, no pulse.
        obs=subprocess.Popen([sys.executable,'-B',str(ROOT/'study.py'),'observer','--display',display],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        ready,_=child_ready(obs,'observer'); epoch=time.monotonic_ns()+15_000_000; send_start(obs,{"case":"construction-static","epoch_ns":epoch})
        static=[]
        while True:
            line=obs.stdout.readline(); rcv=time.monotonic_ns(); row=json.loads(line)
            if row.get('kind')=='done': done=row; break
            row['received_ns']=rcv; static.append(row)
        obs_err=obs.stderr.read().decode(); obs.wait(3)
        # GIL load exposure, no pulse comparison.
        set_aff(0); lt,ls,lo=start_load(True); time.sleep(.035); lr=stop_load(lt,ls,lo)
        result={"status":"PASS_STATIC_CONSTRUCTION","short_pulse_cases":0,"static_counts":rows,"clock":{"py_before_ns":py0,"c_ns":[int(x) for x in t],"py_after_ns":py1},
                "static_pipe":{"ready":ready,"records":static,"done":done,"exit":obs.returncode,"stderr":obs_err},"load":lr,"environment":environment()}
    finally:
        xstop=stop_xvfb(xvfb,sock)
    result['xvfb']=xstop
    (out/'construction.json').write_text(json.dumps(result,sort_keys=True,indent=2),encoding='utf-8')
    if any(r['actual']!=r['expected'] for r in rows) or obs.returncode!=0 or any(r['target_pixels']!=0 for r in static) or lr['cpu_end_ns']<=lr['cpu_start_ns'] or not xstop['socket_absent']:
        raise SystemExit(2)
    print(jdump({"status":result['status'],"out":str(out)}))


def cmd_formal(args):
    freeze=json.loads((ROOT/'FREEZE.json').read_text())
    for name,row in freeze['files'].items():
        p=ROOT/name
        if not p.exists() or sha256(p)!=row['sha256']: raise SystemExit(f"source mismatch {name}")
    out=pathlib.Path(args.out); out.mkdir(parents=True,exist_ok=False); (out/'STARTED').write_text(str(time.monotonic_ns()))
    display=':240'; xvfb,sock=start_xvfb(display); cases=[]
    try:
        lib=load_native(); d=open_display(lib,display); lib.q_paint(d,0); lib.q_close(d)
        for spec in freeze['plan']['cases']:
            cases.append(run_case(spec,display))
    finally:
        xstop=stop_xvfb(xvfb,sock)
    raw={"schema":"observer-ipc-freshness-v2","allocation":freeze['allocation'],"freeze_sha256":sha256(ROOT/'FREEZE.json'),"environment":environment(),"cases":cases,"xvfb":xstop,"completed_ns":time.monotonic_ns()}
    (out/'RAW.json').write_text(json.dumps(raw,sort_keys=True,separators=(',',':')),encoding='utf-8')
    (out/'END.json').write_text(json.dumps({"cases":len(cases),"xvfb":xstop,"completed_ns":raw['completed_ns']},sort_keys=True,indent=2),encoding='utf-8')
    print(jdump({"cases":len(cases),"raw_sha256":sha256(out/'RAW.json'),"xvfb":xstop}))


def main():
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest='cmd',required=True)
    p=sub.add_parser('fixture');p.add_argument('--display',required=True)
    p=sub.add_parser('observer');p.add_argument('--display',required=True)
    p=sub.add_parser('construction');p.add_argument('--out',required=True)
    p=sub.add_parser('formal');p.add_argument('--out',required=True)
    args=ap.parse_args()
    {'fixture':cmd_fixture,'observer':cmd_observer,'construction':cmd_construction,'formal':cmd_formal}[args.cmd](args)
if __name__=='__main__': main()
