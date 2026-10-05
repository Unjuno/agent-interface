"""Real X11 input observation during cooperative lease stalls."""
import argparse,contextlib,hashlib,json,sys,threading,time
from pathlib import Path
import session_v4
import session_v5
from executor_v3 import Executor

HERE=Path(__file__).resolve().parent


def run(out,fault,seed,isolated):
    current=session_v5 if isolated else session_v4
    out.mkdir(parents=True,exist_ok=False);s=None;e=None;b=None;watcher=None;monitor=None;events=[];samples=[];stop=threading.Event()
    def emit(r):
        events.append(r)
        if fault=='log' and r['event']=='input_admission':time.sleep(.5)
    try:
        with (out/'setup.txt').open('w') as f,contextlib.redirect_stdout(f):
            s=current.suite.Session();current.suite.prepare(s,'xterm',seed,'')
            monitor=current.suite.base.xdisplay.Display(s.name)
        code=monitor.keysym_to_keycode(current.suite.base.XK.string_to_keysym('Control_L'))
        def watch():
            while not stop.is_set():
                state=bool(monitor.query_keymap()[code//8]&(1<<(code%8)))
                samples.append(dict(ns=time.perf_counter_ns(),down=state));stop.wait(.002)
        watcher=threading.Thread(target=watch);watcher.start()
        b=current.Backend(s,out,emit);b.sequence=1
        original=b.snapshot
        def snapshot(identifier,index):
            if fault=='capture':time.sleep(.5)
            original(identifier,index)
        b.snapshot=snapshot;e=Executor(b,emit);deadline=time.perf_counter_ns()+200_000_000
        done=threading.Event()
        base_emit=e.emit
        def dispatch(r):
            base_emit(r)
            if r['event']=='terminal':done.set()
        e.emit=dispatch
        e.submit('hold',[dict(op='hold',keys=['Control_L'],duration_ms=1000),dict(op='text',text='bad')],1,deadline)
        if not done.wait(5):raise TimeoutError('executor completion')
        e.close();time.sleep(.02);stop.set();watcher.join();monitor.close()
        terminal=next(r for r in events if r['event']=='terminal')
        assert terminal['status']=='expired' and terminal['release']['verified']
        downs=[r for r in samples if r['down']];assert downs
        released=next(r for r in samples if not r['down'] and r['ns']>downs[-1]['ns'])
        report=dict(fault=fault,seed=seed,isolated=isolated,deadline_ns=deadline,
            last_observed_down_after_deadline_ms=(downs[-1]['ns']-deadline)/1e6,
            first_observed_up_after_deadline_ms=(released['ns']-deadline)/1e6,
            terminal_release_after_deadline_ms=(terminal['release']['verified_ns']-deadline)/1e6,
            release_verified=True,tail_started=any(r['event']=='step_started' and r['step']==1 for r in events),
            scope='separate X11 connection samples key state; 500 ms injected worker stall; no hard deadline claim')
        (out/'report.json').write_text(json.dumps(report,indent=2));return report
    finally:
        if e is not None:e.close()
        if b is not None and isolated:
            b.close()
            (out/'owner-events.json').write_text(json.dumps(b.owner.records,indent=2))
        stop.set()
        if watcher is not None and watcher.is_alive():watcher.join()
        (out/'events.json').write_text(json.dumps(events));(out/'key-samples.json').write_text(json.dumps(samples))
        if s is not None:s.close()


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    a.out.mkdir(parents=True,exist_ok=False)
    names=['probe_stalls_v2.py','session_v4.py','session_v5.py','input_owner.py','executor_v3.py','lease.py']
    (a.out/'sources.json').write_text(json.dumps({n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in names},indent=2))
    rows=[]
    try:
        for seed in (910301,910302):
            for fault in ('log','capture'):
                for isolated in ((False,True) if seed==910301 else (True,False)):
                    r=run(a.out/f'{seed}-{fault}-{int(isolated)}',fault,seed,isolated);rows.append(r);print(json.dumps(r),flush=True)
    finally:(a.out/'summary.json').write_text(json.dumps(rows,indent=2))
