"""Shared executor/backend integration checks in a private managed X11 surface."""
import argparse,hashlib,json,sys,time,threading,shutil
from pathlib import Path
from Xlib import X
from session_v9 import Backend,suite
from executor_v3 import Executor
from lease import Expired
HERE=Path(__file__).resolve().parent

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    sources=[HERE/n for n in ['session_v9.py','session_v8.py','session_v7.py','session_v6.py','session_v5.py','session_v4.py','input_owner_v5.py','executor_v3.py','lease.py']]+[Path(__file__).resolve()]
    (a.out/'manifest.json').write_text(json.dumps({'scope':'shared executor/backend integration, not agent gameplay','sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}},indent=2)+'\n')
    s=suite.Session();d=s.d;root=d.screen().root;backend=None;engine=None;events=[];checks=[];down=threading.Event()
    def emit(r):
        events.append(r)
        if r.get('event')=='pointer_admission' and r.get('operation')=='button_down':down.set()
    def wait():
        end=time.monotonic()+6
        while engine.active is not None and time.monotonic()<end:time.sleep(.01)
        assert engine.active is None,'executor did not become idle'
        return next(r for r in reversed(events) if r['event']=='terminal')
    def submit(name,steps,status='completed'):
        engine.submit(name,steps,backend.sequence,time.perf_counter_ns()+5_000_000_000)
        r=wait();assert r['status']==status and r['release']['verified'],r
        checks.append({'case':name,'status':r['status'],'release_verified':True})
    def reject(name,steps,sequence=None,deadline=None):
        before=sum(r['event'] in ('pointer_admission','input_admission') for r in events)
        try:engine.submit(name,steps,backend.sequence if sequence is None else sequence,time.perf_counter_ns()+5_000_000_000 if deadline is None else deadline)
        except (ValueError,Expired):pass
        else:raise AssertionError(name+' not rejected')
        assert before==sum(r['event'] in ('pointer_admission','input_admission') for r in events)
        checks.append({'case':name,'rejected_before_input':True})
    try:
        w=root.create_window(100,100,320,240,0,d.screen().root_depth,X.InputOutput,X.CopyFromParent,background_pixel=0xffffff,event_mask=X.ButtonPressMask|X.ButtonReleaseMask|X.KeyPressMask|X.KeyReleaseMask)
        w.set_wm_name('Pointer backend fixture');w.map();d.sync();s.wait_window('Pointer backend fixture');s.focus('Pointer backend fixture')
        backend=Backend(s,a.out,emit);engine=Executor(backend,emit);backend.snapshot('initial',0)
        b=backend.observed_pointer;assert b and b['surface']==w.id,b
        x,y=b['geometry'][:2];click={'op':'pointer_click','x':x+80,'y':y+80}
        reject('invalid_tail',[click,{'op':'pointer_move','x':-1,'y':0}])
        reject('stale_sequence',[click],sequence=backend.sequence-1)
        reject('expired_program',[click],deadline=time.perf_counter_ns()-1)
        reject('combined_budget',[{'op':'hold','keys':['a'],'duration_ms':5000},{'op':'pointer_drag','points':[{'x':x+80,'y':y+80},{'x':x+90,'y':y+90}],'duration_ms':5000},click])
        reject('planner_target_injection',[dict(click,expected_surface=w.id)])
        submit('click_scroll_key',[click,{'op':'pointer_scroll','x':x+80,'y':y+80,'ticks':2},{'op':'key','key':'a'}])
        d.sync();received=[]
        while d.pending_events():
            e=d.next_event()
            if e.type in (X.ButtonPress,X.ButtonRelease,X.KeyPress,X.KeyRelease):received.append([e.type,e.detail])
        assert [X.ButtonPress,1] in received and [X.ButtonRelease,1] in received
        assert received.count([X.ButtonPress,4])==2 and any(e[0]==X.KeyPress for e in received)
        checks.append({'case':'actual_surface_events','events':received})
        down.clear();engine.submit('cancel_drag',[{'op':'pointer_drag','points':[{'x':x+80,'y':y+80},{'x':x+100,'y':y+100}],'duration_ms':1000}],backend.sequence,time.perf_counter_ns()+5_000_000_000)
        assert down.wait(1);engine.cancel('cancel_drag');r=wait();assert r['status']=='cancelled' and r['release']['verified'],r
        assert not root.query_pointer().mask & X.Button1Mask
        checks.append({'case':'cancel_drag','status':r['status'],'button1_down':False})
        backend.snapshot('before_move',0);old=dict(backend.observed_pointer)
        w.configure(x=x+20,y=y);d.sync();end=time.monotonic()+2
        while backend.binding()['geometry']==old['geometry'] and time.monotonic()<end:time.sleep(.02)
        assert backend.binding()['geometry']!=old['geometry']
        before=sum(r['event']=='pointer_admission' for r in events)
        submit('observe_does_not_renew_geometry',[{'op':'observe'},click],'needs_decision')
        assert before==sum(r['event']=='pointer_admission' for r in events)
        x,y=backend.observed_pointer['geometry'][:2]
        submit('fresh_geometry_recovers',[{'op':'pointer_click','x':x+80,'y':y+80}])
    finally:
        if engine:engine.close()
        if backend:
            backend.close();(a.out/'owner-events.json').write_text(json.dumps(backend.owner.records,indent=2)+'\n')
        (a.out/'events.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in events))
        s.close();shutil.rmtree(s.tmp)
        (a.out/'results.json').write_text(json.dumps(checks,indent=2)+'\n')
    print(json.dumps({'checks':len(checks),'frames':backend.sequence,'passed':True}))

if __name__=='__main__':main()
