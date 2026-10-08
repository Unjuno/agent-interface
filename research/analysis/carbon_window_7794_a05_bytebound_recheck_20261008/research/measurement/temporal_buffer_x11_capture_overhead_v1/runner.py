from __future__ import annotations
import argparse,collections,json,math,os,platform,resource,statistics,subprocess,tempfile,time
from pathlib import Path
from Xlib import X, display
W=320; H=240; PERIOD_NS=50_000_000; RING_AGE_NS=500_000_000

def pct(xs,p):
    if not xs:return None
    ys=sorted(xs); k=(len(ys)-1)*p; lo=math.floor(k); hi=math.ceil(k)
    return ys[lo] if lo==hi else ys[lo]*(hi-k)+ys[hi]*(k-lo)

def wait_file(p,timeout=3):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        if p.exists(): return
        time.sleep(.01)
    raise RuntimeError(f'timeout {p}')

def one_arm(root,display_num,arm,warmup_s,measure_s):
    ddir=root/f'd{display_num}_{arm}'; ddir.mkdir(parents=True,exist_ok=True)
    ready=ddir/'ready'; startf=ddir/'start'; stopf=ddir/'stop'; out=ddir/'fixture.json'
    env=os.environ.copy(); env['DISPLAY']=f':{display_num}'; env['XAUTHORITY']=str(ddir/'xauth'); (ddir/'xauth').touch()
    xv=subprocess.Popen(['Xvfb',f':{display_num}','-screen','0',f'{W}x{H}x24','-nolisten','tcp','-ac'],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,env=env)
    try:
        sock=Path(f'/tmp/.X11-unix/X{display_num}'); wait_file(sock)
        fix=subprocess.Popen(['python',str(root/'fixture.py'),'--ready',str(ready),'--start',str(startf),'--stop',str(stopf),'--out',str(out)],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        try:
            wait_file(ready); time.sleep(warmup_s)
            old_display=os.environ.get('DISPLAY'); old_xauth=os.environ.get('XAUTHORITY')
            os.environ['DISPLAY']=env['DISPLAY']; os.environ['XAUTHORITY']=env['XAUTHORITY']
            d=display.Display(env['DISPLAY']) if arm=='capture' else None
            rwin=d.screen().root if d else None
            start=time.perf_counter_ns(); startf.write_text(str(start)); end=start+int(measure_s*1e9)
            cpu0=time.process_time_ns(); caps=[]; dropped=0; ring=collections.deque(); ring_bytes=0; max_ring=0; frame_bytes=None; exceptions=[]
            if arm=='capture':
                nxt=start
                while True:
                    now=time.perf_counter_ns()
                    if now>=end: break
                    if now<nxt: time.sleep((nxt-now)/1e9)
                    before=time.perf_counter_ns()
                    late=before-nxt
                    if late>=PERIOD_NS:
                        miss=late//PERIOD_NS; dropped+=int(miss); nxt+=int(miss)*PERIOD_NS
                    try:
                        img=rwin.get_image(0,0,W,H,X.ZPixmap,0xffffffff); data=bytes(img.data)
                    except Exception as e:
                        exceptions.append(repr(e)); break
                    after=time.perf_counter_ns(); caps.append(after-before); frame_bytes=len(data) if frame_bytes is None else frame_bytes
                    ring.append((after,data)); ring_bytes+=len(data)
                    while ring and after-ring[0][0]>RING_AGE_NS:
                        ring_bytes-=len(ring.popleft()[1])
                    max_ring=max(max_ring,ring_bytes); nxt+=PERIOD_NS
                d.sync(); d.close()
            else:
                while time.perf_counter_ns()<end: time.sleep(.01)
            if old_display is None: os.environ.pop('DISPLAY',None)
            else: os.environ['DISPLAY']=old_display
            if old_xauth is None: os.environ.pop('XAUTHORITY',None)
            else: os.environ['XAUTHORITY']=old_xauth
            cpu=time.process_time_ns()-cpu0; stop=time.perf_counter_ns(); stopf.write_text(str(stop)); wait_file(out); fix.wait(timeout=2)
            fj=json.loads(out.read_text()); ts=fj['times_ns']; gaps=[b-a for a,b in zip(ts,ts[1:])]
            return {'arm':arm,'display':display_num,'measure_wall_ns':stop-start,'process_cpu_ns':cpu,'cpu_fraction':cpu/max(1,stop-start),
                    'capture_count':len(caps),'capture_dropped_slots':dropped,'capture_exceptions':exceptions,'capture_latency_ns':{'p50':pct(caps,.5),'p95':pct(caps,.95),'max':max(caps) if caps else None},
                    'frame_bytes':frame_bytes,'max_ring_bytes':max_ring,'fixture_count':len(ts),'fixture_gap_ns':{'p50':pct(gaps,.5),'p95':pct(gaps,.95),'max':max(gaps) if gaps else None},
                    'fixture_geometry':fj['geometry'],'max_rss_kb':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
        finally:
            if fix.poll() is None: fix.kill(); fix.wait()
    finally:
        if xv.poll() is None: xv.terminate();
        try: xv.wait(timeout=2)
        except: xv.kill(); xv.wait()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--construction',action='store_true'); ap.add_argument('--out'); args=ap.parse_args(); root=Path(__file__).parent
    if not args.construction and not args.out: raise SystemExit('formal --out required')
    if not args.construction and Path(args.out).exists(): raise SystemExit('formal result exists')
    pairs=1 if args.construction else 6; warm=.15 if args.construction else .3; dur=.7 if args.construction else 1.5; rows=[]
    base_display=170 if args.construction else 190
    for i in range(pairs):
        order=['baseline','capture'] if i%2==0 else ['capture','baseline']
        pair=[]
        for j,arm0 in enumerate(order):
            arm='capture' if arm0=='capture' else 'baseline'; pair.append(one_arm(root,base_display+i*2+j,arm,warm,dur))
        rows.append(pair)
    result={'construction':args.construction,'formal':not args.construction,'formal_invocations':0 if args.construction else 1,'reruns':0,'pairs':rows,'platform':platform.platform(),'python':platform.python_version(),'grants_input_authority':False,'task':'TEMPORAL-BUFFER-X11-CAPTURE-OVERHEAD-20260918-001'}
    if args.out: Path(args.out).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,indent=2,sort_keys=True))
if __name__=='__main__': main()
