from __future__ import annotations
import argparse,collections,json,math,os,platform,resource,subprocess,time
from pathlib import Path
from Xlib import X,display
W=320;H=240;PERIOD_NS=66_666_667;RING_AGE_NS=500_000_000

def pct(xs,p):
    if not xs:return None
    ys=sorted(xs);k=(len(ys)-1)*p;lo=math.floor(k);hi=math.ceil(k)
    return ys[lo] if lo==hi else ys[lo]*(hi-k)+ys[hi]*(k-lo)
def wait_file(p,timeout=3):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        if p.exists():return
        time.sleep(.01)
    raise RuntimeError(f'timeout {p}')
def one_arm(root,n,arm,warm,measure):
    dd=root/f'd{n}_{arm}';dd.mkdir(parents=True,exist_ok=True);ready=dd/'ready';startf=dd/'start';stopf=dd/'stop';out=dd/'fixture.json'
    env=os.environ.copy();env['DISPLAY']=f':{n}';env['XAUTHORITY']=str(dd/'xauth');(dd/'xauth').touch()
    xv=subprocess.Popen(['Xvfb',f':{n}','-screen','0',f'{W}x{H}x24','-nolisten','tcp','-ac'],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,env=env)
    try:
        wait_file(Path(f'/tmp/.X11-unix/X{n}'));fix=subprocess.Popen(['python',str(root/'fixture.py'),'--ready',str(ready),'--start',str(startf),'--stop',str(stopf),'--out',str(out)],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        try:
            wait_file(ready);time.sleep(warm);oldD=os.environ.get('DISPLAY');oldA=os.environ.get('XAUTHORITY');os.environ['DISPLAY']=env['DISPLAY'];os.environ['XAUTHORITY']=env['XAUTHORITY']
            d=display.Display(env['DISPLAY']) if arm=='capture' else None;r=d.screen().root if d else None
            start=time.perf_counter_ns();startf.write_text(str(start));end=start+int(measure*1e9);cpu0=time.process_time_ns();caps=[];dropped=0;ring=collections.deque();rb=0;maxrb=0;fb=None;exc=[]
            if arm=='capture':
                nxt=start
                while time.perf_counter_ns()<end:
                    now=time.perf_counter_ns()
                    if now<nxt:time.sleep((nxt-now)/1e9)
                    before=time.perf_counter_ns();late=before-nxt
                    if late>=PERIOD_NS:miss=late//PERIOD_NS;dropped+=int(miss);nxt+=int(miss)*PERIOD_NS
                    try:data=bytes(r.get_image(0,0,W,H,X.ZPixmap,0xffffffff).data)
                    except Exception as e:exc.append(repr(e));break
                    after=time.perf_counter_ns();caps.append(after-before);fb=len(data) if fb is None else fb;ring.append((after,data));rb+=len(data)
                    while ring and after-ring[0][0]>RING_AGE_NS:rb-=len(ring.popleft()[1])
                    maxrb=max(maxrb,rb);nxt+=PERIOD_NS
                d.sync();d.close()
            else:
                while time.perf_counter_ns()<end:time.sleep(.01)
            if oldD is None:os.environ.pop('DISPLAY',None)
            else:os.environ['DISPLAY']=oldD
            if oldA is None:os.environ.pop('XAUTHORITY',None)
            else:os.environ['XAUTHORITY']=oldA
            cpu=time.process_time_ns()-cpu0;stop=time.perf_counter_ns();stopf.write_text(str(stop));wait_file(out);fix.wait(timeout=2);fj=json.loads(out.read_text());ts=fj['times_ns'];g=[b-a for a,b in zip(ts,ts[1:])]
            return {'arm':arm,'display':n,'measure_wall_ns':stop-start,'process_cpu_ns':cpu,'cpu_fraction':cpu/max(1,stop-start),'capture_count':len(caps),'capture_dropped_slots':dropped,'capture_exceptions':exc,'capture_latency_ns':{'p50':pct(caps,.5),'p95':pct(caps,.95),'max':max(caps) if caps else None},'frame_bytes':fb,'max_ring_bytes':maxrb,'fixture_count':len(ts),'fixture_gap_ns':{'p50':pct(g,.5),'p95':pct(g,.95),'max':max(g) if g else None},'fixture_geometry':fj['geometry'],'max_rss_kb':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
        finally:
            if fix.poll() is None:fix.kill();fix.wait()
    finally:
        if xv.poll() is None:xv.terminate()
        try:xv.wait(timeout=.25)
        except: xv.kill();xv.wait()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);a=ap.parse_args();root=Path(__file__).parent;out=Path(a.out)
    if out.exists():raise SystemExit('formal result exists')
    rows=[]
    for i in range(6):
        order=['baseline','capture'] if i%2==0 else ['capture','baseline'];rows.append([one_arm(root,200+i*2+j,arm,.3,1.5) for j,arm in enumerate(order)])
    result={'formal':True,'formal_invocations':1,'reruns':0,'pairs':rows,'platform':platform.platform(),'python':platform.python_version(),'grants_input_authority':False,'task':'TEMPORAL-BUFFER-X11-CAPTURE-CADENCE-20260918-006'};out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
