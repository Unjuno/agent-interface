"""Real X11 output stalls at local servo callback boundaries; no input oracle."""
import argparse,hashlib,importlib,json,shutil,threading,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=['session_v16','session_v17'],required=True);ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
module=importlib.import_module(args.backend);Backend,suite=module.Backend,module.suite
from executor_v3 import Executor
args.out.mkdir(exist_ok=False,parents=True)
rows=[]
for name,event,lease_ms,explicit_cancel in [('yield_timeout','pointer_yield',4000,False),('feedback_timeout','servo_feedback',4000,False),('yield_expiry','pointer_yield',700,False),('yield_cancel','pointer_yield',4000,True)]:
    out=args.out/name;out.mkdir();s=suite.Session();backend=None;engine=None;output=None;events=[];blocked=threading.Event();resume=threading.Event()
    def emit(r):
        r['emitted_ns']=time.perf_counter_ns();events.append(r)
        if r.get('event')==event and r.get('id')=='servo':
            blocked.set()
            if not resume.wait(5):raise RuntimeError('probe release did not resume output')
    try:
        goal,output,_=suite.prepare(s,'inkscape',991011,'unused');backend=Backend(s,out,emit);engine=Executor(backend,emit);backend.snapshot('initial',0)
        step=dict(op='pointer_servo',source_sequence=backend.sequence,box=[592,369,56,44],target_delta=[24,0],points=[{'x':619,'y':390},{'x':631,'y':390}],duration_ms=100,max_corrections=3)
        engine.submit('servo',[step],backend.sequence,time.perf_counter_ns()+lease_ms*1_000_000)
        assert blocked.wait(3),'did not reach requested stall'
        if explicit_cancel:engine.cancel('servo')
        deadline=time.monotonic()+2
        while time.monotonic()<deadline:
            state=backend.owner.call('input_state')
            if not state['owned_buttons']:break
            time.sleep(.005)
        assert not state['owned_buttons'] and engine.active is not None,'independent release failed'
        position=state['pointer'];resume.set();deadline=time.monotonic()+3
        while engine.active is not None and time.monotonic()<deadline:time.sleep(.01)
        assert engine.active is None
        terminal=next(r for r in reversed(events) if r['event']=='terminal')
        final=backend.owner.call('input_state')
        assert terminal['release']['verified'] and final['pointer']==position
        row={'case':name,'terminal':terminal,'released_while_output_blocked':True,'no_late_motion':True,'pointer':position}
        rows.append(row)
    finally:
        resume.set()
        if engine:engine.close()
        if backend:backend.close();(out/'owner-events.json').write_text(json.dumps(backend.owner.records,indent=2)+'\n')
        (out/'events.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in events))
        s.close();shutil.rmtree(s.tmp)
(args.out/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
sources=[Path(__file__),HERE/(args.backend+'.py'),HERE/'session_v15.py',HERE/'input_owner_v9.py',HERE/'pointer_reply_v2.py',HERE/'patch_servo.py',HERE/'visual_anchor.py',HERE/'executor_v3.py',HERE/'lease.py']
(args.out/'sources.json').write_text(json.dumps({str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},indent=2)+'\n')
print(json.dumps(rows,indent=2))
