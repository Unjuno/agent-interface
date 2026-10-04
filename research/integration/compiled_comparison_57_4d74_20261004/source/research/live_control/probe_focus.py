"""Private-X11 focus transfer probe with a visible independent key-event sink."""
import argparse,contextlib,hashlib,json,time
from pathlib import Path
import session_v5,session_v6
from executor_v3 import Executor

HERE=Path(__file__).resolve().parent

def run(out,guarded,changed,seed):
    out.mkdir(parents=True,exist_ok=False)
    module=session_v6 if guarded else session_v5
    s=None;b=None;e=None;monitor=None;events=[]
    try:
        with (out/'setup.txt').open('w') as f,contextlib.redirect_stdout(f):
            s=module.suite.Session();module.suite.prepare(s,'xterm',seed,'')
            monitor=module.suite.base.xdisplay.Display(s.name)
            b=module.Backend(s,out,events.append)
        X=module.suite.base.X
        sink=monitor.screen().root.create_window(0,0,160,90,0,monitor.screen().root_depth,
            background_pixel=monitor.screen().white_pixel,override_redirect=True,event_mask=X.KeyPressMask)
        sink.set_wm_name('FOCUS PROBE KEY SINK');sink.map();monitor.sync()
        original=monitor.get_input_focus().focus
        original_id=original.id if hasattr(original,'id') else original
        assert original_id not in (0,1,sink.id)
        b.snapshot('initial',0)
        if changed:
            sink.set_input_focus(X.RevertToParent,X.CurrentTime);monitor.sync()
        actual=monitor.get_input_focus().focus
        actual_id=actual.id if hasattr(actual,'id') else actual
        assert (actual_id==sink.id)==changed
        e=Executor(b,events.append)
        e.submit('input',[dict(op='text',text='a')],b.sequence,time.perf_counter_ns()+2_000_000_000)
        limit=time.perf_counter()+3
        while not any(r['event']=='terminal' for r in events) and time.perf_counter()<limit:
            time.sleep(.002)
        terminal=next(r for r in events if r['event']=='terminal')
        e.close();monitor.sync()
        received=[]
        while monitor.pending_events():
            event=monitor.next_event()
            if event.type==X.KeyPress:received.append(event.detail)
        expected='needs_decision' if guarded and changed else 'completed'
        assert terminal['status']==expected and terminal['release']['verified']
        assert bool(received)==(changed and not guarded)
        if not changed:assert any(r['event']=='input_admission' for r in events)
        report=dict(seed=seed,guarded=guarded,focus_changed=changed,observed_focus=original_id,
            pre_submit_focus=actual_id,sink_window=sink.id,sink_keypresses=received,
            terminal_status=terminal['status'],release_verified=True,
            scope='local focus transfer and X11 key delivery; no saved-task or planner-speed comparison')
        (out/'report.json').write_text(json.dumps(report,indent=2))
        return report
    finally:
        if e is not None:e.close()
        if b is not None:
            b.close();(out/'owner-events.json').write_text(json.dumps(b.owner.records,indent=2))
        (out/'events.json').write_text(json.dumps(events))
        if monitor is not None:monitor.close()
        if s is not None:s.close()

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    a.out.mkdir(parents=True,exist_ok=False)
    names=['probe_focus.py','session_v5.py','session_v6.py','session_v4.py','input_owner.py','input_owner_v2.py','executor_v3.py','lease.py']
    (a.out/'sources.json').write_text(json.dumps({n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in names},indent=2))
    rows=[]
    try:
        for seed in (930101,930102):
            for changed in (False,True):
                for guarded in ((False,True) if seed==930101 else (True,False)):
                    r=run(a.out/f'{seed}-{int(changed)}-{int(guarded)}',guarded,changed,seed)
                    rows.append(r);print(json.dumps(r),flush=True)
    finally:(a.out/'summary.json').write_text(json.dumps(rows,indent=2))
