"""Real capture-time focus change, recovery observation, and explicit new intent."""
import argparse,contextlib,hashlib,json,time
from pathlib import Path
import session_v6,session_v7
from executor_v3 import Executor

HERE=Path(__file__).resolve().parent

def run(out,candidate,seed):
    out.mkdir(parents=True,exist_ok=False)
    module=session_v7 if candidate else session_v6
    s=None;b=None;e=None;d=None;events=[]
    try:
        with (out/'setup.txt').open('w') as f,contextlib.redirect_stdout(f):
            s=module.suite.Session();module.suite.prepare(s,'xterm',seed,'')
            d=module.suite.base.xdisplay.Display(s.name);b=module.Backend(s,out,events.append)
        X=module.suite.base.X
        sink=d.screen().root.create_window(0,0,160,90,0,d.screen().root_depth,
            background_pixel=d.screen().white_pixel,override_redirect=True,event_mask=X.KeyPressMask)
        sink.map();d.sync()
        original_context=s.context
        def transfer():
            sink.set_input_focus(X.RevertToParent,X.CurrentTime);d.sync()
            return original_context()
        s.context=transfer
        b.snapshot('initial',0)
        s.context=original_context
        assert b.observed_focus is None
        e=Executor(b,events.append)
        def submit(identifier,steps):
            e.submit(identifier,steps,b.sequence,time.perf_counter_ns()+2_000_000_000)
            limit=time.perf_counter()+3
            while time.perf_counter()<limit:
                terminal=next((r for r in events if r['event']=='terminal' and r['id']==identifier),None)
                if terminal:return terminal
                time.sleep(.002)
            raise TimeoutError(identifier)
        # An observation inside this program must not authorize its input tail.
        mixed=submit('mixed',[dict(op='observe'),dict(op='text',text='b')])
        assert mixed['status']=='needs_decision'
        assert not any(r['event']=='input_admission' for r in events)
        sequence=b.sequence
        observed=submit('recover',[dict(op='observe')])
        assert observed['status']==('completed' if candidate else 'needs_decision')
        assert (b.sequence>sequence)==candidate
        if candidate:
            fresh=submit('fresh',[dict(op='text',text='a')])
            assert fresh['status']=='completed'
        d.sync();received=[]
        while d.pending_events():
            event=d.next_event()
            if event.type==X.KeyPress:received.append(dict(type=event.type,keycode=event.detail,window=event.window.id,time=event.time))
        expected_code=d.keysym_to_keycode(module.suite.base.XK.string_to_keysym('a'))
        assert [r['keycode'] for r in received]==([expected_code] if candidate else [])
        report=dict(seed=seed,candidate=candidate,mixed_status=mixed['status'],
            recovery_status=observed['status'],fresh_input_completed=candidate,
            sink_events=received,all_releases_verified=all(r['release']['verified'] for r in events if r['event']=='terminal'),
            scope='controlled capture-time focus transfer; fresh input deliberately targets the newly observed sink')
        assert report['all_releases_verified']
        (out/'report.json').write_text(json.dumps(report,indent=2));return report
    finally:
        if e is not None:e.close()
        if b is not None:
            b.close();(out/'owner-events.json').write_text(json.dumps(b.owner.records,indent=2))
        (out/'events.json').write_text(json.dumps(events))
        if d is not None:d.close()
        if s is not None:s.close()

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    a.out.mkdir(parents=True,exist_ok=False)
    names=['probe_focus_recovery.py','session_v7.py','session_v6.py','session_v5.py','session_v4.py','input_owner_v2.py','executor_v3.py','lease.py']
    (a.out/'sources.json').write_text(json.dumps({n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in names},indent=2))
    rows=[]
    try:
        for seed in (940101,940102):
            for candidate in ((False,True) if seed==940101 else (True,False)):
                result=run(a.out/f'{seed}-{int(candidate)}',candidate,seed);rows.append(result);print(json.dumps(result),flush=True)
    finally:(a.out/'summary.json').write_text(json.dumps(rows,indent=2))
