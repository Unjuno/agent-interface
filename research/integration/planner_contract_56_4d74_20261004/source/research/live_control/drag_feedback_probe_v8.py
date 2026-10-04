"""Actual-app drag checkpoint and independent release checks with blocked output."""
import argparse,hashlib,json,shutil,threading,time
from pathlib import Path
from Xlib import X,display
from session_v12 import Backend,suite
from executor_v3 import Executor
HERE=Path(__file__).resolve().parent

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    names=['session_v12.py','session_v11.py','session_v9.py','session_v8.py','session_v7.py','session_v6.py','session_v5.py','session_v4.py','input_owner_v5.py','executor_v3.py','lease.py','quiet_window.py']
    sources=[HERE/n for n in names]+[HERE/'input_owner_v6.py',Path(__file__).resolve(),HERE.parent/'observation_gating/gui_suite.py',HERE.parent/'observation_tiles/tile_transport.py',HERE.parent/'observation_tiles/image_artifact.py',HERE.parent/'real_apps_v1/real_app_suite_v1.py']
    (a.out/'sources.json').write_text(json.dumps({str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},indent=2)+'\n')
    s=suite.Session();backend=None;engine=None;reader=None;events=[];checks=[];blocked=threading.Event();resume=threading.Event();stall=None
    def emit(r):
        r['emitted_ns']=time.perf_counter_ns();events.append(r)
        if r['event']=='drag_checkpoint' and r['point_index']==1 and r['id']==stall:
            blocked.set();assert resume.wait(3),'test did not unblock output'
    def wait():
        end=time.monotonic()+7
        while engine.active is not None and time.monotonic()<end:time.sleep(.01)
        assert engine.active is None
        return next(e for e in reversed(events) if e['event']=='terminal')
    def submit(name,steps,deadline_ms=4000):engine.submit(name,steps,backend.sequence,time.perf_counter_ns()+deadline_ms*1_000_000)
    try:
        suite.prepare(s,'inkscape',991003,'unused');backend=Backend(s,a.out,emit);engine=Executor(backend,emit)
        reader=display.Display(s.name);root=reader.screen().root
        backend.snapshot('initial',0);bbox=suite.red_bbox(backend.decoder.frame);x=(bbox[0]+bbox[2])//2;y=(bbox[1]+bbox[3])//2
        submit('select',[{'op':'pointer_click','x':x,'y':y},{'op':'settle','quiet_ms':100,'timeout_ms':1200}]);assert wait()['status']=='completed'
        base={'op':'pointer_drag','points':[{'x':x+i,'y':y} for i in (0,12,24,36)],'duration_ms':300,'observe_at':[0,1,2],'feedback_delay_ms':60}
        for invalid in [[True],[1,1],[2,1],[3],[-1],[0,1,2,3,4]]:
            before=len(backend.owner.records)
            try:submit('invalid-'+str(invalid),[{'op':'pointer_click','x':x,'y':y},dict(base,observe_at=invalid)])
            except ValueError:pass
            else:raise AssertionError('invalid checkpoint list accepted')
            assert len(backend.owner.records)==before
        checks.append({'case':'six_invalid_checkpoint_lists','rejected_before_input':True})
        submit('complete',[base]);terminal=wait();assert terminal['status']=='completed' and terminal['release']['verified']
        feedback=[e for e in events if e['event']=='drag_feedback' and e['id']=='complete'];assert [e['point_index'] for e in feedback]==[0,1,2]
        downs=[r for r in backend.owner.records if r.get('operation')=='button_down']
        assert feedback[-1]['emitted_ns']<terminal['terminal_ns'] and not root.query_pointer().mask & X.Button1Mask
        checks.append({'case':'completed_checkpoints','count':3,'release_verified':True})
        for mode in ['cancel','expiry']:
            stall=mode;blocked.clear();resume.clear()
            submit(mode,[dict(base,observe_at=[1])],deadline_ms=700 if mode=='expiry' else 4000)
            assert blocked.wait(2)
            assert root.query_pointer().mask & X.Button1Mask
            if mode=='cancel':engine.cancel(mode)
            deadline=time.monotonic()+2
            while root.query_pointer().mask & X.Button1Mask and time.monotonic()<deadline:time.sleep(.005)
            released=not root.query_pointer().mask & X.Button1Mask
            assert released and engine.active is not None and not resume.is_set()
            point=root.query_pointer();assert (point.root_x,point.root_y)==(x+12,y)
            released_ns=time.perf_counter_ns();resume.set();terminal=wait()
            assert terminal['status']==('cancelled' if mode=='cancel' else 'expired') and terminal['release']['verified'],terminal
            point=root.query_pointer();assert (point.root_x,point.root_y)==(x+12,y)
            checks.append({'case':mode+'_while_output_blocked','released_before_output_resumed':True,'release_observed_ns':released_ns,'tail_motion_absent':True,'terminal':terminal['status']})
    except Exception as exc:
        checks.append({'error':repr(exc)});raise
    finally:
        resume.set()
        if engine:engine.close()
        if backend:
            backend.close();(a.out/'owner-events.json').write_text(json.dumps(backend.owner.records,indent=2)+'\n')
        if reader:reader.close()
        (a.out/'events.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in events))
        s.close();(a.out/'cleanup.json').write_text(json.dumps({'all_owned_processes_exited':all(p.poll() is not None for p in s.procs)})+'\n');shutil.rmtree(s.tmp)
        (a.out/'results.json').write_text(json.dumps(checks,indent=2)+'\n')
    print(json.dumps(checks),flush=True)

if __name__=='__main__':main()
