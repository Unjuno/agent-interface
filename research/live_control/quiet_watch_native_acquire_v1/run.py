#!/usr/bin/env python3
"""Fixed-cadence acquisition comparison; exact #231 fixture, fresh allocation."""
import argparse, base64, ctypes, hashlib, importlib.util, json, os, platform
import random, subprocess, sys, threading, time, traceback, zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = '821d214b13500db52e6b34ff57b6ece59a76142f'
UPSTREAM = HERE.parent / 'quiet_watch_poll_period_v1/run_quiet_watch_poll_period_v1.py'
UPSTREAM_SHA = 'd50233d9584876f119e78251728ccbf682a4b46b5485197ae60229970d9d520d'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load():
    if digest(UPSTREAM) != UPSTREAM_SHA:
        raise RuntimeError('upstream source mismatch')
    spec = importlib.util.spec_from_file_location('q231', UPSTREAM)
    old = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(old)
    lib = ctypes.CDLL(str(HERE / 'native.so'))
    lib.q_init.restype = ctypes.c_int
    lib.q_open.argtypes = [ctypes.c_char_p]
    lib.q_open.restype = ctypes.c_void_p
    lib.q_close.argtypes = [ctypes.c_void_p]
    lib.q_close.restype = None
    lib.q_read.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t]
    lib.q_read.restype = ctypes.c_int
    if not lib.q_init():
        raise RuntimeError('XInitThreads failed')
    return old, lib

def schedule():
    pairs = [('target', o, r) for r in range(3) for o in (150,152,154,156,158)]
    pairs += [('nuisance', o, r) for r,o in enumerate((150,152,154,156))]
    rng = random.Random(23620260916)
    rng.shuffle(pairs)
    answer = []
    for i,(kind,offset,rep) in enumerate(pairs):
        # Balanced order within kind: target 8/7, nuisance 2/2.
        j = sum(c['kind'] == kind for c in answer) // 2
        arms = ('python','native') if j % 2 == 0 else ('native','python')
        for arm in arms:
            answer.append(dict(case_id=f'{kind}-o{offset}-r{rep}-{arm}',
                pair_id=f'{kind}-o{offset}-r{rep}', kind=kind, offset_ms=offset,
                period_ms=2, backend=arm, order=len(answer)))
    return answer

class Reader:
    def __init__(self, old, lib, name, arm):
        self.old, self.lib, self.arm = old, lib, arm
        self.handle = lib.q_open(name.encode())  # Same extra connection in both arms.
        if not self.handle:
            raise RuntimeError('native display unavailable')
        self.buf = ctypes.create_string_buffer(4096)
        self.samples = []

    def native(self):
        status = self.lib.q_read(self.handle, self.buf, 4096)
        if status:
            raise RuntimeError(f'native capture/ABI failure: {status}')
        return self.buf.raw

    def __call__(self, dpy, root):
        cpu0 = time.thread_time_ns()
        s = time.perf_counter_ns()
        if self.arm == 'native':
            raw = self.native()
        else:
            image = root.get_image(48,48,32,32,self.old.X.ZPixmap,0xffffffff)
            raw = image.data.encode('latin1') if isinstance(image.data,str) else bytes(image.data)
        e = time.perf_counter_ns()
        cpu1 = time.thread_time_ns()
        count = self.old.roi_match_count(raw)  # Byte-identical predicate, no optimization.
        end = time.perf_counter_ns()
        cpu2 = time.thread_time_ns()
        self.samples.append([s, e, cpu1-cpu0, end, cpu2-cpu0])
        return s,e,raw,count

    def close(self):
        self.lib.q_close(self.handle)
        self.handle = None

def environment():
    import importlib.metadata, Xlib
    return dict(platform=platform.platform(), python=sys.version,
        python_xlib=dict(module=str(Xlib.__file__),version=str(getattr(Xlib,'__version__','UNKNOWN')),distributions=importlib.metadata.packages_distributions().get('Xlib',[])),
        affinity=sorted(os.sched_getaffinity(0)), cpu_frequency_pinned=False,
        cpuinfo=Path('/proc/cpuinfo').read_text().split('\n\n')[0],
        clock={name:vars(time.get_clock_info(name)) for name in ('perf_counter','thread_time')},
        compiler=subprocess.check_output(['gcc','--version'],text=True).splitlines()[0],
        packages=subprocess.check_output(['dpkg-query','-W','libx11-6','xvfb','tk8.6'],text=True),
        binary_sha256=digest(HERE/'native.so'))

def static_checks(old, lib, name):
    root=old.tk.Tk(); root.geometry('640x400+0+0')
    cv=old.tk.Canvas(root,width=640,height=400,highlightthickness=0)
    cv.pack(); root.update()
    d=old.display.Display(name); r=Reader(old,lib,name,'native'); rows=[]
    try:
        for red_count in (0,1,511,512,513,1023,1024):
            colors=['#dc3232' if i<red_count else '#db3232' for i in range(1024)]
            image=old.tk.PhotoImage(width=32,height=32)
            image.put(' '.join('{'+' '.join(colors[i:i+32])+'}' for i in range(0,1024,32)))
            cv.delete('all'); cv.create_image(48,48,image=image,anchor='nw'); root.update()
            py=d.screen().root.get_image(48,48,32,32,old.X.ZPixmap,0xffffffff).data
            py=py.encode('latin1') if isinstance(py,str) else bytes(py)
            native=r.native()
            check=dict(target_pixels=red_count, bytes_equal=py==native,
                python_count=old.roi_match_count(py),native_count=old.roi_match_count(native),
                raw_b64=base64.b64encode(native).decode())
            rows.append(check)
            if not (check['bytes_equal'] and check['python_count']==red_count==check['native_count']):
                raise RuntimeError('static byte or predicate mismatch')
        assert lib.q_read(r.handle,r.buf,4095)==-1
        assert lib.q_read(None,r.buf,4096)==-1
    finally:
        r.close(); d.close(); root.destroy()
    return rows

def run_one(old,lib,name,case):
    reader=Reader(old,lib,name,case['backend'])
    original=old.acquire_roi
    exceptions=[]
    old_hook=threading.excepthook
    threading.excepthook=lambda x: exceptions.append(str(x.exc_value))
    old.acquire_roi=reader
    try:
        result=old.run_case(case,name)
        result['acquisition_metrics']=reader.samples[:-1]
        result['final_metrics']=reader.samples[-1]
        result['thread_errors']=exceptions
        return result
    finally:
        old.acquire_roi=original
        threading.excepthook=old_hook
        # Private-display emergency cleanup, outside all reported case endpoints.
        d=old.display.Display(name)
        old.xtest.fake_input(d,old.X.KeyRelease,d.keysym_to_keycode(old.XK.string_to_keysym('Right')))
        d.sync(); d.close(); reader.close()

def check_case(r):
    assert not r['thread_errors']
    assert not r['owner'].get('error') and not r['watcher'].get('error')
    assert r['owner']['verified_empty'] and not r['right_down_final']
    assert [e['kind'] for e in r['events']]==['app_key_press','app_key_release']
    assert r['final']['match_count']==0
    assert len(r['acquisition_metrics'])==len(r['acquisitions'])
    if r['case']['kind']=='nuisance':
        assert not r['derived']['detected']

def write(path,obj):
    path.write_text(json.dumps(obj,sort_keys=True,separators=(',',':'))+'\n')

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--mode',choices=['preflight','formal'],required=True)
    ap.add_argument('--display',default=':97')
    ap.add_argument('--out',required=True)
    args=ap.parse_args()
    out=Path(args.out)
    out.mkdir(parents=True,exist_ok=False)  # No overwrite or same-ID retry.
    old,lib=load()
    sources={p.name:digest(p) for p in (HERE/'run.py',HERE/'native.c',HERE/'audit.py',UPSTREAM)}
    payload=dict(schema='quiet_watch_native_acquire_v1',mode=args.mode,base=BASE,
        sources=sources,environment=environment(),records=[],errors=[])
    if args.mode=='formal':
        frozen=json.loads((HERE/'prereg.json').read_text())
        assert sources==frozen['sources']
        assert hashlib.sha256(json.dumps(schedule(),sort_keys=True).encode()).hexdigest()==frozen['schedule_sha256']
        assert payload['environment']['binary_sha256']==frozen['binary_sha256']
        payload['prereg_sha256']=digest(HERE/'prereg.json')
        cases=schedule()
    else:
        cases=[dict(case_id=f'preflight-{kind}-{arm}',pair_id=f'preflight-{kind}',
               kind=kind,offset_ms=150,period_ms=2,backend=arm,order=i)
               for i,(kind,arm) in enumerate([('target','python'),('target','native'),
                                            ('nuisance','native'),('nuisance','python')])]
    try:
        if args.mode=='preflight': payload['static']=static_checks(old,lib,args.display)
        for case in cases:
            r=run_one(old,lib,args.display,case)
            payload['records'].append(r)
            write(out/'raw.json',payload)
            check_case(r)
            print(case['case_id'],r['derived']['detected'],flush=True)
    except BaseException:
        payload['errors'].append(traceback.format_exc())
        raise
    finally:
        write(out/'raw.json',payload)
        (out/'raw.json.zlib').write_bytes(zlib.compress((out/'raw.json').read_bytes(),9))

if __name__=='__main__': main()
