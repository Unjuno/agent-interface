from __future__ import annotations
import argparse,collections,json,math,os,platform,subprocess,time
from pathlib import Path
from Xlib import X,display
W=320;H=240;ROI=(80,60,160,120);PERIOD_NS=50_000_000;RING_AGE_NS=500_000_000;EXPECTED_FRAME_BYTES=76_800
HISTORY_OFFSETS_NS=[-150_000_000,-50_000_000]

def normalize_image_data(raw):
    if isinstance(raw,bytes): data=raw
    elif isinstance(raw,(bytearray,memoryview)): data=bytes(raw)
    elif isinstance(raw,str):
        try:data=raw.encode('latin-1')
        except UnicodeEncodeError as exc: raise ValueError('non-latin1 image payload') from exc
    else: raise TypeError('unsupported image payload type: '+type(raw).__name__)
    if len(data)!=EXPECTED_FRAME_BYTES: raise ValueError(f'roi payload length {len(data)} != {EXPECTED_FRAME_BYTES}')
    return data

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

def capture(rwin):
    started=time.perf_counter_ns();img=rwin.get_image(*ROI,X.ZPixmap,0xffffffff);raw=img.data
    data=normalize_image_data(raw);finished=time.perf_counter_ns()
    return {'capture_ns':finished,'started_ns':started,'latency_ns':finished-started,'data':data,'payload_type':type(raw).__name__}

def nearest(ring,target_ns): return min(ring,key=lambda x:abs(x['capture_ns']-target_ns))

def one_arm(root,display_num,arm,request_offsets_ns):
    ddir=root/f'd{display_num}_{arm}';ddir.mkdir(parents=True,exist_ok=True)
    ready=ddir/'ready';startf=ddir/'start';stopf=ddir/'stop';fout=ddir/'fixture.json'
    env=os.environ.copy();env['DISPLAY']=f':{display_num}';env['XAUTHORITY']=str(ddir/'xauth');(ddir/'xauth').touch()
    xv=subprocess.Popen(['Xvfb',f':{display_num}','-screen','0',f'{W}x{H}x24','-nolisten','tcp','-ac'],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,env=env)
    try:
        wait_file(Path(f'/tmp/.X11-unix/X{display_num}'))
        fix=subprocess.Popen(['python',str(root/'fixture.py'),'--ready',str(ready),'--start',str(startf),'--stop',str(stopf),'--out',str(fout)],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        try:
            wait_file(ready)
            oldD=os.environ.get('DISPLAY');oldA=os.environ.get('XAUTHORITY');os.environ['DISPLAY']=env['DISPLAY'];os.environ['XAUTHORITY']=env['XAUTHORITY']
            d=display.Display(env['DISPLAY']);rwin=d.screen().root
            start=time.perf_counter_ns();startf.write_text(str(start));end=start+1_500_000_000
            trials=[];exceptions=[];payload_types={};caps=[];ring=collections.deque();max_ring_bytes=0
            if arm=='ring':
                nxt=start;reqi=0
                while time.perf_counter_ns()<end:
                    next_req=start+request_offsets_ns[reqi] if reqi<len(request_offsets_ns) else end+1
                    now=time.perf_counter_ns();event_ns=min(nxt,next_req,end)
                    if now<event_ns:time.sleep((event_ns-now)/1e9)
                    now=time.perf_counter_ns()
                    if nxt<=next_req and nxt<end and now+500_000>=nxt:
                        try:
                            fr=capture(rwin);payload_types[fr['payload_type']]=payload_types.get(fr['payload_type'],0)+1
                            caps.append(fr['latency_ns']);ring.append(fr)
                            while ring and fr['capture_ns']-ring[0]['capture_ns']>RING_AGE_NS:ring.popleft()
                            max_ring_bytes=max(max_ring_bytes,len(ring)*EXPECTED_FRAME_BYTES)
                        except Exception as exc:
                            exceptions.append(repr(exc));break
                        nxt+=PERIOD_NS;continue
                    if reqi<len(request_offsets_ns) and now>=next_req:
                        request_ns=time.perf_counter_ns();targets=[request_ns+x for x in HISTORY_OFFSETS_NS]
                        q0=time.perf_counter_ns()
                        if len(ring)<2: raise RuntimeError('insufficient retained history')
                        selected=[nearest(ring,t) for t in targets];q1=time.perf_counter_ns()
                        trials.append({'request_index':reqi,'request_ns':request_ns,'query_latency_ns':q1-q0,'target_ns':targets,
                          'selected_capture_ns':[x['capture_ns'] for x in selected],'target_error_ns':[abs(x['capture_ns']-t) for x,t in zip(selected,targets)],
                          'distinct_frames':selected[0]['capture_ns']!=selected[1]['capture_ns'],'both_before_request':all(x['capture_ns']<request_ns for x in selected),
                          'exact_requested_past_available':True,'evidence_role':'historical','extra_acquisition_boundaries':0})
                        reqi+=1;continue
                if len(trials)!=4: raise RuntimeError(f'ring trials {len(trials)} != 4')
            elif arm=='jit':
                for reqi,off in enumerate(request_offsets_ns):
                    due=start+off;now=time.perf_counter_ns()
                    if now<due:time.sleep((due-now)/1e9)
                    request_ns=time.perf_counter_ns()
                    try:
                        first=capture(rwin);payload_types[first['payload_type']]=payload_types.get(first['payload_type'],0)+1;caps.append(first['latency_ns'])
                        target2=request_ns+100_000_000;now=time.perf_counter_ns()
                        if now<target2:time.sleep((target2-now)/1e9)
                        second=capture(rwin);payload_types[second['payload_type']]=payload_types.get(second['payload_type'],0)+1;caps.append(second['latency_ns'])
                    except Exception as exc:
                        exceptions.append(repr(exc));break
                    done=time.perf_counter_ns()
                    trials.append({'request_index':reqi,'request_ns':request_ns,'evidence_latency_ns':done-request_ns,
                      'current_capture_ns':first['capture_ns'],'future_capture_ns':second['capture_ns'],'future_delay_ns':second['capture_ns']-request_ns,
                      'exact_requested_past_available':False,'evidence_role':'future_equivalent','extra_acquisition_boundaries':1,'promoted_future_as_history':False})
                if len(trials)!=4: raise RuntimeError(f'jit trials {len(trials)} != 4')
                now=time.perf_counter_ns()
                if now<end:time.sleep((end-now)/1e9)
            else: raise ValueError(arm)
            d.sync();d.close()
            if oldD is None:os.environ.pop('DISPLAY',None)
            else:os.environ['DISPLAY']=oldD
            if oldA is None:os.environ.pop('XAUTHORITY',None)
            else:os.environ['XAUTHORITY']=oldA
            stop=time.perf_counter_ns();stopf.write_text(str(stop));wait_file(fout);fix.wait(timeout=2);fj=json.loads(fout.read_text())
            return {'arm':arm,'display':display_num,'trials':trials,'capture_count':len(caps),'capture_exceptions':exceptions,
              'capture_latency_ns':{'p50':pct(caps,.5),'p95':pct(caps,.95),'max':max(caps) if caps else None},'capture_payload_types':payload_types,
              'frame_bytes':EXPECTED_FRAME_BYTES,'max_ring_bytes':max_ring_bytes,'capture_region':list(ROI),'fixture_geometry':fj['geometry'],'fixture_count':len(fj['times_ns'])}
        finally:
            if fix.poll() is None:fix.kill();fix.wait()
    finally:
        if xv.poll() is None:xv.terminate()
        try:xv.wait(timeout=.25)
        except Exception:xv.kill();xv.wait()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);a=ap.parse_args();root=Path(__file__).parent;out=Path(a.out)
    if out.exists():raise SystemExit('formal result exists')
    schedule=json.loads((root/'schedule.json').read_text());pairs=[]
    for p in schedule['pairs']:
        pair=[]
        for j,arm in enumerate(p['order']):pair.append(one_arm(root,620+(p['pair']-1)*2+j,arm,[x*1_000_000 for x in p['request_offsets_ms']]))
        pairs.append({'pair':p['pair'],'arms':pair})
    result={'formal':True,'formal_invocations':1,'reruns':0,'pairs':pairs,'platform':platform.platform(),'python':platform.python_version(),'grants_input_authority':False,'task':schedule['task']}
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,sort_keys=True))
if __name__=='__main__':main()
