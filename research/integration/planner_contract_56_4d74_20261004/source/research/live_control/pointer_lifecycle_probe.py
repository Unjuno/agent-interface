"""Failure injection limited to this probe's private Xvfb process."""
import argparse,hashlib,json,os,signal,sys,time,shutil
from pathlib import Path
from Xlib import X
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'observation_gating'))
from gui_suite import Session
from input_owner_v5 import InputOwner
from lease import Lease

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    files=[Path(__file__).resolve(),HERE/'input_owner_v5.py',HERE/'lease.py',HERE/'executor_v3.py']
    (a.out/'manifest.json').write_text(json.dumps({'scope':'private Xvfb lifecycle failures only','sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files}},indent=2)+'\n')
    rows=[]
    for case in ['stopped_server','disconnected_server']:
        s=Session();d=s.d;root=d.screen().root;owner=None;paused=False
        row={'case':case}
        try:
            w=root.create_window(50,80,200,180,0,d.screen().root_depth,X.InputOutput,X.CopyFromParent,override_redirect=True)
            w.map();w.set_input_focus(X.RevertToParent,X.CurrentTime);d.sync()
            owner=InputOwner(s.name);l=Lease(time.perf_counter_ns()+10_000_000_000)
            l.expected_focus=w.id;l.expected_surface=w.id;l.expected_geometry=[50,80,200,180]
            owner.call('move',l,{'x':100,'y':120});owner.call('button_down',l,1)
            assert root.query_pointer().mask & X.Button1Mask
            assert s.xvfb.poll() is None
            if case=='stopped_server':
                os.kill(s.xvfb.pid,signal.SIGSTOP);paused=True
            else:
                os.kill(s.xvfb.pid,signal.SIGKILL);s.xvfb.wait(timeout=2)
            time.sleep(.05)
            start=time.monotonic()
            try:owner.call('move',l,{'x':180,'y':160})
            except Exception as exc:row['call_error']=type(exc).__name__
            else:raise AssertionError('failed server accepted call')
            row['call_seconds']=time.monotonic()-start
            assert row['call_seconds']<2.5
            start=time.monotonic()
            try:owner.call('move',l,{'x':190,'y':170})
            except RuntimeError:pass
            else:raise AssertionError('failed owner accepted retry')
            row['retry_rejected_seconds']=time.monotonic()-start
            if paused:
                os.kill(s.xvfb.pid,signal.SIGCONT);paused=False
            assert owner.stopped.wait(2), 'owner failed to stop after server terminal/resume'
            if case=='stopped_server':
                point=root.query_pointer()
                assert not point.mask & X.Button1Mask
                assert (point.root_x,point.root_y)==(100,120), 'queued move replayed after resume'
                row['release_verified_after_resume']=True
                row['queued_move_not_replayed']=True
            else:
                row['release_verified']=False
                row['release_status']='unverifiable after X server termination, not a successful cleanup claim'
                assert any(e['event']=='cleanup_failed' for e in owner.records)
        finally:
            if paused:os.kill(s.xvfb.pid,signal.SIGCONT)
            if owner:
                try:owner.close()
                except Exception as exc:row['close_error']=repr(exc)
                row['owner_thread_stopped']=not owner.thread.is_alive()
                row['owner_events']=owner.records
            s.close()
            for p in s.procs:p.wait(timeout=5)
            row['all_owned_processes_exited']=all(p.poll() is not None for p in s.procs)
            shutil.rmtree(s.tmp);rows.append(row)
            (a.out/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
    print(json.dumps([{k:v for k,v in r.items() if k!='owner_events'} for r in rows],indent=2))

if __name__=='__main__':main()
