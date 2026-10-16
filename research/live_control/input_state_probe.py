"""Actual-app capture/delivery stalls verify historical input-state bracketing."""
import argparse,hashlib,json,shutil,threading,time
from pathlib import Path
from Xlib import X
from session_v13 import Backend,suite
from session_v9 import ImageGrab
from executor_v3 import Executor
HERE=Path(__file__).resolve().parent

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    names=['session_v13.py','session_v12.py','session_v11.py','session_v9.py','session_v8.py','session_v7.py','session_v6.py','session_v5.py','session_v4.py','input_owner_v7.py','input_owner_v6.py','input_owner_v5.py','executor_v3.py','lease.py','quiet_window.py']
    paths=[HERE/n for n in names]+[Path(__file__).resolve(),HERE.parent/'observation_gating/gui_suite.py',HERE.parent/'real_apps_v1/real_app_suite_v1.py',HERE.parent/'observation_tiles/tile_transport.py',HERE.parent/'observation_tiles/image_artifact.py']
    (a.out/'sources.json').write_text(json.dumps({str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},indent=2)+'\n')
    s=suite.Session();backend=None;engine=None;events=[];rows=[];entered=threading.Event();resume=threading.Event();armed=None;original=ImageGrab.grab
    def grab(*args,**kwargs):
        nonlocal armed
        image=original(*args,**kwargs)
        if armed=='capture':armed=None;entered.set();assert resume.wait(3)
        return image
    def emit(r):
        nonlocal armed
        if r.get('event')=='observation' and armed=='delivery':armed=None;entered.set();assert resume.wait(3)
        r['delivered_ns']=time.perf_counter_ns();events.append(r)
    def wait():
        end=time.monotonic()+5
        while engine.active is not None and time.monotonic()<end:time.sleep(.005)
        assert engine.active is None
        return next(r for r in reversed(events) if r['event']=='terminal')
    try:
        suite.prepare(s,'inkscape',991003,'unused');backend=Backend(s,a.out,emit);engine=Executor(backend,emit);backend.snapshot('initial',0)
        ImageGrab.grab=grab
        base={'op':'pointer_drag','points':[{'x':400,'y':250},{'x':410,'y':250}],'duration_ms':200,'observe_at':[0]}
        for name,mode in [('normal',None),('cancel_capture','capture'),('expiry_capture','capture'),('cancel_delivery','delivery')]:
            backend.snapshot(name+'-fresh',0);entered.clear();resume.clear();armed=mode
            deadline=time.perf_counter_ns()+(700_000_000 if name=='expiry_capture' else 4_000_000_000)
            engine.submit(name,[base],backend.sequence,deadline)
            release_sample=None
            if mode:
                assert entered.wait(2)
                held=backend.owner.call('input_state');assert held['owned_buttons']==[1]
                if name!='expiry_capture':engine.cancel(name)
                end=time.monotonic()+2
                while time.monotonic()<end:
                    release_sample=backend.owner.call('input_state')
                    if not release_sample['owned_buttons'] and not release_sample['physical_pointer_mask']&X.Button1Mask:break
                    time.sleep(.005)
                assert release_sample and not release_sample['owned_buttons'] and not release_sample['physical_pointer_mask']&X.Button1Mask
                assert engine.active is not None;resume.set()
            terminal=wait();expected='completed' if mode is None else 'expired' if name=='expiry_capture' else 'cancelled'
            assert terminal['status']==expected and terminal['release']['verified'],terminal
            observation=next(r for r in events if r.get('event')=='observation' and r.get('id')==name)
            before=observation['input_state_before'];after=observation['input_state_after']
            assert before['owned_buttons']==[1]
            if mode=='capture':
                assert after['owned_buttons']==[] and after['revision']>before['revision'] and not observation['owner_revision_unchanged']
            else:assert after['owned_buttons']==[1] and observation['owner_revision_unchanged']
            if mode=='delivery':assert release_sample['revision']>after['revision'] and release_sample['sample_finished_ns']<observation['delivered_ns']
            rows.append({'case':name,'terminal':terminal['status'],'before':before,'after':after,'release_sample_while_blocked':release_sample,'delivered_ns':observation['delivered_ns']})
    except Exception as exc:rows.append({'error':repr(exc)});raise
    finally:
        resume.set();ImageGrab.grab=original
        if engine:engine.close()
        if backend:backend.close();(a.out/'owner-events.json').write_text(json.dumps(backend.owner.records,indent=2)+'\n')
        (a.out/'events.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in events));(a.out/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
        s.close();(a.out/'cleanup.json').write_text(json.dumps({'all_owned_processes_exited':all(p.poll() is not None for p in s.procs)})+'\n');shutil.rmtree(s.tmp)
    print(json.dumps([{'case':r['case'],'terminal':r['terminal']} for r in rows]))
if __name__=='__main__':main()
